"""v0.4 units 2–9: connector, relay, seats, approvals, channels, plugins, service, upgrade."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from sovereign_agent.approvals import (
    ApprovalConflict,
    ApprovalDecisionKind,
    ApprovalRequest,
    ApprovalService,
    PolicyEffect,
    PolicyRule,
)
from sovereign_agent.channels.adapter import OutboundMessage
from sovereign_agent.channels.email import EmailAdapter, EmailSendBlocked
from sovereign_agent.channels.webhook import WebhookAdapter
from sovereign_agent.connectors import ConnectorError, ZeroEmployeeConnector
from sovereign_agent.contracts import canonical_json_bytes
from sovereign_agent.operations import backup, compact, migrate_v03_copy_on_write, restore
from sovereign_agent.plugins import PluginLoader
from sovereign_agent.registry import SeatRegistry
from sovereign_agent.registry.supervisor import PresenceState, SeatSupervisor, SupervisorConflict
from sovereign_agent.relay import AmbiguousRecipient, DurableRelay, RelayMessage, resolve_recipient
from sovereign_agent.runtime import RUNTIME_LAYOUT_VERSION, RuntimeRoot
from sovereign_agent.service import CoordinatorConflict, ServiceRuntime, acquire_coordinator_lease
from tests.test_governed_execution import _request


@pytest.mark.asyncio
async def test_zeo_connector_round_trip_and_malformed_refusal(governed, tmp_path: Path) -> None:
    engine, _provider, runtime = governed
    connector = ZeroEmployeeConnector(engine)
    request = _request(execution_id="zeo-round")
    fixture = tmp_path / "zeo-request.json"
    payload = request.to_dict()
    fixture.write_bytes(canonical_json_bytes(payload))
    restored = json.loads(fixture.read_text(encoding="utf-8"))
    assert restored == json.loads(canonical_json_bytes(payload))
    ack, receipt = await connector.execute(fixture)
    assert ack.acknowledged is True
    assert receipt.verify_evidence()
    exported = connector.export_receipt(str(request.execution_id))
    assert ZeroEmployeeConnector.verify_receipt(exported)["valid"] is True
    with pytest.raises(ConnectorError):
        connector.load_request(b'{"not":"a-governed-request"}')
    assert connector.probe()["imports_zero_employee"] is False


def test_relay_v2_crash_transitions_and_idempotent_apply(tmp_path: Path) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    registry = SeatRegistry(runtime)
    sender = registry.register(
        instance_id="sender-1", seat_id="seat", provider="codex", backend="bare"
    )
    recipient = registry.register(
        instance_id="recipient-1", seat_id="seat", provider="codex", backend="bare"
    )
    relay = DurableRelay(runtime, registry, max_attempts=3, backoff_base=0.01, backoff_cap=0.05)
    crashes: list[str] = []

    def hook(status: str, _path: Path) -> None:
        crashes.append(status)
        if len(crashes) == 1:
            raise RuntimeError("crash-after-enqueue")

    relay._fault_hook = hook  # noqa: SLF001
    message = RelayMessage(
        message_id="msg-crash-1",
        sender=sender.address,
        recipient=recipient.address,
        kind="ping",
        payload={"n": 1},
        created_at=datetime.now(UTC),
        conversation_id="round_351",
    )
    with pytest.raises(RuntimeError):
        relay.enqueue(message)
    recovered = DurableRelay(runtime, registry, max_attempts=3)
    again = recovered.enqueue(message)
    assert again.message.message_id.value == "msg-crash-1"
    claimed = recovered.claim(recipient.address, owner="worker-a", lease_seconds=5)
    assert claimed is not None
    recovered.ack(claimed.message.message_id, owner="worker-a", lease_token=claimed.lease_token)
    assert recovered.get(claimed.message.message_id).status.value == "acknowledged"
    duplicate = recovered.enqueue(message)
    assert duplicate.message.message_id.value == "msg-crash-1"
    assert recovered.inspect_conversation("round_351")["message_ids"] == ["msg-crash-1"]
    with pytest.raises(AmbiguousRecipient):
        resolve_recipient(registry, seat_type="seat")


def test_seat_supervisor_fences_duplicates_and_recovers(tmp_path: Path) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    registry = SeatRegistry(runtime)
    instance = registry.register(
        instance_id="research-01",
        seat_id="zeo-stream",
        provider="codex",
        backend="bare",
        provider_session_id="opaque-1",
    )
    supervisor = SeatSupervisor(
        runtime,
        registry,
        heartbeat_timeout=timedelta(seconds=1),
        unknown_grace=timedelta(seconds=1),
    )
    supervisor.acquire_instance(instance.instance_id, owner="coord-a")
    with pytest.raises(SupervisorConflict):
        supervisor.acquire_instance(instance.instance_id, owner="coord-b")
    supervisor.heartbeat_instance(
        instance.instance_id, presence=PresenceState.BUSY, active_execution="exec-1"
    )
    with pytest.raises(SupervisorConflict):
        supervisor.heartbeat_instance(
            instance.instance_id, presence=PresenceState.BUSY, active_execution="exec-2"
        )
    supervisor.drain(instance.instance_id)
    event = supervisor.recover(instance.instance_id, provider_session="opaque-2")
    assert event is not None
    assert event.reason


def test_approvals_survive_restart_and_resume_once(tmp_path: Path) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    service = ApprovalService(
        runtime, rules=(PolicyRule(PolicyEffect.ALLOW, action_kinds=("read",)),)
    )
    request = ApprovalRequest(
        approval_id="approval_01JTEST",
        execution_id="exec_01JTEST",
        seat_instance="research-01",
        action_kind="email.send",
        action_summary="Send an email to 42 recipients",
        risk_class="external-write",
        requested_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=2),
        requested_capabilities=("email.send",),
    )
    pending = service.submit(request, engage_mode="autonomous")
    assert pending["status"] == "require-human"
    restarted = ApprovalService(runtime)
    assert restarted.pending()
    restarted.decide(
        request.approval_id,
        ApprovalDecisionKind.APPROVED,
        actor="human",
        reason="ok",
    )
    execution = restarted.resume_execution(request.approval_id)
    assert execution == "exec_01JTEST"
    with pytest.raises(ApprovalConflict):
        restarted.resume_execution(request.approval_id)


@pytest.mark.asyncio
async def test_channels_dedup_and_email_cannot_bypass_approval(tmp_path: Path) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    secret = b"whsec"
    webhook = WebhookAdapter(runtime, secret, approval_gate=lambda cap: False)
    body = json.dumps(
        {
            "account_id": "acct",
            "message_id": "m1",
            "sender_id": "u1",
            "text": "hello",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    ).encode()
    signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
    first = webhook.receive(body, signature)
    second = webhook.receive(body, signature)
    assert first is not None
    assert second is None
    email = EmailAdapter(runtime, approval_gate=lambda cap: False)
    with pytest.raises(EmailSendBlocked):
        await email.deliver("ops@example.invalid", None, OutboundMessage.text("hi"))
    email.draft("ops@example.invalid", "draft", "body")


def test_plugins_allowlist_and_incompatible_do_not_block_optional(tmp_path: Path) -> None:
    from sovereign_agent.registries import Registry

    class Dummy:
        kind = "channel"
        name = "ok-plugin"
        channel_type = "dummy"
        supports_threads = False

        async def setup(self, router: object) -> None:
            return None

        async def teardown(self) -> None:
            return None

        async def deliver(self, platform_id: str, thread_id: str | None, message: object) -> None:
            return None

    loaded_flag = {"n": 0}

    class Point:
        def __init__(self, name: str, api_range: str, required: bool = False) -> None:
            self.name = name
            self.attrs = {
                "kind": "channel",
                "api_range": api_range,
                "required": required,
                "package": name,
            }
            self.dist = SimpleNamespace(name=name, version="0.1.0")

        def load(self) -> Dummy:
            loaded_flag["n"] += 1
            plugin = Dummy()
            plugin.name = self.name
            return plugin

    points = [
        Point("blocked-side-effect", ">=0.5,<0.6"),
        Point("ok-plugin", ">=0.5,<0.6"),
        Point("old-plugin", ">=0.4,<0.5"),
    ]
    registry = Registry(kind_filter="channel")
    loader = PluginLoader(
        registry,
        allowlist=("ok-plugin", "old-plugin"),
        entry_points=lambda: points,
    )
    discovered = loader.discover()
    assert discovered
    assert loaded_flag["n"] == 0
    loaded = loader.load()
    assert [item.name for item in loaded] == ["ok-plugin"]
    assert any("not allowlisted" in item for item in loader.failures)
    assert any("incompatible" in item for item in loader.failures)


def test_service_lease_backup_restore_and_compaction(tmp_path: Path) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    first = acquire_coordinator_lease(runtime)
    with pytest.raises(CoordinatorConflict):
        acquire_coordinator_lease(runtime)
    first.release()
    svc = ServiceRuntime(runtime)
    svc.start()
    svc.tick()
    ready = svc.readiness()
    assert ready.ready
    assert ready.live
    archive = backup(runtime, tmp_path / "bak")
    assert (archive / "backup-manifest.json").exists()
    restore(archive, tmp_path / "restored-check", verify_only=True)
    with pytest.raises(CoordinatorConflict):
        restore(archive, runtime.root, live_root=runtime.root)
    restored = restore(archive, tmp_path / "restored")
    assert restored.exists()
    compact(runtime)
    assert (runtime.operations_dir / "compaction-manifest.json").exists()
    svc.stop()


def test_v03_copy_on_write_migration_and_rollback(tmp_path: Path) -> None:
    original = RuntimeRoot(tmp_path / "v03", layout_version=1).initialize()
    (original.receipts_dir / "final.json").write_text('{"ok":true}', encoding="utf-8")
    marker = original.receipts_dir / "final.json"
    digest = hashlib.sha256(marker.read_bytes()).hexdigest()
    upgraded = migrate_v03_copy_on_write(original.root, tmp_path / "v04")
    assert upgraded.layout_version == RUNTIME_LAYOUT_VERSION
    assert hashlib.sha256(marker.read_bytes()).hexdigest() == digest
    assert (tmp_path / "v04" / "receipts" / "final.json").exists()
    assert (tmp_path / "v04" / "api").is_dir()
    # rollback is restoring the untouched original
    assert RuntimeRoot.open(original.root).layout_version == 1
