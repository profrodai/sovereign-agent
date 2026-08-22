"""Immutable execution receipts with one-time cryptographic finalization."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
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
from .ids import (
    ExecutionId,
    InvocationId,
    ProviderSessionId,
    SeatId,
    SeatInstanceId,
    SovereignSessionId,
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ReceiptStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self is not ReceiptStatus.RUNNING


class ReceiptTermination(StrEnum):
    COMPLETED = "completed"
    REFUSED = "refused"
    ABORTED = "aborted"
    IDLE_TIMEOUT = "idle-timeout"
    COMPLETION_TIMEOUT = "completion-timeout"
    WORKER_TIMEOUT = "worker-timeout"
    PROVIDER_TIMEOUT = "provider-timeout"
    LIFECYCLE_TIMEOUT = "lifecycle-timeout"
    PROVIDER_ERROR = "provider-error"
    WORKER_ERROR = "worker-error"
    ISOLATION_UNAVAILABLE = "isolation-unavailable"
    INVALID_STRUCTURED_OUTPUT = "invalid-structured-output"
    VERIFICATION_FAILED = "verification-failed"
    DELIVERY_FAILED = "delivery-failed"
    BUSINESS_VERIFICATION_FAILED = "business-verification-failed"
    AMBIGUOUS_PROVIDER_INVOCATION = "ambiguous-provider-invocation"
    AMBIGUOUS_DELIVERY = "ambiguous-delivery"
    REPOSITORY_DIRTY = "repository-dirty"
    REPOSITORY_ERROR = "repository-error"


_STATUS_FOR_TERMINATION = {
    ReceiptTermination.COMPLETED: ReceiptStatus.SUCCEEDED,
    ReceiptTermination.ABORTED: ReceiptStatus.CANCELLED,
    ReceiptTermination.REFUSED: ReceiptStatus.FAILED,
}


def status_for_termination(
    termination: ReceiptTermination | None, status: ReceiptStatus
) -> ReceiptStatus:
    if termination is None:
        return status
    return _STATUS_FOR_TERMINATION.get(termination, ReceiptStatus.FAILED)


def default_termination(status: ReceiptStatus) -> ReceiptTermination | None:
    if status is ReceiptStatus.SUCCEEDED:
        return ReceiptTermination.COMPLETED
    if status is ReceiptStatus.CANCELLED:
        return ReceiptTermination.ABORTED
    if status is ReceiptStatus.FAILED:
        return ReceiptTermination.PROVIDER_ERROR
    return None


@dataclass(frozen=True)
class VerificationCommand:
    command: tuple[str, ...]
    exit_code: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.command, str) or not isinstance(self.command, Sequence):
            raise ContractValidationError("verification.command must be an argv array")
        object.__setattr__(
            self,
            "command",
            tuple(require_string(item, "verification.command") for item in self.command),
        )
        if not self.command:
            raise ContractValidationError("verification.command must not be empty")
        if self.exit_code is not None and (
            not isinstance(self.exit_code, int) or isinstance(self.exit_code, bool)
        ):
            raise ContractValidationError("verification.exit_code must be an integer")

    def to_dict(self) -> dict[str, Any]:
        return {"command": list(self.command), "exit_code": self.exit_code}

    @classmethod
    def from_dict(cls, value: object) -> VerificationCommand:
        data = require_object(value, "verification")
        command = data.get("command", data.get("argv"))
        return cls(command=tuple(command or ()), exit_code=data.get("exit_code"))


@dataclass(frozen=True)
class CommitEvidence:
    sha: str
    remote_contains: bool | None = None

    def __post_init__(self) -> None:
        require_string(self.sha, "commit.sha")
        if self.remote_contains is not None and not isinstance(self.remote_contains, bool):
            raise ContractValidationError("commit.remote_contains must be boolean or null")

    def to_dict(self) -> dict[str, Any]:
        return {"sha": self.sha, "remote_contains": self.remote_contains}

    @classmethod
    def from_dict(cls, value: object) -> CommitEvidence:
        data = require_object(value, "commit")
        contains = data.get("remote_contains")
        return cls(sha=require_string(data["sha"], "commit.sha"), remote_contains=contains)


@dataclass(frozen=True)
class RepositoryReceipt:
    remote: str | None = None
    branch: str | None = None
    base_commit: str | None = None
    commits: tuple[CommitEvidence, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "remote": self.remote,
            "branch": self.branch,
            "base_commit": self.base_commit,
            "commits": [item.to_dict() for item in self.commits],
        }

    @classmethod
    def from_dict(cls, value: object) -> RepositoryReceipt:
        data = require_object(value, "repository")
        commits = data.get("commits", ())
        if isinstance(commits, str) or not isinstance(commits, Sequence):
            raise ContractValidationError("repository.commits must be an array")
        return cls(
            remote=None if data.get("remote") is None else require_string(data["remote"], "remote"),
            branch=None if data.get("branch") is None else require_string(data["branch"], "branch"),
            base_commit=(
                None
                if data.get("base_commit") is None
                else require_string(data["base_commit"], "base_commit")
            ),
            commits=tuple(CommitEvidence.from_dict(item) for item in commits),
        )


@dataclass(frozen=True)
class UsageRecord:
    input_tokens: int | None = None
    output_tokens: int | None = None
    source: str = "unknown"

    def __post_init__(self) -> None:
        require_string(self.source, "usage.source")
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise ContractValidationError(f"{name} must be a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, value: object) -> UsageRecord:
        data = require_object(value, "usage")
        return cls(
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            source=str(data.get("source", "unknown")),
        )


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
    termination: ReceiptTermination | None = None
    predecessor_execution_id: ExecutionId | None = None
    seat_type: SeatId | None = None
    seat_instance: SeatInstanceId | None = None
    sovereign_session: SovereignSessionId | None = None
    provider: str | None = None
    provider_session: ProviderSessionId | None = None
    worker_backend: str | None = None
    capability_manifest_ref: str | None = None
    completion_signal_seen: bool | None = None
    structured_result_valid: bool | None = None
    technical_verification_valid: bool | None = None
    dataflow_integrity_valid: bool | None = None
    repository: RepositoryReceipt | None = None
    verification: tuple[VerificationCommand, ...] = ()
    usage: UsageRecord | None = None
    artifact_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
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
            "termination",
            "predecessor_execution_id",
            "seat_type",
            "seat_instance",
            "sovereign_session",
            "provider",
            "provider_session",
            "worker_backend",
            "capability_manifest_ref",
            "completion_signal_seen",
            "structured_result_valid",
            "technical_verification_valid",
            "dataflow_integrity_valid",
            "repository",
            "verification",
            "usage",
            "artifact_refs",
            "warnings",
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
        termination = self.termination
        if termination is None:
            termination = default_termination(self.status)
            object.__setattr__(self, "termination", termination)
        elif not isinstance(termination, ReceiptTermination):
            object.__setattr__(self, "termination", ReceiptTermination(termination))
            termination = self.termination
        if termination is not None:
            projected = status_for_termination(termination, self.status)
            if self.status is ReceiptStatus.RUNNING:
                raise ContractValidationError("a running receipt cannot have a termination")
            if (
                self.status is ReceiptStatus.SUCCEEDED
                and termination is not ReceiptTermination.COMPLETED
            ):
                raise ContractValidationError("succeeded receipts terminate as completed")
            if self.status is not projected and self.status is not ReceiptStatus.RUNNING:
                if termination is ReceiptTermination.COMPLETED:
                    raise ContractValidationError("completed termination requires succeeded status")
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
        if self.predecessor_execution_id is not None and not isinstance(
            self.predecessor_execution_id, ExecutionId
        ):
            raise ContractValidationError("predecessor_execution_id must be ExecutionId or null")
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
        object.__setattr__(self, "verification", tuple(self.verification))
        if any(not isinstance(item, VerificationCommand) for item in self.verification):
            raise ContractValidationError("verification entries must be VerificationCommand")
        object.__setattr__(self, "artifact_refs", tuple(self.artifact_refs))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        if any(
            not isinstance(item, str) or not item for item in (*self.artifact_refs, *self.warnings)
        ):
            raise ContractValidationError("artifact_refs and warnings must be non-empty strings")
        if self.repository is not None and not isinstance(self.repository, RepositoryReceipt):
            raise ContractValidationError("repository must be RepositoryReceipt or null")
        if self.usage is not None and not isinstance(self.usage, UsageRecord):
            raise ContractValidationError("usage must be UsageRecord or null")
        worker = self.worker_backend
        if worker is not None:
            require_string(worker, "worker_backend")
        if (
            worker in {"bare", "none"}
            and "bare" not in self.warnings
            and "none" not in self.warnings
        ):
            object.__setattr__(self, "warnings", (*self.warnings, f"worker_backend={worker}"))
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
        termination: ReceiptTermination | None = None,
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
            termination=termination,
            predecessor_execution_id=self.predecessor_execution_id,
            seat_type=self.seat_type,
            seat_instance=self.seat_instance,
            sovereign_session=self.sovereign_session,
            provider=self.provider,
            provider_session=self.provider_session,
            worker_backend=self.worker_backend,
            capability_manifest_ref=self.capability_manifest_ref,
            repository=self.repository,
            verification=self.verification,
            usage=self.usage,
            artifact_refs=self.artifact_refs,
            warnings=self.warnings,
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
            "termination": None if self.termination is None else self.termination.value,
            "predecessor_execution_id": (
                None
                if self.predecessor_execution_id is None
                else str(self.predecessor_execution_id)
            ),
            "seat_type": None if self.seat_type is None else str(self.seat_type),
            "seat_instance": None if self.seat_instance is None else str(self.seat_instance),
            "sovereign_session": (
                None if self.sovereign_session is None else str(self.sovereign_session)
            ),
            "provider": self.provider,
            "provider_session": (
                None if self.provider_session is None else str(self.provider_session)
            ),
            "worker_backend": self.worker_backend,
            "capability_manifest_ref": self.capability_manifest_ref,
            "completion_signal_seen": self.completion_signal_seen,
            "structured_result_valid": self.structured_result_valid,
            "technical_verification_valid": self.technical_verification_valid,
            "dataflow_integrity_valid": self.dataflow_integrity_valid,
            "repository": None if self.repository is None else self.repository.to_dict(),
            "verification": [item.to_dict() for item in self.verification],
            "usage": None if self.usage is None else self.usage.to_dict(),
            "artifact_refs": list(self.artifact_refs),
            "warnings": list(self.warnings),
        }
        return merge_unknown(known, self.unknown_fields)

    @classmethod
    def from_dict(cls, value: object) -> ExecutionReceipt:
        data = require_object(value, "execution_receipt")
        known, unknown = split_known(data, cls._KNOWN)
        required = cls._KNOWN - {
            "result",
            "error",
            "evidence_sha256",
            "supersedes_sha256",
            "termination",
            "predecessor_execution_id",
            "seat_type",
            "seat_instance",
            "sovereign_session",
            "provider",
            "provider_session",
            "worker_backend",
            "capability_manifest_ref",
            "completion_signal_seen",
            "structured_result_valid",
            "technical_verification_valid",
            "dataflow_integrity_valid",
            "repository",
            "verification",
            "usage",
            "artifact_refs",
            "warnings",
        }
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
        termination_raw = known.get("termination")
        repository_raw = known.get("repository")
        usage_raw = known.get("usage")
        verification_raw = known.get("verification", ())
        if isinstance(verification_raw, str) or not isinstance(verification_raw, Sequence):
            raise ContractValidationError("verification must be an array")
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
            termination=(
                None if termination_raw is None else ReceiptTermination(str(termination_raw))
            ),
            predecessor_execution_id=_optional_execution_id(known.get("predecessor_execution_id")),
            seat_type=_optional_id(known.get("seat_type"), SeatId),
            seat_instance=_optional_id(known.get("seat_instance"), SeatInstanceId),
            sovereign_session=_optional_id(known.get("sovereign_session"), SovereignSessionId),
            provider=known.get("provider"),
            provider_session=_optional_id(known.get("provider_session"), ProviderSessionId),
            worker_backend=known.get("worker_backend"),
            capability_manifest_ref=known.get("capability_manifest_ref"),
            completion_signal_seen=known.get("completion_signal_seen"),
            structured_result_valid=known.get("structured_result_valid"),
            technical_verification_valid=known.get("technical_verification_valid"),
            dataflow_integrity_valid=known.get("dataflow_integrity_valid"),
            repository=None
            if repository_raw is None
            else RepositoryReceipt.from_dict(repository_raw),
            verification=tuple(VerificationCommand.from_dict(item) for item in verification_raw),
            usage=None if usage_raw is None else UsageRecord.from_dict(usage_raw),
            artifact_refs=tuple(known.get("artifact_refs") or ()),
            warnings=tuple(known.get("warnings") or ()),
            unknown_fields=unknown,
        )


def _optional_execution_id(value: object) -> ExecutionId | None:
    if value is None:
        return None
    return ExecutionId(require_string(value, "predecessor_execution_id"))


def _optional_id(value: object, cls: type[Any]) -> Any:
    if value is None:
        return None
    return cls(require_string(value, cls.__name__))


def lifecycle_complete(receipt: ExecutionReceipt) -> bool:
    """Lifecycle predicate; deliberately independent of evidence validity."""
    return receipt.is_terminal


def evidence_verified(receipt: ExecutionReceipt) -> bool:
    """Evidence predicate; deliberately independent of lifecycle outcome."""
    return receipt.verify_evidence()


__all__ = [
    "CommitEvidence",
    "ExecutionReceipt",
    "ReceiptStatus",
    "ReceiptTermination",
    "RepositoryReceipt",
    "UsageRecord",
    "VerificationCommand",
    "evidence_verified",
    "lifecycle_complete",
]
