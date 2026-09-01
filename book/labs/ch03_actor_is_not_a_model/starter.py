from __future__ import annotations

from pathlib import Path

from sovereign_agent.models import Actor, Role
from sovereign_agent.providers.base import InvocationRequest, ProviderCapabilities

STUDENT_TODO = True
REQUESTED_ACTION = "accept"


def actor_identity(actor: Actor) -> tuple[str, Role, tuple[str, ...]]:
    """Capture the governed fields that a provider rebind must preserve."""
    return actor.id, actor.role, tuple(actor.authority)


def offline_request(root: Path) -> tuple[InvocationRequest, ProviderCapabilities]:
    """Build a request and deliberately insufficient offline probe result."""
    request = InvocationRequest(workspace=root, output=root / "report.json", prompt="restock")
    capabilities = ProviderCapabilities(available=True, print_mode=True, streaming=False)
    return request, capabilities


def exercise(root: Path) -> dict[str, object]:
    """Rebind a real Actor and gate an invocation with proven capabilities."""
    # TODO(1): Rebind only Actor.provider and compare actor_identity before/after.
    # TODO(2): Prove editing Actor.authority cannot expand ROLE_AUTHORITY.
    # TODO(3): Refuse offline_request until streaming has actually been proven.
    raise NotImplementedError("Use Actor, ROLE_AUTHORITY, and require_proven")
