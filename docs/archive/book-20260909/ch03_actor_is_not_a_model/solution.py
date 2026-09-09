"""Runnable Chapter 3 exercise using the production organization and registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sovereign_agent.errors import Refusal
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization
from sovereign_agent.providers import PROVIDERS


def _assignment(org: Organization, scope: str) -> tuple[str, str]:
    outcome = org.create_outcome(
        "Chapter 3",
        "actor identity survives",
        ["receipt"],
        "principal-human",
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, scope, Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    finished = org.run_assignment(assignment.id)
    workspace = org.root / ".sovereign" / "runs" / assignment.workspace_id
    return finished.state, (workspace / "receipt.json").read_text(encoding="utf-8")


def run_exercise(root: Path, live_provider: str = "claude") -> dict[str, object]:
    org = Organization.init(root)
    actor = org.actor("operator-course")
    identity_before = {
        "id": actor.id,
        "role": actor.role,
        "authority": actor.authority,
    }
    scripted_state, scripted_receipt = _assignment(org, "Write the required offline report.")
    org.rebind_actor(actor.id, live_provider, "principal-human")
    rebound = org.actor(actor.id)
    identity_after = {
        "id": rebound.id,
        "role": rebound.role,
        "authority": rebound.authority,
    }
    try:
        live_state, live_receipt = _assignment(
            org,
            "Inspect README.md if present and write the required report "
            "without expanding authority.",
        )
        live: dict[str, object] = {
            "state": live_state,
            "receipt": json.loads(live_receipt),
        }
    except Refusal as refusal:
        live = {"refused": str(refusal)}
    return {
        "identity_unchanged": identity_before == identity_after,
        "before": identity_before,
        "after": identity_after,
        "scripted": {
            "state": scripted_state,
            "receipt": json.loads(scripted_receipt),
        },
        "live": live,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--provider", choices=tuple(PROVIDERS), default="claude")
    args = parser.parse_args()
    print(json.dumps(run_exercise(args.root, args.provider), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
