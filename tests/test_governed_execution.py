from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from sovereign_agent.cli import app
from sovereign_agent.contracts import (
    CapabilityManifest,
    ExecutionConstraints,
    ExecutionId,
    FrozenDict,
    GovernedExecutionRequest,
    InvocationId,
    ReceiptStatus,
    ReceiptTermination,
    RepositoryId,
    SeatId,
    SeatInstanceId,
    SovereignSessionId,
)
from sovereign_agent.execution import GovernedExecutionEngine
from sovereign_agent.orchestrator import BareWorker, WorkerOutcome
from sovereign_agent.providers import (
    InvocationResult,
    ProviderCapabilities,
    StructuredResultEvent,
)
from sovereign_agent.registry import SeatRegistry
from sovereign_agent.relay import DurableRelay
from sovereign_agent.repository import RepositoryConfig, RepositoryManager
from sovereign_agent.runtime import RuntimeRoot


class FakeProvider:
    kind = "provider"
    name = "fake"
    capabilities = ProviderCapabilities(structured_result=True)

    def __init__(self, *, business_done: bool = True, structured: bool = True) -> None:
        self.calls = 0
        self.business_done = business_done
        self.structured = structured
        self.delay = 0.0
        self.error: Exception | None = None

    async def invoke(
        self, request: Any, *, observers: Any = (), activity_callbacks: Any = ()
    ) -> Any:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error is not None:
            raise self.error
        worktree = Path(str(request.context["repository_worktree"]))
        (worktree / "result.txt").write_text("governed\n", encoding="utf-8")
        _git(worktree, "add", "result.txt")
        _git(
            worktree,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "provider result",
        )
        events = ()
        if self.structured:
            event = StructuredResultEvent(
                execution_id=request.execution_id,
                invocation_id=request.invocation_id,
                sequence=0,
                timestamp=datetime.now(UTC),
                result=FrozenDict((("done", self.business_done),)),
            )
            events = (event,)
            for callback in (*observers, *activity_callbacks):
                value = callback(event)
                if inspect.isawaitable(value):
                    await value
        return InvocationResult(
            success=True,
            output=FrozenDict((("done", self.business_done),)),
            summary="done",
            next_action="stop",
            events=events,
        )


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(("git", "-C", str(cwd), *args), check=True, capture_output=True)


@pytest.fixture
def governed(tmp_path: Path) -> tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot]:
    checkout = tmp_path / "repo"
    checkout.mkdir()
    _git(checkout, "init", "-q")
    (checkout / "README.md").write_text("base\n", encoding="utf-8")
    _git(checkout, "add", "README.md")
    _git(
        checkout,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "base",
    )
    remote = tmp_path / "remote.git"
    subprocess.run(("git", "init", "--bare", "-q", str(remote)), check=True)
    _git(checkout, "remote", "add", "origin", str(remote))
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    seats = SeatRegistry(runtime)
    seats.register(
        instance_id=SeatInstanceId("seat-instance"),
        seat_id=SeatId("worker-seat"),
        provider="fake",
        backend="bare",
        capabilities=("structured_result",),
    )
    provider = FakeProvider()

    async def unused(session_id: str, directory: Path) -> WorkerOutcome:
        del directory
        return WorkerOutcome(session_id, False, False, "unused")

    engine = GovernedExecutionEngine(
        runtime_root=runtime,
        repository_manager=RepositoryManager(
            runtime,
            (RepositoryConfig(RepositoryId("repo"), checkout),),
        ),
        seat_registry=seats,
        providers={"fake": provider},
        backends={"bare": BareWorker(unused)},
    )
    return engine, provider, runtime


