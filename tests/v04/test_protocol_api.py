"""Unit 1 protocol, signing, version negotiation, idempotency, and local API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sovereign_agent.api import (
    PROTOCOL_VERSION,
    Keyring,
    ProtocolEnvelope,
    ProtocolError,
    UnixSocketApiServer,
    UnixSocketClient,
    build_local_stack,
    signed_copy,
)
from sovereign_agent.runtime import RuntimeRoot


def _envelope(**overrides: object) -> ProtocolEnvelope:
    now = datetime.now(UTC)
    data = {
        "protocol": "sovereign-agent",
        "protocol_version": PROTOCOL_VERSION,
        "message_id": "msg_01JTEST",
        "correlation_id": "exec_01JTEST",
        "causation_id": "msg_01JCAUSE",
        "sent_at": now.isoformat().replace("+00:00", "Z"),
        "sender": "zero-employee://instance/master-01",
        "recipient": "sovereign-agent://instance/research-01",
        "kind": "echo",
        "body": {"idempotency_key": "idem-1", "value": 1},
        "auth": {"scheme": "hmac-sha256", "key_id": "operator-local-01", "signature": ""},
    }
    data.update(overrides)
    return ProtocolEnvelope.from_dict(data)


def _stack(tmp_path: Path):
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    keyring = Keyring({"operator-local-01": b"secret"})
    dispatcher, transport = build_local_stack(
        runtime,
        keyring,
        handlers={"echo": lambda envelope: {"echo": dict(envelope.body), "ok": True}},
    )
    return runtime, keyring, dispatcher, transport


def test_canonical_signature_covers_unsigned_bytes(tmp_path: Path) -> None:
    _, keyring, _, transport = _stack(tmp_path)
    signed = signed_copy(_envelope(), keyring)
    assert signed.auth.signature
    response = transport.send(signed)
    assert response.status == 200
    assert response.body["ok"] is True


def test_body_mutation_after_sign_is_rejected(tmp_path: Path) -> None:
    _, keyring, _, transport = _stack(tmp_path)
    signed = signed_copy(_envelope(), keyring)
    mutated = ProtocolEnvelope.from_dict(
        {**signed.to_dict(), "body": {"idempotency_key": "idem-1", "value": 2}}
    )
    response = transport.send(mutated)
    assert response.status == 401
    assert response.body["reason"] == "unauthenticated"


def test_replay_of_same_message_id_is_conflict(tmp_path: Path) -> None:
    _, keyring, _, transport = _stack(tmp_path)
    signed = signed_copy(_envelope(), keyring)
    assert transport.send(signed).status == 200
    again = transport.send(signed)
    assert again.status == 409
    assert again.body["reason"] == "replay"


def test_unsupported_major_version_refuses_before_handler(tmp_path: Path) -> None:
    with pytest.raises(ProtocolError) as exc:
        _envelope(protocol_version="2.0")
    assert exc.value.reason == "unsupported-version"
    assert ">=1.0,<2.0" in exc.value.supported_range


def test_unknown_required_fields_fail_closed() -> None:
    with pytest.raises(ProtocolError) as exc:
        _envelope(required_fields=["future_gate"])
    assert exc.value.reason == "unknown-required-field"


def test_unknown_optional_fields_survive_round_trip() -> None:
    envelope = _envelope(**{"trace_hint": "keep-me"})
    restored = ProtocolEnvelope.from_dict(envelope.to_dict())
    assert restored.to_dict()["trace_hint"] == "keep-me"


def test_duplicate_idempotency_key_with_different_body_conflicts(tmp_path: Path) -> None:
    _, keyring, _, transport = _stack(tmp_path)
    first = signed_copy(_envelope(message_id="msg_a"), keyring)
    assert transport.send(first).status == 200
    second = signed_copy(
        _envelope(message_id="msg_b", body={"idempotency_key": "idem-1", "value": 99}),
        keyring,
    )
    response = transport.send(second)
    assert response.status == 409
    assert response.body["reason"] == "idempotency-conflict"


def test_duplicate_idempotency_key_same_body_returns_original(tmp_path: Path) -> None:
    _, keyring, _, transport = _stack(tmp_path)
    first = signed_copy(_envelope(message_id="msg_a"), keyring)
    original = transport.send(first)
    second = signed_copy(_envelope(message_id="msg_b"), keyring)
    replayed = transport.send(second)
    assert replayed.status == 200
    assert replayed.body == original.body


def test_observer_cannot_mutate(tmp_path: Path) -> None:
    _, keyring, _, transport = _stack(tmp_path)
    signed = signed_copy(_envelope(), keyring)
    response = transport.send(signed, observer=True)
    assert response.status == 403
    assert response.body["reason"] == "observer-forbidden"


def test_unix_socket_http_round_trip(tmp_path: Path) -> None:
    runtime, keyring, dispatcher, _ = _stack(tmp_path)
    del runtime
    socket_path = Path("/tmp") / f"sa-v04-{tmp_path.name[-12:]}.sock"
    with UnixSocketApiServer(socket_path, dispatcher):
        client = UnixSocketClient(socket_path)
        signed = signed_copy(_envelope(message_id="msg_sock"), keyring)
        response = client.post(signed)
        assert response.status == 200
        assert response.body["ok"] is True
        observer = client.post(signed_copy(_envelope(message_id="msg_obs"), keyring), observer=True)
        assert observer.status == 403


def test_skewed_sent_at_is_replay_window_failure(tmp_path: Path) -> None:
    _, keyring, _, transport = _stack(tmp_path)
    stale = datetime.now(UTC) - timedelta(hours=1)
    signed = signed_copy(
        _envelope(sent_at=stale.isoformat().replace("+00:00", "Z"), message_id="msg_old"), keyring
    )
    response = transport.send(signed)
    assert response.status == 409
    assert response.body["reason"] == "replay"
