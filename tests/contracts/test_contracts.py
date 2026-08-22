from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from sovereign_agent.contracts import (
    Capability,
    CapabilityManifest,
    ContractValidationError,
    EvidenceLevel,
    ExecutionId,
    ExecutionReceipt,
    GovernedExecutionRequest,
    InvocationId,
    ReceiptStatus,
    RepositoryId,
    SeatInstanceId,
    SovereignSessionId,
    canonical_json_bytes,
    evidence_verified,
    lifecycle_complete,
    redact_json,
    redact_text,
)

NOW = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)


def manifest() -> CapabilityManifest:
    return CapabilityManifest(
        {
            "network": Capability(
                available=False,
                evidence_level=EvidenceLevel.ENFORCED,
                details={"mechanism": "sandbox"},
            ),
            "shell": Capability(
                available=True,
                evidence_level=EvidenceLevel.DECLARED,
            ),
        }
    )


def request() -> GovernedExecutionRequest:
    return GovernedExecutionRequest(
        seat_instance_id=SeatInstanceId("seat-01"),
        sovereign_session_id=SovereignSessionId("session-01"),
        execution_id=ExecutionId("execution-01"),
        invocation_id=InvocationId("invocation-01"),
        repository_id=RepositoryId("repo:zeroemployee/sovereign-agent"),
        operation="run",
        input={"prompt": "check", "paths": ["src"]},
        governance={"network": "deny"},
        capability_manifest=manifest(),
        requested_at=NOW,
    )


def terminal_receipt() -> ExecutionReceipt:
    return ExecutionReceipt(
        execution_id=ExecutionId("execution-01"),
        invocation_id=InvocationId("invocation-01"),
        status=ReceiptStatus.SUCCEEDED,
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=2),
        result={"exit_code": 0},
        evidence={"stdout": "ok"},
    )


def test_typed_ids_validate_and_do_not_compare_as_plain_strings() -> None:
    assert str(SeatInstanceId("seat-01")) == "seat-01"
    assert SeatInstanceId("same") != ExecutionId("same")
    for invalid in ("", " spaces ", "trailing-", "x" * 129):
        with pytest.raises(ContractValidationError):
            SeatInstanceId(invalid)


def test_request_strict_round_trip_and_unknown_preservation() -> None:
    wire = request().to_dict()
    wire["future_contract_field"] = {"mode": "new"}
    restored = GovernedExecutionRequest.from_dict(wire)
    assert restored.to_dict() == wire
    assert restored.unknown_fields["future_contract_field"]["mode"] == "new"


def test_request_rejects_missing_wrong_and_naive_values() -> None:
    wire = request().to_dict()
    del wire["governance"]
    with pytest.raises(ContractValidationError, match="missing required"):
        GovernedExecutionRequest.from_dict(wire)
    with pytest.raises(ContractValidationError, match="timezone-aware"):
        GovernedExecutionRequest(**{**request().__dict__, "requested_at": datetime(2026, 1, 1)})


def test_capability_availability_and_evidence_are_independent() -> None:
    capabilities = manifest()
    assert not capabilities.is_available("network")
    assert capabilities.has_evidence("network", EvidenceLevel.ENFORCED)
    assert capabilities.is_available("shell")
    assert not capabilities.has_evidence("shell", EvidenceLevel.PROBED)


def test_capability_unknown_fields_round_trip() -> None:
    wire = {
        "capabilities": {
            "gpu": {
                "available": None,
                "evidence_level": "unknown",
                "details": {},
                "future": 7,
            }
        },
        "manifest_extension": True,
    }
    assert CapabilityManifest.from_dict(wire).to_dict() == wire


def test_canonical_json_is_byte_stable_and_rejects_non_json() -> None:
    left = canonical_json_bytes({"b": [2, 1], "a": "é"})
    right = canonical_json_bytes({"a": "é", "b": [2, 1]})
    assert left == right == b'{"a":"\xc3\xa9","b":[2,1]}'
    with pytest.raises(ContractValidationError):
        canonical_json_bytes({"bad": {1, 2}})


def test_redaction_is_recursive_case_insensitive_and_non_mutating() -> None:
    source = {
        "Authorization": "Bearer abc",
        "nested": [{"api-key": "secret"}, {"safe": "kept"}],
    }
    redacted = redact_json(source)
    assert redacted == {
        "Authorization": "[REDACTED]",
        "nested": [{"api-key": "[REDACTED]"}, {"safe": "kept"}],
    }
    assert source["Authorization"] == "Bearer abc"
    assert redact_text("token=abc123 safe=yes") == "token=[REDACTED] safe=yes"


def test_receipt_invalid_lifecycle_combinations_are_rejected() -> None:
    with pytest.raises(ContractValidationError, match="terminal statuses"):
        ExecutionReceipt(
            execution_id=ExecutionId("execution-01"),
            invocation_id=InvocationId("invocation-01"),
            status=ReceiptStatus.SUCCEEDED,
            started_at=NOW,
            completed_at=None,
        )
    with pytest.raises(ContractValidationError, match="requires an error"):
        ExecutionReceipt(
            execution_id=ExecutionId("execution-01"),
            invocation_id=InvocationId("invocation-01"),
            status=ReceiptStatus.FAILED,
            started_at=NOW,
            completed_at=NOW,
        )


def test_lifecycle_and_evidence_predicates_are_independent() -> None:
    receipt = terminal_receipt()
    assert lifecycle_complete(receipt)
    assert not evidence_verified(receipt)
    finalized = receipt.finalize()
    assert lifecycle_complete(finalized)
    assert evidence_verified(finalized)


def test_receipt_finalizes_exactly_once_and_round_trips() -> None:
    finalized = terminal_receipt().finalize()
    assert finalized.evidence_sha256 is not None
    assert len(finalized.evidence_sha256) == 64
    assert ExecutionReceipt.from_dict(finalized.to_dict()) == finalized
    with pytest.raises(ContractValidationError, match="already"):
        finalized.finalize()


def test_receipt_rejects_tampered_finalized_wire_data() -> None:
    wire = terminal_receipt().finalize().to_dict()
    wire["evidence"]["stdout"] = "tampered"
    with pytest.raises(ContractValidationError, match="does not match"):
        ExecutionReceipt.from_dict(wire)


def test_receipt_is_deeply_immutable_and_corrections_supersede() -> None:
    original = terminal_receipt().finalize()
    with pytest.raises(TypeError):
        original.evidence["stdout"] = "changed"
    with pytest.raises(FrozenInstanceError):
        original.status = ReceiptStatus.FAILED

    correction = original.supersede(
        status=ReceiptStatus.FAILED,
        completed_at=NOW + timedelta(seconds=3),
        error={"code": "POST_CHECK_FAILED"},
        evidence={"check": "failed"},
    )
    assert correction.is_finalized
    assert correction.supersedes_sha256 == original.evidence_sha256
    assert correction.correction_sequence == 1
    assert original.status is ReceiptStatus.SUCCEEDED


def test_receipt_unknown_fields_are_preserved_and_covered_by_digest() -> None:
    draft_wire = terminal_receipt().to_dict()
    draft_wire["future_attestation"] = {"issuer": "zeo"}
    finalized = ExecutionReceipt.from_dict(draft_wire).finalize()
    assert finalized.to_dict()["future_attestation"] == {"issuer": "zeo"}
    tampered = finalized.to_dict()
    tampered["future_attestation"]["issuer"] = "other"
    with pytest.raises(ContractValidationError):
        ExecutionReceipt.from_dict(tampered)