def _request(
    *,
    execution_id: str = "execution-1",
    governance: dict[str, Any] | None = None,
) -> GovernedExecutionRequest:
    governance_value = governance or {
        "authority": {"grant": "test"},
        "constraints": {"structured_output": {"required_fields": ["done"]}},
        "verification": [{"type": "changed_paths_nonempty"}],
        "business_completion": [
            {
                "type": "output_field_equals",
                "field": "done",
                "value": True,
            }
        ],
        "delivery": {"enabled": False},
    }
    constraint_values = dict(governance_value.get("constraints", {}))
    known_constraint_names = {
        "dirty_worktree",
        "filesystem_isolation",
        "network_isolation",
        "preserve_on_failure",
        "structured_output",
        "timeouts",
    }
    delivery = dict(governance_value.get("delivery", {}))
    return GovernedExecutionRequest(
        seat_instance_id=SeatInstanceId("seat-instance"),
        sovereign_session_id=SovereignSessionId("session-1"),
        execution_id=ExecutionId(execution_id),
        invocation_id=InvocationId(f"{execution_id}-invocation"),
        repository_id=RepositoryId("repo"),
        operation="edit",
        input=FrozenDict((("task", "write result"),)),
        governance=FrozenDict(tuple(governance_value.items())),
        conversation_id=f"conversation-{execution_id}",
        seat_type=SeatId("worker-seat"),
        requested_by="test-suite",
        authority_refs=("authority:test",),
        work_artifact_refs=(),
        base_ref="HEAD",
        branch=f"sovereign/{execution_id}",
        constraints=ExecutionConstraints(
            dirty_worktree=str(constraint_values.get("dirty_worktree", "fail")),
            filesystem_isolation=bool(constraint_values.get("filesystem_isolation", False)),
            network_isolation=bool(constraint_values.get("network_isolation", False)),
            preserve_on_failure=bool(constraint_values.get("preserve_on_failure", True)),
            structured_output=constraint_values.get("structured_output", False),
            timeouts=FrozenDict(tuple(dict(constraint_values.get("timeouts", {})).items())),
            delivery_enabled=bool(delivery.get("enabled", False)),
            delivery_remote=delivery.get("remote"),
            delivery_branch=delivery.get("branch"),
            unknown_fields=FrozenDict(
                tuple(
                    (name, value)
                    for name, value in constraint_values.items()
                    if name not in known_constraint_names
                )
            ),
        ),
        capability_manifest=CapabilityManifest(FrozenDict()),
        requested_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_happy_path_receipt_is_final_and_retry_is_idempotent(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    request = _request()
    first = await engine.run(request)
    second = await engine.run(request)

    assert first == second
    assert first.status is ReceiptStatus.SUCCEEDED
    assert first.verify_evidence()
    assert provider.calls == 1
    assert first.evidence["delivery"]["state"] == "not_requested"


@pytest.mark.asyncio
async def test_process_success_does_not_imply_business_completion(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    provider.business_done = False

    receipt = await engine.run(_request(execution_id="business-fail"))

    assert receipt.status is ReceiptStatus.FAILED
    assert receipt.error["reason"] == "business-verification-failed"
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_invalid_structured_output_has_distinct_reason(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    provider.structured = False

    receipt = await engine.run(_request(execution_id="structured-fail"))

    assert receipt.error["reason"] == "invalid-structured-output"


@pytest.mark.asyncio
async def test_rejection_writes_refused_receipt_and_redacts_secrets(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, runtime = governed
    request = _request(
        execution_id="rejected",
        governance={
            "authority": {"grant": "test", "api_key": "top-secret"},
            "constraints": {"future_required_boundary": True},
        },
    )

    receipt = await engine.run(request)

    assert receipt.termination is ReceiptTermination.REFUSED
    assert receipt.status is ReceiptStatus.FAILED
    assert receipt.is_finalized
    assert provider.calls == 0
    persisted = (
        runtime.executions_dir / _digest(request.execution_id) / "rejection.json"
    ).read_text(encoding="utf-8")
    assert "top-secret" not in persisted
    assert "[REDACTED]" in persisted
    assert "top-secret" not in (
        runtime.receipts_dir / f"{_digest(request.execution_id)}.json"
    ).read_text(encoding="utf-8")


def _digest(execution_id: object) -> str:
    return hashlib.sha256(str(execution_id).encode()).hexdigest()


@pytest.mark.asyncio
async def test_provider_error_and_timeout_have_distinct_reasons(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    provider.error = RuntimeError("provider exploded")
    errored = await engine.run(_request(execution_id="provider-error"))
    assert errored.error["reason"] == "provider-error"

    provider.error = None
    provider.delay = 0.1
    timed = await engine.run(
        _request(
            execution_id="provider-timeout",
            governance={
                "authority": {"grant": "test"},
                "constraints": {"timeouts": {"execute_s": 0.01}},
            },
        )
    )
    assert timed.error["reason"] == "provider-timeout"


@pytest.mark.asyncio
async def test_requested_filesystem_isolation_refuses_before_invoke(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    receipt = await engine.run(
        _request(
            execution_id="isolation-refused",
            governance={
                "authority": {"grant": "test"},
                "constraints": {"filesystem_isolation": True},
            },
        )
    )
    assert receipt.termination is ReceiptTermination.REFUSED
    assert receipt.error["reason"] == "capability-mismatch"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_cancellation_persists_terminal_receipt(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    provider.delay = 1.0
    request = _request(execution_id="cancelled")
    running = asyncio.create_task(engine.run(request))
    await asyncio.sleep(0.02)

    assert engine.cancel(request.execution_id)
    receipt = await running

    assert receipt.status is ReceiptStatus.CANCELLED
    assert receipt.error["reason"] == "aborted"
    assert engine.status(request.execution_id).cancellation_requested


@pytest.mark.asyncio
async def test_requested_delivery_is_pushed_and_independently_verified(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, _, _ = governed
    receipt = await engine.run(
        _request(
            execution_id="delivered",
            governance={
                "authority": {"grant": "test"},
                "constraints": {},
                "delivery": {"enabled": True},
            },
        )
    )

    assert receipt.status is ReceiptStatus.SUCCEEDED
    assert receipt.evidence["delivery"]["state"] == "verified"
    assert receipt.evidence["delivery"]["local_sha"] == receipt.evidence["delivery"]["verified_sha"]


@pytest.mark.asyncio
async def test_relay_messages_are_correlated_causal_and_ack_safe(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, _, runtime = governed
    relay = DurableRelay(runtime, engine.seats)
    engine.relay = relay
    request = _request(execution_id="relayed")

    await engine.run(request)

    claimed = relay.claim("local://seat-instance", owner="test")
    assert claimed is not None
    assert claimed.message.conversation_id == str(request.execution_id)
    ack = relay.ack(
        claimed.message.message_id,
        owner="test",
        lease_token=claimed.lease_token,
    )
    assert relay.acknowledgement(ack.message_id) == ack


@pytest.mark.asyncio
async def test_cli_receipt_json_and_stable_not_found_exit(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
    tmp_path: Path,
) -> None:
    engine, _, runtime = governed
    request = _request(execution_id="cli-receipt")
    receipt = await engine.run(request)
    checkout = receipt.evidence["git"]["identity"]["checkout"]
    config = tmp_path / "wiring.json"
    config.write_text(
        json.dumps(
            {
                "runtime_root": str(runtime.root),
                "repositories": [{"repository_id": "repo", "checkout": checkout}],
                "providers": [],
                "backends": ["bare"],
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    found = runner.invoke(
        app,
        ["governed", "receipt", str(request.execution_id), "--config", str(config)],
    )
    missing = runner.invoke(
        app,
        ["governed", "receipt", "missing", "--config", str(config)],
    )

    assert found.exit_code == 0
    assert json.loads(found.stdout)["evidence_sha256"] == receipt.evidence_sha256
    assert missing.exit_code == 4
    assert json.loads(missing.stdout)["error"] == "not_found"

    shown = runner.invoke(
        app,
        ["receipt", "show", str(request.execution_id), "--config", str(config)],
    )
    assert shown.exit_code == 0
    assert json.loads(shown.stdout)["termination"] == "completed"


@pytest.mark.asyncio
async def test_resume_from_completed_provider_checkpoint_does_not_reinvoke(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, runtime = governed
    request = _request(execution_id="checkpoint-resume")
    await engine.run(request)
    digest = hashlib.sha256(str(request.execution_id).encode()).hexdigest()
    receipt_path = runtime.receipts_dir / f"{digest}.json"
    state_path = runtime.executions_dir / digest / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    receipt_path.unlink()
    state["phase"] = "provider_completed"
    for key in ("delivery", "git_evidence", "receipt_sha256"):
        state.pop(key, None)
    state_path.write_text(json.dumps(state), encoding="utf-8")

    recovered = await engine.run(request)

    assert recovered.status is ReceiptStatus.SUCCEEDED
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_ambiguous_provider_checkpoint_fails_without_duplicate_invocation(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, runtime = governed
    request = _request(execution_id="checkpoint-ambiguous")
    await engine.run(request)
    digest = hashlib.sha256(str(request.execution_id).encode()).hexdigest()
    receipt_path = runtime.receipts_dir / f"{digest}.json"
    state_path = runtime.executions_dir / digest / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    receipt_path.unlink()
    state["phase"] = "provider_invoking"
    state.pop("provider_result", None)
    state.pop("receipt_sha256", None)
    state_path.write_text(json.dumps(state), encoding="utf-8")

    recovered = await engine.run(request)

    assert recovered.status is ReceiptStatus.FAILED
    assert recovered.error["reason"] == "ambiguous-provider-invocation"
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_isolation_capability_mismatch_rejects_before_provider_side_effect(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    request = _request(
        execution_id="isolation-rejected",
        governance={
            "authority": {"grant": "test"},
            "constraints": {"filesystem_isolation": True},
        },
    )

    receipt = await engine.run(request)

    assert receipt.termination is ReceiptTermination.REFUSED
    assert receipt.error["reason"] == "capability-mismatch"
    assert provider.calls == 0
    assert engine.receipt(request.execution_id) == receipt


@pytest.mark.asyncio
async def test_dirty_repository_failure_is_distinct_and_precedes_provider(
    governed: tuple[GovernedExecutionEngine, FakeProvider, RuntimeRoot],
) -> None:
    engine, provider, _ = governed
    checkout = engine.repositories.resolve(RepositoryId("repo")).checkout
    (checkout / "operator-dirty.txt").write_text("dirty\n", encoding="utf-8")

    receipt = await engine.run(_request(execution_id="dirty-repository"))

    assert receipt.status is ReceiptStatus.FAILED
    assert receipt.error["reason"] == "repository-dirty"
    assert provider.calls == 0
