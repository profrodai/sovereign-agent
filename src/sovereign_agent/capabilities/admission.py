"""Admission: grant, worker evidence, and scoped context — not global service presence."""

from __future__ import annotations

from zeo_core.tools import BoundCapability, ToolContext

from sovereign_agent.capabilities.context import ExecutionScope
from sovereign_agent.contracts import EvidenceLevel, RuntimeCapabilityManifest


class AdmissionRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def admit_capability(
    *,
    capability: BoundCapability,
    execution: ExecutionScope,
    worker_manifest: RuntimeCapabilityManifest | None = None,
) -> None:
    canonical = capability.definition.id.canonical()
    allowed = execution.allowed_capabilities
    if allowed and canonical not in allowed:
        raise AdmissionRefused(
            "SA_TOOL_NOT_FOUND",
            f"capability {canonical} is not in the governed allow-list",
        )
    granted = execution.granted_capabilities
    if granted and canonical not in granted:
        raise AdmissionRefused(
            "SA_TOOL_NOT_FOUND",
            f"capability {canonical} is not granted to this execution",
        )
    requirements = capability.definition.requirements
    manifest = worker_manifest or execution.runtime_manifest
    if requirements.network.required and not _evidence_ok(
        manifest, "network", EvidenceLevel.PROBED
    ):
        raise AdmissionRefused(
            "SA_SYS_ISOLATION_UNAVAILABLE",
            "capability requires network that this worker cannot evidence",
        )
    if (requirements.filesystem.read or requirements.filesystem.write) and not _evidence_ok(
        manifest, "filesystem_isolation", EvidenceLevel.DECLARED
    ):
        # Absence of a filesystem_isolation assertion is allowed for session-local
        # capabilities; only fail when the assertion is present and false.
        assertion = manifest.get("filesystem_isolation")
        if assertion is not None and assertion.available is False:
            raise AdmissionRefused(
                "SA_SYS_ISOLATION_UNAVAILABLE",
                "filesystem isolation is asserted unavailable",
            )


def context_is_scoped(ctx: ToolContext) -> bool:
    forbidden = ("credentials", "authority", "governed_request", "approval_state")
    return not any(key in ctx.metadata for key in forbidden)


def _evidence_ok(manifest: RuntimeCapabilityManifest, name: str, minimum: EvidenceLevel) -> bool:
    assertion = manifest.get(name)
    if assertion is None:
        return True
    if assertion.available is False:
        return False
    return assertion.has_evidence(minimum)
