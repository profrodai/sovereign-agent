"""The governed request passed across an execution boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from ._core import (
    ContractValidationError,
    FrozenDict,
    format_datetime,
    freeze_json,
    merge_unknown,
    parse_datetime,
    require_object,
    require_string,
    split_known,
    thaw_json,
)
from .capabilities import CapabilityManifest
from .ids import (
    ExecutionId,
    InvocationId,
    ProviderSessionId,
    RepositoryId,
    SeatInstanceId,
    SovereignSessionId,
    WorkerHandleId,
)


@dataclass(frozen=True)
class GovernedExecutionRequest:
    """Complete immutable input to a governed provider invocation."""

    SCHEMA_VERSION: ClassVar[str] = "1.0"

    seat_instance_id: SeatInstanceId
    sovereign_session_id: SovereignSessionId
    execution_id: ExecutionId
    invocation_id: InvocationId
    repository_id: RepositoryId
    operation: str
    input: FrozenDict
    governance: FrozenDict
    capability_manifest: CapabilityManifest
    requested_at: datetime
    provider_session_id: ProviderSessionId | None = None
    worker_handle_id: WorkerHandleId | None = None
    schema_version: str = SCHEMA_VERSION
    unknown_fields: FrozenDict = field(default_factory=FrozenDict, repr=False)

    _KNOWN: ClassVar[frozenset[str]] = frozenset(
        {
            "schema_version",
            "seat_instance_id",
            "sovereign_session_id",
            "execution_id",
            "invocation_id",
            "provider_session_id",
            "worker_handle_id",
            "repository_id",
            "operation",
            "input",
            "governance",
            "capability_manifest",
            "requested_at",
        }
    )

    def __post_init__(self) -> None:
        id_types = (
            ("seat_instance_id", self.seat_instance_id, SeatInstanceId),
            ("sovereign_session_id", self.sovereign_session_id, SovereignSessionId),
            ("execution_id", self.execution_id, ExecutionId),
            ("invocation_id", self.invocation_id, InvocationId),
            ("repository_id", self.repository_id, RepositoryId),
        )
        for name, value, expected in id_types:
            if not isinstance(value, expected):
                raise ContractValidationError(f"{name} must be {expected.__name__}")
        if self.provider_session_id is not None and not isinstance(
            self.provider_session_id, ProviderSessionId
        ):
            raise ContractValidationError("provider_session_id must be ProviderSessionId or null")
        if self.worker_handle_id is not None and not isinstance(
            self.worker_handle_id, WorkerHandleId
        ):
            raise ContractValidationError("worker_handle_id must be WorkerHandleId or null")
        require_string(self.operation, "operation")
        if self.schema_version != self.SCHEMA_VERSION:
            raise ContractValidationError(
                f"schema_version must be {self.SCHEMA_VERSION!r}, got {self.schema_version!r}"
            )
        format_datetime(self.requested_at, "requested_at")
        if not isinstance(self.capability_manifest, CapabilityManifest):
            raise ContractValidationError("capability_manifest must be CapabilityManifest")
        object.__setattr__(self, "input", freeze_json(require_object(self.input, "input")))
        object.__setattr__(
            self, "governance", freeze_json(require_object(self.governance, "governance"))
        )
        object.__setattr__(
            self,
            "unknown_fields",
            freeze_json(
                require_object(self.unknown_fields, "unknown_fields"), path="unknown_fields"
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        known: dict[str, Any] = {
            "schema_version": self.schema_version,
            "seat_instance_id": str(self.seat_instance_id),
            "sovereign_session_id": str(self.sovereign_session_id),
            "execution_id": str(self.execution_id),
            "invocation_id": str(self.invocation_id),
            "provider_session_id": (
                str(self.provider_session_id) if self.provider_session_id is not None else None
            ),
            "worker_handle_id": (
                str(self.worker_handle_id) if self.worker_handle_id is not None else None
            ),
            "repository_id": str(self.repository_id),
            "operation": self.operation,
            "input": thaw_json(self.input),
            "governance": thaw_json(self.governance),
            "capability_manifest": self.capability_manifest.to_dict(),
            "requested_at": format_datetime(self.requested_at, "requested_at"),
        }
        return merge_unknown(known, self.unknown_fields)

    @classmethod
    def from_dict(cls, value: object) -> GovernedExecutionRequest:
        data = require_object(value, "governed_execution_request")
        known, unknown = split_known(data, cls._KNOWN)
        required = cls._KNOWN - {"provider_session_id", "worker_handle_id"}
        missing = sorted(required - known.keys())
        if missing:
            raise ContractValidationError(f"missing required fields: {', '.join(missing)}")

        provider = known.get("provider_session_id")
        worker = known.get("worker_handle_id")
        return cls(
            schema_version=require_string(known["schema_version"], "schema_version"),
            seat_instance_id=SeatInstanceId(
                require_string(known["seat_instance_id"], "seat_instance_id")
            ),
            sovereign_session_id=SovereignSessionId(
                require_string(known["sovereign_session_id"], "sovereign_session_id")
            ),
            execution_id=ExecutionId(require_string(known["execution_id"], "execution_id")),
            invocation_id=InvocationId(require_string(known["invocation_id"], "invocation_id")),
            provider_session_id=(
                ProviderSessionId(require_string(provider, "provider_session_id"))
                if provider is not None
                else None
            ),
            worker_handle_id=(
                WorkerHandleId(require_string(worker, "worker_handle_id"))
                if worker is not None
                else None
            ),
            repository_id=RepositoryId(require_string(known["repository_id"], "repository_id")),
            operation=require_string(known["operation"], "operation"),
            input=freeze_json(require_object(known["input"], "input")),
            governance=freeze_json(require_object(known["governance"], "governance")),
            capability_manifest=CapabilityManifest.from_dict(known["capability_manifest"]),
            requested_at=parse_datetime(known["requested_at"], "requested_at"),
            unknown_fields=unknown,
        )


__all__ = ["GovernedExecutionRequest"]
