from __future__ import annotations

from pathlib import Path

from sovereign_agent.errors import Refusal
from sovereign_agent.models import Actor, Role
from sovereign_agent.policy import ROLE_AUTHORITY, require_authority
from sovereign_agent.providers.base import InvocationRequest, ProviderCapabilities, require_proven

STUDENT_TODO = False


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    actor = Actor(
        id="operator-course",
        role=Role.OPERATOR,
        provider="scripted",
        authority=["read", "write_workspace", "run_checks", "report"],
    )
    before = (actor.id, actor.role.value, tuple(actor.authority))
    actor.provider = "claude"
    after = (actor.id, actor.role.value, tuple(actor.authority))

    actor.authority.append("accept")
    self_grant_blocked = False
    try:
        require_authority(actor.role, "accept")
    except Refusal:
        self_grant_blocked = True

    request = InvocationRequest(workspace=root, output=root / "report.json", prompt="restock")
    unproven = ProviderCapabilities(available=True, print_mode=True, streaming=False)
    capability_category = ""
    try:
        require_proven(
            unproven,
            request,
            missing="offline-provider",
            inspect="probe evidence",
            next_command="choose a proven adapter",
        )
    except Refusal as refusal:
        capability_category = refusal.category
    proven = ProviderCapabilities(available=True, print_mode=True, streaming=True)
    require_proven(
        proven,
        request,
        missing="offline-provider",
        inspect="probe evidence",
        next_command="choose a proven adapter",
    )
    return {
        "actor_id": actor.id,
        "provider_after_rebind": actor.provider,
        "identity_role_authority_preserved": before == after,
        "self_grant_blocked": self_grant_blocked,
        "operator_role_actions": sorted(ROLE_AUTHORITY[Role.OPERATOR]),
        "unproven_streaming_refusal": capability_category,
        "proven_streaming_allowed": True,
    }
