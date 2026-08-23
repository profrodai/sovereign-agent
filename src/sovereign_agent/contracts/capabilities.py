"""Runtime/provider/worker capability *evidence* — not ZeoCore capability definitions.

ZeoCore's ``CapabilityManifest`` describes one reusable callable.
This module describes whether an execution substrate can guarantee a feature.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from ._core import (
    ContractValidationError,
    FrozenDict,
    freeze_json,
    merge_unknown,
    require_object,
    require_string,
    split_known,
    thaw_json,
)


class EvidenceLevel(IntEnum):
    """Ordered evidence strength without conflating evidence and availability."""

    UNKNOWN = 0
    DECLARED = 1
    PROBED = 2
    ENFORCED = 3

    def to_wire(self) -> str:
        return self.name.lower()

    @classmethod
    def from_wire(cls, value: object) -> EvidenceLevel:
        text = require_string(value, "evidence_level")
        try:
            return cls[text.upper()]
        except KeyError as exc:
            allowed = ", ".join(item.to_wire() for item in cls)
            raise ContractValidationError(f"evidence_level must be one of: {allowed}") from exc


@dataclass(frozen=True)
class RuntimeCapabilityAssertion:
    """One runtime/provider/backend feature assertion.

    ``available`` is the assertion; ``evidence_level`` says how strongly that
    assertion is supported. Keeping those fields independent avoids treating
    an unverified declaration as either absent or enforced.
    """

    available: bool | None
    evidence_level: EvidenceLevel = EvidenceLevel.UNKNOWN
    details: FrozenDict = field(default_factory=FrozenDict)
    unknown_fields: FrozenDict = field(default_factory=FrozenDict, repr=False)

    def __post_init__(self) -> None:
        if self.available is not None and not isinstance(self.available, bool):
            raise ContractValidationError("capability.available must be boolean or null")
        if not isinstance(self.evidence_level, EvidenceLevel):
            raise ContractValidationError("capability.evidence_level must be an EvidenceLevel")
        object.__setattr__(
            self,
            "details",
            freeze_json(
                require_object(self.details, "capability.details"), path="capability.details"
            ),
        )
        object.__setattr__(
            self,
            "unknown_fields",
            freeze_json(
                require_object(self.unknown_fields, "capability.unknown_fields"),
                path="capability.unknown_fields",
            ),
        )

    def has_evidence(self, minimum: EvidenceLevel = EvidenceLevel.DECLARED) -> bool:
        return self.evidence_level >= minimum

    def is_available(self) -> bool:
        return self.available is True

    def to_dict(self) -> dict[str, Any]:
        return merge_unknown(
            {
                "available": self.available,
                "evidence_level": self.evidence_level.to_wire(),
                "details": thaw_json(self.details),
            },
            self.unknown_fields,
        )

    @classmethod
    def from_dict(cls, value: object) -> RuntimeCapabilityAssertion:
        data = require_object(value, "capability")
        known, unknown = split_known(data, frozenset({"available", "evidence_level", "details"}))
        if "available" not in known:
            raise ContractValidationError("capability.available is required")
        details = require_object(known.get("details", {}), "capability.details")
        return cls(
            available=known["available"],
            evidence_level=EvidenceLevel.from_wire(known.get("evidence_level", "unknown")),
            details=freeze_json(details),
            unknown_fields=unknown,
        )


@dataclass(frozen=True)
class RuntimeCapabilityManifest:
    """Immutable named runtime capability assertions for one execution."""

    capabilities: FrozenDict
    unknown_fields: FrozenDict = field(default_factory=FrozenDict, repr=False)

    def __post_init__(self) -> None:
        source = require_object(self.capabilities, "capabilities")
        normalized: dict[str, RuntimeCapabilityAssertion] = {}
        for name, value in source.items():
            require_string(name, "capability name")
            normalized[name] = (
                value
                if isinstance(value, RuntimeCapabilityAssertion)
                else RuntimeCapabilityAssertion.from_dict(value)
            )
        object.__setattr__(self, "capabilities", FrozenDict(tuple(normalized.items())))
        object.__setattr__(
            self,
            "unknown_fields",
            freeze_json(
                require_object(self.unknown_fields, "manifest.unknown_fields"),
                path="manifest.unknown_fields",
            ),
        )

    def get(self, name: str) -> RuntimeCapabilityAssertion | None:
        value = self.capabilities.get(name)
        return value if isinstance(value, RuntimeCapabilityAssertion) else None

    def is_available(self, name: str) -> bool:
        capability = self.get(name)
        return capability is not None and capability.is_available()

    def has_evidence(self, name: str, minimum: EvidenceLevel = EvidenceLevel.DECLARED) -> bool:
        capability = self.get(name)
        return capability is not None and capability.has_evidence(minimum)

    def to_dict(self) -> dict[str, Any]:
        capabilities = {
            name: capability.to_dict()
            for name, capability in self.capabilities.items()
            if isinstance(capability, RuntimeCapabilityAssertion)
        }
        known: dict[str, Any] = {"capabilities": capabilities}
        return merge_unknown(known, self.unknown_fields)

    @classmethod
    def from_dict(cls, value: object) -> RuntimeCapabilityManifest:
        data = require_object(value, "capability_manifest")
        known, unknown = split_known(data, frozenset({"capabilities"}))
        if "capabilities" not in known:
            raise ContractValidationError("capability_manifest.capabilities is required")
        capabilities = require_object(known["capabilities"], "capability_manifest.capabilities")
        return cls(
            capabilities=FrozenDict(
                tuple(
                    (name, RuntimeCapabilityAssertion.from_dict(item))
                    for name, item in capabilities.items()
                )
            ),
            unknown_fields=unknown,
        )


@dataclass(frozen=True)
class RuntimeRequirement:
    """Minimum evidence a governed execution demands of one runtime feature."""

    minimum_evidence: EvidenceLevel

    def to_dict(self) -> dict[str, Any]:
        return {"minimum_evidence": self.minimum_evidence.to_wire()}

    @classmethod
    def from_dict(cls, value: object) -> RuntimeRequirement:
        data = require_object(value, "runtime_requirement")
        return cls(
            minimum_evidence=EvidenceLevel.from_wire(data.get("minimum_evidence", "unknown"))
        )


if TYPE_CHECKING:
    Capability = RuntimeCapabilityAssertion
    CapabilityManifest = RuntimeCapabilityManifest


def __getattr__(name: str) -> Any:
    # Deprecated names through v0.5. Same objects so isinstance checks keep working.
    if name == "Capability":
        warnings.warn(
            "Capability is deprecated; use RuntimeCapabilityAssertion",
            DeprecationWarning,
            stacklevel=2,
        )
        return RuntimeCapabilityAssertion
    if name == "CapabilityManifest":
        warnings.warn(
            "CapabilityManifest is deprecated; use RuntimeCapabilityManifest",
            DeprecationWarning,
            stacklevel=2,
        )
        return RuntimeCapabilityManifest
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Capability",
    "CapabilityManifest",
    "EvidenceLevel",
    "RuntimeCapabilityAssertion",
    "RuntimeCapabilityManifest",
    "RuntimeRequirement",
]
