"""Provider capabilities and invocation boundary models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sovereign_agent.contracts import (
    Capability,
    CapabilityManifest,
    ContractValidationError,
    EvidenceLevel,
    ExecutionId,
    FrozenDict,
    InvocationId,
    ProviderSessionId,
)
from sovereign_agent.contracts._core import freeze_json, require_object, require_string, thaw_json
from sovereign_agent.session.directory import Session

from .events import ProviderEventType


@dataclass(frozen=True)
class ProviderCapabilities:
    """Typed provider features convertible to the Unit 1 capability contract."""

    tools: bool = False
    usage: bool = False
    provider_session: bool = False
    structured_result: bool = False
    streaming: bool = False
    resume: bool = False
    available: bool = True
    evidence_level: EvidenceLevel = EvidenceLevel.DECLARED

    def to_manifest(self) -> CapabilityManifest:
        values = {
            name: Capability(available=value, evidence_level=self.evidence_level)
            for name, value in (
                ("tools", self.tools),
                ("usage", self.usage),
                ("provider_session", self.provider_session),
                ("structured_result", self.structured_result),
                ("streaming", self.streaming),
                ("resume", self.resume),
                ("available", self.available),
            )
        }
        return CapabilityManifest(capabilities=FrozenDict(tuple(values.items())))

    @classmethod
    def from_manifest(cls, manifest: CapabilityManifest) -> ProviderCapabilities:
        if not isinstance(manifest, CapabilityManifest):
            raise ContractValidationError("manifest must be CapabilityManifest")
        levels = [
            capability.evidence_level
            for capability in manifest.capabilities.values()
            if isinstance(capability, Capability)
        ]
        level = min(levels, default=EvidenceLevel.UNKNOWN)
        return cls(
            tools=manifest.is_available("tools"),
            usage=manifest.is_available("usage"),
            provider_session=manifest.is_available("provider_session"),
            structured_result=manifest.is_available("structured_result"),
            streaming=manifest.is_available("streaming"),
            resume=manifest.is_available("resume"),
            available=(
                True if manifest.get("available") is None else manifest.is_available("available")
            ),
            evidence_level=level,
        )


@dataclass(frozen=True)
class InvocationRequest:
    """Immutable request to one agent provider invocation.

    ``session`` is the local runtime handle. It is intentionally omitted from
    ``to_dict`` because provider wire traffic carries only stable identity and
    JSON input; NativeProvider requires it to preserve v0.2 artifacts.
    """

    execution_id: ExecutionId
    invocation_id: InvocationId
    task: str
    session: Session
    context: FrozenDict = field(default_factory=FrozenDict)
    provider_session_id: ProviderSessionId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise ContractValidationError("execution_id must be ExecutionId")
        if not isinstance(self.invocation_id, InvocationId):
            raise ContractValidationError("invocation_id must be InvocationId")
        require_string(self.task, "task", allow_empty=True)
        if not isinstance(self.session, Session):
            raise ContractValidationError("session must be Session")
        object.__setattr__(self, "context", freeze_json(require_object(self.context, "context")))
        if isinstance(self.provider_session_id, str):
            object.__setattr__(
                self, "provider_session_id", ProviderSessionId(self.provider_session_id)
            )
        if self.provider_session_id is not None and not isinstance(
            self.provider_session_id, ProviderSessionId
        ):
            raise ContractValidationError("provider_session_id must be ProviderSessionId or None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": str(self.execution_id),
            "invocation_id": str(self.invocation_id),
            "task": self.task,
            "context": thaw_json(self.context),
            "provider_session_id": (
                str(self.provider_session_id) if self.provider_session_id is not None else None
            ),
        }


@dataclass(frozen=True)
class InvocationResult:
    """Completed provider result and its exact normalized event sequence."""

    success: bool
    output: FrozenDict
    summary: str
    next_action: str
    events: tuple[ProviderEventType, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise ContractValidationError("success must be boolean")
        object.__setattr__(self, "output", freeze_json(require_object(self.output, "output")))
        require_string(self.summary, "summary", allow_empty=True)
        require_string(self.next_action, "next_action")
        expected = list(range(len(self.events)))
        actual = [event.sequence for event in self.events]
        if actual != expected:
            raise ContractValidationError(
                f"events must have contiguous sequence numbers from zero; got {actual}"
            )


__all__ = ["InvocationRequest", "InvocationResult", "ProviderCapabilities"]
