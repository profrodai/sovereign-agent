"""Immutable execution receipts with one-time cryptographic finalization."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar

from ._core import (
    ContractValidationError,
    FrozenDict,
    canonical_json_bytes,
    format_datetime,
    freeze_json,
    merge_unknown,
    parse_datetime,
    require_object,
    require_string,
    split_known,
    thaw_json,
)
from .ids import ExecutionId, InvocationId

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ReceiptStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self is not ReceiptStatus.RUNNING


@dataclass(frozen=True)
class ExecutionReceipt:
    """A deeply immutable observation of an execution.

    Draft receipts have no ``evidence_sha256``. A terminal draft can be
    finalized once, yielding a new immutable object whose digest covers every
    wire field except the digest itself. Corrections create a new finalized
    receipt linked by ``supersedes_sha256``.
    """

    SCHEMA_VERSION: ClassVar[str] = "1.0"

    execution_id: ExecutionId
    invocation_id: InvocationId
    status: ReceiptStatus
    started_at: datetime
    completed_at: datetime | None
    result: Any = None
    error: Mapping[str, Any] | None = None
    evidence: Mapping[str, Any] = field(default_factory=FrozenDict)
    evidence_sha256: str | None = None
    supersedes_sha256: str | None = None
    correction_sequence: int = 0
    schema_version: str = SCHEMA_VERSION
    unknown_fields: FrozenDict = field(default_factory=FrozenDict, repr=False)

    _KNOWN: ClassVar[frozenset[str]] = frozenset(
        {
            "schema_version",
            "execution_id",
            "invocation_id",
            "status",
            "started_at",
            "completed_at",
            "result",
            "error",
            "evidence",
            "evidence_sha256",
            "supersedes_sha256",
            "correction_sequence",
        }
    )

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise ContractValidationError("execution_id must be ExecutionId")
        if not isinstance(self.invocation_id, InvocationId):
            raise ContractValidationError("invocation_id must be InvocationId")
        if not isinstance(self.status, ReceiptStatus):
            raise ContractValidationError("status must be ReceiptStatus")
        if self.schema_version != self.SCHEMA_VERSION:
            raise ContractValidationError(f"schema_version must be {self.SCHEMA_VERSION!r}")
        format_datetime(self.started_at, "started_at")
        if self.completed_at is not None:
            format_datetime(self.completed_at, "completed_at")
            if self.completed_at < self.started_at:
                raise ContractValidationError("completed_at cannot precede started_at")
        if self.status.is_terminal != (self.completed_at is not None):
            raise ContractValidationError(
                "terminal statuses require completed_at; running status forbids it"
            )
        if self.status is ReceiptStatus.SUCCEEDED and self.error is not None:
            raise ContractValidationError("a succeeded receipt cannot contain an error")
        if self.status is not ReceiptStatus.SUCCEEDED and self.result is not None:
            raise ContractValidationError("only a succeeded receipt may contain a result")
        if self.status is ReceiptStatus.FAILED and self.error is None:
            raise ContractValidationError("a failed receipt requires an error object")
        if not isinstance(self.correction_sequence, int) or isinstance(
            self.correction_sequence, bool
        ):
            raise ContractValidationError("correction_sequence must be an integer")
        if self.correction_sequence < 0:
            raise ContractValidationError("correction_sequence cannot be negative")
        if (self.correction_sequence == 0) != (self.supersedes_sha256 is None):
            raise ContractValidationError(
                "a correction must have both a positive sequence and supersedes_sha256"
            )
        for name, digest in (
            ("evidence_sha256", self.evidence_sha256),
            ("supersedes_sha256", self.supersedes_sha256),
        ):
            if digest is not None and not _SHA256_PATTERN.fullmatch(digest):
                raise ContractValidationError(f"{name} must be a lowercase SHA-256 hex digest")
        object.__setattr__(self, "result", freeze_json(self.result, path="result"))
        if self.error is not None:
            object.__setattr__(
                self, "error", freeze_json(require_object(self.error, "error"), path="error")
            )
        object.__setattr__(
            self,
            "evidence",
            freeze_json(require_object(self.evidence, "evidence"), path="evidence"),
        )
        object.__setattr__(
            self,
            "unknown_fields",
            freeze_json(
                require_object(self.unknown_fields, "unknown_fields"), path="unknown_fields"
            ),
        )
        if self.evidence_sha256 is not None and not self.verify_evidence():
            raise ContractValidationError("evidence_sha256 does not match receipt contents")

    @property
    def is_finalized(self) -> bool:
        return self.evidence_sha256 is not None

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    @property
    def is_successful(self) -> bool:
        return self.status is ReceiptStatus.SUCCEEDED

    def _unsigned_dict(self) -> dict[str, Any]:
        value = self.to_dict()
        value.pop("evidence_sha256")
        return value

    def expected_evidence_sha256(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self._unsigned_dict())).hexdigest()

    def verify_evidence(self) -> bool:
        return (
            self.evidence_sha256 is not None
            and self.evidence_sha256 == self.expected_evidence_sha256()
        )

    def finalize(self) -> ExecutionReceipt:
        """Finalize a terminal draft exactly once."""
        if self.is_finalized:
            raise ContractValidationError("receipt has already been finalized")
        if not self.is_terminal:
            raise ContractValidationError("a running receipt cannot be finalized")
        digest = self.expected_evidence_sha256()
        return replace(self, evidence_sha256=digest)

    def supersede(
        self,
        *,
        status: ReceiptStatus,
        completed_at: datetime,
        result: Any = None,
        error: Mapping[str, Any] | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> ExecutionReceipt:
        """Create and finalize a linked correction; never alter this receipt."""
        if not self.is_finalized:
            raise ContractValidationError("only a finalized receipt can be superseded")
        correction = ExecutionReceipt(
            execution_id=self.execution_id,
            invocation_id=self.invocation_id,
            status=status,
            started_at=self.started_at,
            completed_at=completed_at,
            result=result,
            error=error,
            evidence=self.evidence if evidence is None else evidence,
            supersedes_sha256=self.evidence_sha256,
            correction_sequence=self.correction_sequence + 1,
            unknown_fields=self.unknown_fields,
        )
        return correction.finalize()

    def to_dict(self) -> dict[str, Any]:
        known: dict[str, Any] = {
            "schema_version": self.schema_version,
            "execution_id": str(self.execution_id),
            "invocation_id": str(self.invocation_id),
            "status": self.status.value,
            "started_at": format_datetime(self.started_at, "started_at"),
            "completed_at": (
                format_datetime(self.completed_at, "completed_at")
                if self.completed_at is not None
                else None
            ),
            "result": thaw_json(self.result),
            "error": thaw_json(self.error) if self.error is not None else None,
            "evidence": thaw_json(self.evidence),
            "evidence_sha256": self.evidence_sha256,
            "supersedes_sha256": self.supersedes_sha256,
            "correction_sequence": self.correction_sequence,
        }
        return merge_unknown(known, self.unknown_fields)

    @classmethod
    def from_dict(cls, value: object) -> ExecutionReceipt:
        data = require_object(value, "execution_receipt")
        known, unknown = split_known(data, cls._KNOWN)
        required = cls._KNOWN - {"result", "error", "evidence_sha256", "supersedes_sha256"}
        missing = sorted(required - known.keys())
        if missing:
            raise ContractValidationError(f"missing required fields: {', '.join(missing)}")
        try:
            status = ReceiptStatus(require_string(known["status"], "status"))
        except ValueError as exc:
            raise ContractValidationError("status is not a recognized receipt status") from exc
        completed = known["completed_at"]
        sequence = known["correction_sequence"]
        if not isinstance(sequence, int) or isinstance(sequence, bool):
            raise ContractValidationError("correction_sequence must be an integer")
        return cls(
            schema_version=require_string(known["schema_version"], "schema_version"),
            execution_id=ExecutionId(require_string(known["execution_id"], "execution_id")),
            invocation_id=InvocationId(require_string(known["invocation_id"], "invocation_id")),
            status=status,
            started_at=parse_datetime(known["started_at"], "started_at"),
            completed_at=(
                parse_datetime(completed, "completed_at") if completed is not None else None
            ),
            result=known.get("result"),
            error=known.get("error"),
            evidence=freeze_json(require_object(known["evidence"], "evidence")),
            evidence_sha256=known.get("evidence_sha256"),
            supersedes_sha256=known.get("supersedes_sha256"),
            correction_sequence=sequence,
            unknown_fields=unknown,
        )


def lifecycle_complete(receipt: ExecutionReceipt) -> bool:
    """Lifecycle predicate; deliberately independent of evidence validity."""
    return receipt.is_terminal


def evidence_verified(receipt: ExecutionReceipt) -> bool:
    """Evidence predicate; deliberately independent of lifecycle outcome."""
    return receipt.verify_evidence()


__all__ = [
    "ExecutionReceipt",
    "ReceiptStatus",
    "evidence_verified",
    "lifecycle_complete",
]
