"""The governed request passed across an execution boundary."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
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
    SeatId,
    SeatInstanceId,
    SovereignSessionId,
    WorkerHandleId,
)

_PROTECTED_TRUNK = frozenset({"main", "master", "HEAD", "origin/main", "origin/master"})
_SUPPORTED_EVIDENCE = frozenset(
    {
        "structured_result",
        "verification_commands",
        "commit_sha",
        "remote_containment",
    }
)


class MutationPolicy(StrEnum):
    FORBIDDEN = "forbidden"
    ALLOWED = "allowed"


class SandboxMinimum(StrEnum):
    NONE = "none"
    BARE = "bare"
    PROCESS = "process"
    FILESYSTEM_ISOLATED = "filesystem-isolated"
    NETWORK_RESTRICTED = "network-restricted"


class NetworkPolicy(StrEnum):
    UNKNOWN = "unknown"
    UNRESTRICTED = "unrestricted"
    RESTRICTED = "restricted"
    DENIED = "denied"


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ContractValidationError(f"{name} must be an array of strings")
    items = tuple(require_string(item, f"{name}[{index}]") for index, item in enumerate(value))
    return items


@dataclass(frozen=True)
class ExecutionConstraints:
    """Typed enforcement requested of Sovereign Agent, not organizational wisdom."""

    trunk_mutation: MutationPolicy = MutationPolicy.FORBIDDEN
    self_merge: MutationPolicy = MutationPolicy.FORBIDDEN
    sandbox_minimum: SandboxMinimum = SandboxMinimum.NONE
    network: NetworkPolicy = NetworkPolicy.UNKNOWN
    max_invocations: int = 1
    idle_timeout_seconds: int | None = None
    dirty_worktree: str = "fail"
    filesystem_isolation: bool = False
    network_isolation: bool = False
    preserve_on_failure: bool = True
    structured_output: Any = False
    timeouts: FrozenDict = field(default_factory=FrozenDict)
    delivery_enabled: bool = False
    delivery_remote: str | None = None
    delivery_branch: str | None = None
    unknown_fields: FrozenDict = field(default_factory=FrozenDict, repr=False)

    _KNOWN: ClassVar[frozenset[str]] = frozenset(
        {
            "trunk_mutation",
            "self_merge",
            "sandbox_minimum",
            "network",
            "max_invocations",
            "idle_timeout_seconds",
            "dirty_worktree",
            "filesystem_isolation",
            "network_isolation",
            "preserve_on_failure",
            "structured_output",
            "timeouts",
            "delivery_enabled",
            "delivery_remote",
            "delivery_branch",
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "trunk_mutation", MutationPolicy(self.trunk_mutation))
        object.__setattr__(self, "self_merge", MutationPolicy(self.self_merge))
        object.__setattr__(self, "sandbox_minimum", SandboxMinimum(self.sandbox_minimum))
        object.__setattr__(self, "network", NetworkPolicy(self.network))
        if not isinstance(self.max_invocations, int) or isinstance(self.max_invocations, bool):
            raise ContractValidationError("max_invocations must be an integer")
        if self.max_invocations < 1:
            raise ContractValidationError("max_invocations must be at least 1")
        if self.idle_timeout_seconds is not None:
            if not isinstance(self.idle_timeout_seconds, int) or isinstance(
                self.idle_timeout_seconds, bool
            ):
                raise ContractValidationError("idle_timeout_seconds must be an integer")
            if self.idle_timeout_seconds <= 0:
                raise ContractValidationError("idle_timeout_seconds must be positive")
        if self.dirty_worktree not in {"fail", "allow"}:
            raise ContractValidationError("dirty_worktree must be 'fail' or 'allow'")
        for name in (
            "filesystem_isolation",
            "network_isolation",
            "preserve_on_failure",
            "delivery_enabled",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ContractValidationError(f"{name} must be a boolean")
        object.__setattr__(
            self,
            "timeouts",
            freeze_json(require_object(self.timeouts, "timeouts"), path="timeouts"),
        )
        object.__setattr__(self, "structured_output", freeze_json(self.structured_output))
        for name in ("delivery_remote", "delivery_branch"):
            value = getattr(self, name)
            if value is not None:
                require_string(value, name)
        if (
            self.trunk_mutation is MutationPolicy.ALLOWED
            and self.sandbox_minimum is SandboxMinimum.FILESYSTEM_ISOLATED
        ):
            raise ContractValidationError(
                "trunk mutation cannot be allowed under filesystem-isolated governed execution"
            )
        object.__setattr__(
            self,
            "unknown_fields",
            freeze_json(require_object(self.unknown_fields, "unknown_fields")),
        )

    def to_dict(self) -> dict[str, Any]:
        known: dict[str, Any] = {
            "trunk_mutation": self.trunk_mutation.value,
            "self_merge": self.self_merge.value,
            "sandbox_minimum": self.sandbox_minimum.value,
            "network": self.network.value,
            "max_invocations": self.max_invocations,
            "idle_timeout_seconds": self.idle_timeout_seconds,
            "dirty_worktree": self.dirty_worktree,
            "filesystem_isolation": self.filesystem_isolation,
            "network_isolation": self.network_isolation,
            "preserve_on_failure": self.preserve_on_failure,
            "structured_output": thaw_json(self.structured_output),
            "timeouts": thaw_json(self.timeouts),
            "delivery_enabled": self.delivery_enabled,
            "delivery_remote": self.delivery_remote,
            "delivery_branch": self.delivery_branch,
        }
        return merge_unknown(known, self.unknown_fields)

    @classmethod
    def from_dict(cls, value: object) -> ExecutionConstraints:
        data = require_object(value, "constraints")
        known, unknown = split_known(data, cls._KNOWN)
        return cls(
            trunk_mutation=MutationPolicy(
                require_string(known.get("trunk_mutation", "forbidden"), "trunk_mutation")
            ),
            self_merge=MutationPolicy(
                require_string(known.get("self_merge", "forbidden"), "self_merge")
            ),
            sandbox_minimum=SandboxMinimum(
                require_string(known.get("sandbox_minimum", "none"), "sandbox_minimum")
            ),
            network=NetworkPolicy(require_string(known.get("network", "unknown"), "network")),
            max_invocations=int(known.get("max_invocations", 1)),
            idle_timeout_seconds=known.get("idle_timeout_seconds"),
            dirty_worktree=str(known.get("dirty_worktree", "fail")),
            filesystem_isolation=bool(known.get("filesystem_isolation", False)),
            network_isolation=bool(known.get("network_isolation", False)),
            preserve_on_failure=bool(known.get("preserve_on_failure", True)),
            structured_output=known.get("structured_output", False),
            timeouts=freeze_json(require_object(known.get("timeouts", {}), "timeouts")),
            delivery_enabled=bool(known.get("delivery_enabled", False)),
            delivery_remote=known.get("delivery_remote"),
            delivery_branch=known.get("delivery_branch"),
            unknown_fields=unknown,
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
    capability_manifest: CapabilityManifest
    requested_at: datetime
    conversation_id: str
    seat_type: SeatId
    requested_by: str
    authority_refs: tuple[str, ...]
    work_artifact_refs: tuple[str, ...]
    base_ref: str
    branch: str
    constraints: ExecutionConstraints = field(default_factory=ExecutionConstraints)
    required_evidence: tuple[str, ...] = ()
    acceptance_commands: tuple[tuple[str, ...], ...] = ()
    predecessor_execution_id: ExecutionId | None = None
    provider_session_id: ProviderSessionId | None = None
    worker_handle_id: WorkerHandleId | None = None
    governance: FrozenDict = field(default_factory=FrozenDict)
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
            "conversation_id",
            "seat_type",
            "requested_by",
            "authority_refs",
            "work_artifact_refs",
            "base_ref",
            "branch",
            "constraints",
            "required_evidence",
            "acceptance_commands",
            "predecessor_execution_id",
        }
    )

    def __post_init__(self) -> None:
        id_types = (
            ("seat_instance_id", self.seat_instance_id, SeatInstanceId),
            ("sovereign_session_id", self.sovereign_session_id, SovereignSessionId),
            ("execution_id", self.execution_id, ExecutionId),
            ("invocation_id", self.invocation_id, InvocationId),
            ("repository_id", self.repository_id, RepositoryId),
            ("seat_type", self.seat_type, SeatId),
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
        if self.predecessor_execution_id is not None:
            if not isinstance(self.predecessor_execution_id, ExecutionId):
                raise ContractValidationError(
                    "predecessor_execution_id must be ExecutionId or null"
                )
            if self.predecessor_execution_id == self.execution_id:
                raise ContractValidationError("predecessor_execution_id cannot equal execution_id")
        require_string(self.operation, "operation")
        require_string(self.conversation_id, "conversation_id")
        require_string(self.requested_by, "requested_by")
        require_string(self.base_ref, "base_ref")
        require_string(self.branch, "branch")
        object.__setattr__(
            self, "authority_refs", _string_tuple(self.authority_refs, "authority_refs")
        )
        if not self.authority_refs:
            raise ContractValidationError("authority_refs must not be empty")
        object.__setattr__(
            self, "work_artifact_refs", _string_tuple(self.work_artifact_refs, "work_artifact_refs")
        )
        object.__setattr__(
            self, "required_evidence", _string_tuple(self.required_evidence, "required_evidence")
        )
        unknown_evidence = sorted(set(self.required_evidence) - _SUPPORTED_EVIDENCE)
        if unknown_evidence:
            raise ContractValidationError(
                f"unsupported required_evidence: {', '.join(unknown_evidence)}"
            )
        object.__setattr__(self, "acceptance_commands", _command_tuple(self.acceptance_commands))
        if not isinstance(self.constraints, ExecutionConstraints):
            raise ContractValidationError("constraints must be ExecutionConstraints")
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
        if self.constraints.trunk_mutation is MutationPolicy.FORBIDDEN:
            if _is_protected_trunk(self.branch):
                raise ContractValidationError("direct governed trunk mutation is forbidden")
            if _is_protected_trunk(self.base_ref) and self.branch in _PROTECTED_TRUNK:
                raise ContractValidationError("direct governed trunk mutation is forbidden")
        if self.constraints.self_merge is MutationPolicy.ALLOWED:
            if self.constraints.trunk_mutation is MutationPolicy.FORBIDDEN:
                raise ContractValidationError(
                    "self_merge cannot be allowed while trunk mutation is forbidden"
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
            "predecessor_execution_id": (
                None
                if self.predecessor_execution_id is None
                else str(self.predecessor_execution_id)
            ),
            "repository_id": str(self.repository_id),
            "operation": self.operation,
            "input": thaw_json(self.input),
            "governance": thaw_json(self.governance),
            "capability_manifest": self.capability_manifest.to_dict(),
            "requested_at": format_datetime(self.requested_at, "requested_at"),
            "conversation_id": self.conversation_id,
            "seat_type": str(self.seat_type),
            "requested_by": self.requested_by,
            "authority_refs": list(self.authority_refs),
            "work_artifact_refs": list(self.work_artifact_refs),
            "base_ref": self.base_ref,
            "branch": self.branch,
            "constraints": self.constraints.to_dict(),
            "required_evidence": list(self.required_evidence),
            "acceptance_commands": [list(command) for command in self.acceptance_commands],
        }
        return merge_unknown(known, self.unknown_fields)

    @classmethod
    def from_dict(cls, value: object) -> GovernedExecutionRequest:
        data = require_object(value, "governed_execution_request")
        known, unknown = split_known(data, cls._KNOWN)
        required = cls._KNOWN - {
            "provider_session_id",
            "worker_handle_id",
            "predecessor_execution_id",
            "governance",
            "required_evidence",
            "acceptance_commands",
            "constraints",
        }
        missing = sorted(required - known.keys())
        if missing:
            raise ContractValidationError(f"missing required fields: {', '.join(missing)}")

        provider = known.get("provider_session_id")
        worker = known.get("worker_handle_id")
        predecessor = known.get("predecessor_execution_id")
        constraints_raw = known.get("constraints", {})
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
            predecessor_execution_id=(
                ExecutionId(require_string(predecessor, "predecessor_execution_id"))
                if predecessor is not None
                else None
            ),
            repository_id=RepositoryId(require_string(known["repository_id"], "repository_id")),
            operation=require_string(known["operation"], "operation"),
            input=freeze_json(require_object(known["input"], "input")),
            governance=freeze_json(require_object(known.get("governance", {}), "governance")),
            capability_manifest=CapabilityManifest.from_dict(known["capability_manifest"]),
            requested_at=parse_datetime(known["requested_at"], "requested_at"),
            conversation_id=require_string(known["conversation_id"], "conversation_id"),
            seat_type=SeatId(require_string(known["seat_type"], "seat_type")),
            requested_by=require_string(known["requested_by"], "requested_by"),
            authority_refs=_string_tuple(known["authority_refs"], "authority_refs"),
            work_artifact_refs=_string_tuple(known["work_artifact_refs"], "work_artifact_refs"),
            base_ref=require_string(known["base_ref"], "base_ref"),
            branch=require_string(known["branch"], "branch"),
            constraints=ExecutionConstraints.from_dict(constraints_raw),
            required_evidence=_string_tuple(
                known.get("required_evidence", ()), "required_evidence"
            ),
            acceptance_commands=_command_tuple(known.get("acceptance_commands", ())),
            unknown_fields=unknown,
        )


def _command_tuple(value: object) -> tuple[tuple[str, ...], ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ContractValidationError("acceptance_commands must be an array of argv arrays")
    commands: list[tuple[str, ...]] = []
    for index, item in enumerate(value):
        if isinstance(item, str):
            commands.append((item,))
            continue
        commands.append(_string_tuple(item, f"acceptance_commands[{index}]"))
        if not commands[-1]:
            raise ContractValidationError("acceptance_commands entries must not be empty")
    return tuple(commands)


def _is_protected_trunk(value: str) -> bool:
    name = value.removeprefix("refs/heads/")
    return name in _PROTECTED_TRUNK or name.rsplit("/", 1)[-1] in {"main", "master"}


__all__ = [
    "ExecutionConstraints",
    "GovernedExecutionRequest",
    "MutationPolicy",
    "NetworkPolicy",
    "SandboxMinimum",
]
