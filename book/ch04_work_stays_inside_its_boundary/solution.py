"""Chapter 4: the workspace boundary is detectable, and reclaim is a policy.

Runs a real assignment through the production organization, then exercises
the same workspace-lifecycle machinery `Organization.run_assignment` already
calls on every invocation: `safe_join` (traversal refusal), the before/after
`snapshot_boundary`/`diff_boundary` pair (a violation outside the workspace is
detected), and `reclaim_workspace` (temporary_directory reclaims scratch
space, persistent does not). Imports the production package throughout --
nothing here reimplements the boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sovereign_agent.errors import Refusal
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization
from sovereign_agent.workspace import (
    diff_boundary,
    reclaim_workspace,
    safe_join,
    snapshot_boundary,
)


def _run_one_assignment(org: Organization, scope: str) -> tuple[str, Path]:
    outcome = org.create_outcome(
        "Chapter 4",
        "work stays inside its declared workspace",
        ["receipt"],
        "principal-human",
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, scope, Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    finished = org.run_assignment(assignment.id)
    workspace = org.root / ".sovereign" / "runs" / finished.workspace_id
    return finished.state, workspace


def explore_workspace_lifecycle(root: Path) -> dict[str, Any]:
    # Resolved once, up front: safe_join itself resolves both root and the
    # joined candidate before comparing them, and on macOS /tmp is a symlink
    # into /private/tmp -- an unresolved root here would make relative_to
    # below fail even on a call safe_join itself accepted correctly.
    root = root.resolve()
    org = Organization.init(root)

    # 1. safe_join refuses traversal, accepts a legitimate nested path.
    workspace_root = root / "sample-workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "nested").mkdir()
    (workspace_root / "nested" / "artifact.txt").write_text("real", encoding="utf-8")

    safe_join_results: dict[str, str] = {}
    try:
        resolved = safe_join(workspace_root, "nested/artifact.txt")
        safe_join_results["legitimate_nested"] = f"resolved to {resolved.relative_to(root)}"
    except Refusal as error:
        safe_join_results["legitimate_nested"] = f"WRONGLY REFUSED: {error}"

    for label, candidate in (
        ("traversal", "../../etc/passwd"),
        ("absolute", "/etc/passwd"),
        ("empty", ""),
    ):
        try:
            safe_join(workspace_root, candidate)
            safe_join_results[label] = "ALLOWED (this would be a bug)"
        except Refusal as error:
            safe_join_results[label] = f"refused: {str(error).splitlines()[0]}"

    # 2. The boundary is detectable: a real write outside the workspace, made
    # by code standing in for an unsandboxed provider, trips diff_boundary.
    outside_target = root / "outside-the-workspace.txt"
    before = snapshot_boundary(root, workspace_root)
    outside_target.write_text("a provider with no sandbox wrote here", encoding="utf-8")
    after = snapshot_boundary(root, workspace_root)
    dirty = diff_boundary(before, after)

    before_clean = snapshot_boundary(root, workspace_root)
    (workspace_root / "nested" / "in_bounds.txt").write_text("stayed inside", encoding="utf-8")
    after_clean = snapshot_boundary(root, workspace_root)
    clean = diff_boundary(before_clean, after_clean)

    # 3. workspace_policy actually branches reclaim: temporary_directory
    # clears scratch space (preserving receipt.json and .sovereign-out/);
    # persistent reclaims nothing at all.
    temp_state, temp_workspace = _run_one_assignment(org, "Write the required offline report.")
    (temp_workspace / "provider-raw" / "scratch.log").parent.mkdir(exist_ok=True)
    (temp_workspace / "provider-raw" / "scratch.log").write_text("scratch", encoding="utf-8")
    before_reclaim = sorted(p.name for p in temp_workspace.iterdir())
    reclaimed = reclaim_workspace(temp_workspace, "temporary_directory")
    after_reclaim = sorted(p.name for p in temp_workspace.iterdir())

    org.rebind_actor("operator-course", "scripted", "principal-human")
    persistent_actor = org.actor("operator-course")

    return {
        "safe_join": safe_join_results,
        "boundary_scope": dirty.scope,
        "boundary_violation_detected": {
            "violated": dirty.violated,
            "added": list(dirty.added),
        },
        "boundary_clean_run_not_flagged": {
            "violated": clean.violated,
        },
        "reclaim": {
            "assignment_state": temp_state,
            "before": before_reclaim,
            "after": after_reclaim,
            "reclaimed_something": reclaimed,
            "receipt_preserved": "receipt.json" in after_reclaim,
            "output_dir_preserved": ".sovereign-out" in after_reclaim,
            "scratch_removed": "provider-raw" not in after_reclaim,
        },
        "workspace_policy_default": persistent_actor.workspace_policy,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(explore_workspace_lifecycle(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
