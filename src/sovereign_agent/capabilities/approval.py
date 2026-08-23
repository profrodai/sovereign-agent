"""Approval disposition evaluated before a mutating capability runs."""

from __future__ import annotations

from enum import StrEnum

from zeo_core.contracts import EffectKind
from zeo_core.tools import BoundCapability

from sovereign_agent.capabilities.context import ExecutionScope

_MUTATING = frozenset(
    {
        EffectKind.WRITE,
        EffectKind.DELETE,
        EffectKind.EXTERNAL_COMMUNICATION,
        EffectKind.FINANCIAL,
        EffectKind.SECURITY_SENSITIVE,
    }
)


class ApprovalDisposition(StrEnum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    PREAPPROVED = "preapproved"
    DENIED = "denied"


class ApprovalPolicy:
    """Sovereign-owned policy. Never encoded in CapabilityResult."""

    def evaluate(
        self,
        capability: BoundCapability,
        scope: ExecutionScope,
    ) -> ApprovalDisposition:
        canonical = capability.definition.id.canonical()
        if canonical in scope.denied_capabilities:
            return ApprovalDisposition.DENIED
        kinds = capability.definition.effects.kinds
        if not (kinds & _MUTATING):
            return ApprovalDisposition.NOT_REQUIRED
        if canonical in scope.preapproved_capabilities:
            return ApprovalDisposition.PREAPPROVED
        if scope.require_approval_for_mutations:
            return ApprovalDisposition.REQUIRED
        return ApprovalDisposition.NOT_REQUIRED
