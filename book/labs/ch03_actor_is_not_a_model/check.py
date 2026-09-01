from __future__ import annotations

from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    result = target_module.exercise(root)
    assert result["actor_id"] == "operator-course"
    assert result["provider_after_rebind"] == "claude"
    assert result["identity_role_authority_preserved"] is True
    assert result["self_grant_blocked"] is True
    assert result["operator_role_actions"] == ["read", "report", "run_checks", "write_workspace"]
    assert result["unproven_streaming_refusal"] == "capability_refusal"
    assert result["proven_streaming_allowed"] is True
    return {
        "actor_identity_survived_rebind": True,
        "authority_came_from_role_table": True,
        "unproven_capability_refused": True,
        "proven_capability_allowed": True,
    }
