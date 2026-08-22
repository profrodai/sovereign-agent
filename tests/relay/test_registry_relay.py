from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from multiprocessing import get_context
from pathlib import Path

import pytest

from sovereign_agent.contracts import RelayMessageId
from sovereign_agent.registry import (
    RegistrationConflict,
    RuntimeAddress,
    SeatLifecycle,
    SeatRegistry,
)
from sovereign_agent.relay import (
    DeliveryStatus,
    DuplicateMessageConflict,
    DurableRelay,
    LeaseLost,
    RelayCorruptionError,
    RelayMessage,
)
from sovereign_agent.runtime import RuntimeRoot


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def _process_enqueue(root_path: str) -> str:
    root = RuntimeRoot.open(Path(root_path))
    registry = SeatRegistry(root)
    sender = registry.get("sender-1")
    recipient = registry.get("recipient-1")
    relay = DurableRelay(root, registry)
    record = relay.enqueue(
        RelayMessage(
            message_id=RelayMessageId("process-message"),
            sender=sender.address,
            recipient=recipient.address,
            kind="task",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            payload={"value": 1},
        )
    )
    return record.message.message_id.value


@pytest.fixture
def system(tmp_path):
    clock = Clock()
    root = RuntimeRoot(tmp_path / "runtime").initialize()
    registry = SeatRegistry(root, clock=clock)
    sender = registry.register(
        instance_id="sender-1",
        seat_id="sender",
        provider="native",
        backend="process",
        capabilities=["send"],
    )
    recipient = registry.register(
        instance_id="recipient-1",
        seat_id="recipient",
        provider="native",
        backend="process",
        capabilities=["receive"],
    )
    relay = DurableRelay(
        root, registry, clock=clock, max_attempts=2, backoff_base=2, backoff_cap=10
    )
    return clock, root, registry, sender, recipient, relay


def message(system, identifier: str, *, created_offset: int = 0) -> RelayMessage:
    clock, _, _, sender, recipient, _ = system
    return RelayMessage(
        message_id=RelayMessageId(identifier),
        sender=sender.address,
        recipient=recipient.address,
        kind="task",
        correlation_id="corr",
        created_at=clock.now + timedelta(seconds=created_offset),
        payload={"nested": {"value": 1}},
    )


def test_registration_reopen_conflict_and_staleness(system):
    clock, root, registry, sender, _, _ = system
    reopened = SeatRegistry(RuntimeRoot.open(root.root), clock=clock)
    assert reopened.get("sender-1") == sender
    assert (
        reopened.register(
            instance_id="sender-1",
            seat_id="sender",
            provider="native",
            backend="process",
            capabilities=["send"],
        )
        == sender
    )
    with pytest.raises(RegistrationConflict):
        reopened.register(
            instance_id="sender-1",
            seat_id="other",
            provider="native",
            backend="process",
        )
    clock.advance(11)
    assert {item.instance_id.value for item in reopened.stale(10)} == {
        "sender-1",
        "recipient-1",
    }
    live = reopened.heartbeat("sender-1", lifecycle=SeatLifecycle.RUNNING, status={"pid": 7})
    assert live.lifecycle is SeatLifecycle.RUNNING
    assert reopened.is_live("sender-1", 10)
    assert live.registered_at == sender.registered_at


def test_address_validation_rejects_traversal():
    with pytest.raises(ValueError):
        RuntimeAddress("local://../escape")
    with pytest.raises(ValueError):
        RuntimeAddress("local://seat/../escape")
    with pytest.raises(ValueError):
        RuntimeAddress("tcp://host/seat")


def test_enqueue_is_persistent_idempotent_and_payload_is_immutable(system):
    _, root, registry, _, _, relay = system
    envelope = message(system, "m1")
    first = relay.enqueue(envelope)
    assert relay.enqueue(envelope) == first
    with pytest.raises(TypeError):
        envelope.payload["new"] = 1  # type: ignore[index]
    conflict = RelayMessage(
        **{**envelope.__dict__, "kind": "different"}  # type: ignore[arg-type]
    )
    with pytest.raises(DuplicateMessageConflict):
        relay.enqueue(conflict)
    reopened = DurableRelay(RuntimeRoot.open(root.root), registry)
    assert reopened.get("m1").message == envelope


