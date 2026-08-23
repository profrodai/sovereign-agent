"""Versioned wire contracts for governed execution and receipts."""

from typing import TYPE_CHECKING, Any

from ._core import ContractValidationError, FrozenDict
from .canonical import canonical_json_bytes
from .capabilities import (
    EvidenceLevel,
    RuntimeCapabilityAssertion,
    RuntimeCapabilityManifest,
    RuntimeRequirement,
)
from .execution import (
    ExecutionConstraints,
    GovernedExecutionRequest,
    MutationPolicy,
    NetworkPolicy,
    SandboxMinimum,
)
from .ids import (
    ExecutionId,
    InvocationId,
    ProviderSessionId,
    RelayMessageId,
    RepositoryId,
    SeatId,
    SeatInstanceId,
    SovereignSessionId,
    WorkerHandleId,
)
from .receipts import (
    CommitEvidence,
    ExecutionReceipt,
    ReceiptStatus,
    ReceiptTermination,
    RepositoryReceipt,
    UsageRecord,
    VerificationCommand,
    evidence_verified,
    lifecycle_complete,
)
from .redaction import REDACTED, redact_json, redact_mapping, redact_text

if TYPE_CHECKING:
    Capability = RuntimeCapabilityAssertion
    CapabilityManifest = RuntimeCapabilityManifest


def __getattr__(name: str) -> Any:
    if name in {"Capability", "CapabilityManifest"}:
        from . import capabilities as cap_mod

        return getattr(cap_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Capability",
    "CapabilityManifest",
    "CommitEvidence",
    "ContractValidationError",
    "EvidenceLevel",
    "ExecutionConstraints",
    "ExecutionId",
    "ExecutionReceipt",
    "FrozenDict",
    "GovernedExecutionRequest",
    "InvocationId",
    "MutationPolicy",
    "NetworkPolicy",
    "ProviderSessionId",
    "RelayMessageId",
    "REDACTED",
    "ReceiptStatus",
    "ReceiptTermination",
    "RepositoryId",
    "RepositoryReceipt",
    "RuntimeCapabilityAssertion",
    "RuntimeCapabilityManifest",
    "RuntimeRequirement",
    "SandboxMinimum",
    "SeatId",
    "SeatInstanceId",
    "SovereignSessionId",
    "UsageRecord",
    "VerificationCommand",
    "WorkerHandleId",
    "canonical_json_bytes",
    "evidence_verified",
    "lifecycle_complete",
    "redact_json",
    "redact_mapping",
    "redact_text",
]