def test_ordered_claim_ack_and_acknowledgement(system):
    clock, _, _, _, recipient, relay = system
    relay.enqueue(message(system, "later", created_offset=1))
    relay.enqueue(message(system, "first"))
    claim = relay.claim(recipient.address, owner="worker", lease_seconds=5)
    assert claim is not None and claim.message.message_id.value == "first"
    assert relay.claim(recipient.address, owner="other") is None
    ack = relay.ack("first", owner="worker", lease_token=claim.lease_token)
    assert ack.message_id.value == "first"
    assert relay.acknowledgement("first") == ack
    clock.advance(1)
    second = relay.claim(recipient.address, owner="worker")
    assert second is not None and second.message.message_id.value == "later"


def test_nack_backoff_and_max_attempt_dead_letter(system):
    clock, _, _, _, recipient, relay = system
    relay.enqueue(message(system, "retry"))
    first = relay.claim(recipient.address, owner="one")
    assert first is not None
    pending = relay.nack("retry", owner="one", lease_token=first.lease_token, error="temporary")
    assert pending.available_at == clock.now + timedelta(seconds=2)
    assert relay.claim(recipient.address, owner="one") is None
    clock.advance(2)
    second = relay.claim(recipient.address, owner="two")
    assert second is not None and second.attempt_count == 2
    dead = relay.nack("retry", owner="two", lease_token=second.lease_token, error="permanent")
    assert dead.status is DeliveryStatus.DEAD_LETTERED
    assert relay.dead_letters() == [dead]


def test_expired_lease_is_recovered_and_old_claim_is_fenced(system):
    clock, _, _, _, recipient, relay = system
    relay.enqueue(message(system, "leased"))
    old = relay.claim(recipient.address, owner="old", lease_seconds=3)
    assert old is not None
    clock.advance(4)
    new = relay.claim(recipient.address, owner="new", lease_seconds=3)
    assert new is not None and new.lease_token != old.lease_token
    with pytest.raises(LeaseLost):
        relay.ack("leased", owner="old", lease_token=old.lease_token)
    relay.ack("leased", owner="new", lease_token=new.lease_token)


def test_expired_claim_cannot_ack_before_takeover(system):
    clock, _, _, _, recipient, relay = system
    relay.enqueue(message(system, "expired-ack"))
    old = relay.claim(recipient.address, owner="old", lease_seconds=3)
    assert old is not None
    clock.advance(4)
    with pytest.raises(LeaseLost):
        relay.ack("expired-ack", owner="old", lease_token=old.lease_token)
    new = relay.claim(recipient.address, owner="new")
    assert new is not None
    relay.ack("expired-ack", owner="new", lease_token=new.lease_token)


def test_negative_acknowledgement_redacts_diagnostic_secrets(system):
    _, _, _, _, recipient, relay = system
    relay.enqueue(message(system, "redacted-nack"))
    claim = relay.claim(recipient.address, owner="worker")
    assert claim is not None
    record = relay.nack(
        "redacted-nack",
        owner="worker",
        lease_token=claim.lease_token,
        error="token=super-secret",
    )
    assert record.last_error == "token=[REDACTED]"


def test_corruption_is_quarantined_explicitly(system):
    _, root, _, _, recipient, relay = system
    relay.enqueue(message(system, "bad"))
    path = next((root.relay_dir / "messages").glob("*.json"))
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(RelayCorruptionError, match="quarantined"):
        relay.claim(recipient.address, owner="worker")
    assert list((root.relay_dir / "quarantine").glob("*.json"))


def test_concurrent_producers_dedupe_and_claimants_fence(system):
    _, _, _, _, recipient, relay = system
    envelope = message(system, "concurrent")
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(lambda _: relay.enqueue(envelope), range(20)))
    assert len({item.message.message_id for item in records}) == 1
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(
            pool.map(
                lambda index: relay.claim(recipient.address, owner=f"worker-{index}"),
                range(8),
            )
        )
    assert sum(item is not None for item in claims) == 1


def test_process_safe_enqueue_is_atomic(system):
    _, root, _, _, _, relay = system
    context = get_context("spawn")
    with context.Pool(4) as pool:
        results = pool.map(_process_enqueue, [str(root.root)] * 12)
    assert results == ["process-message"] * 12
    assert relay.get("process-message").attempt_count == 0
