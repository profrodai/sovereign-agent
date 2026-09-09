"""Chapter 2: what makes ACCEPTED mean something.

Runs the production governed loop, then attempts to accept several false claims
and records how each one is refused. Imports the production package throughout.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from reference_organizations.store.demo import run_simulated
from sovereign_agent.checks import run_check
from sovereign_agent.errors import Refusal
from sovereign_agent.organization import Organization

SKU = "SKU-TEA"


def _reopen(org: Organization, outcome_id: str) -> None:
    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.state', 'VERIFYING') WHERE id = ?",
        (outcome_id,),
    )
    org.db.connection.commit()


def _attempt(org: Organization, outcome_id: str, accepter: str = "principal-human") -> str:
    _reopen(org, outcome_id)
    try:
        org.accept(outcome_id, accepter)
    except Refusal as refusal:
        return f"refused: {str(refusal).splitlines()[0]}"
    return "ACCEPTED (this would be a bug)"


def explore_governance(root: Path) -> dict[str, Any]:
    run_simulated(root)
    org = Organization(root)
    outcome_id = str(org.db.connection.execute("SELECT id FROM outcomes").fetchone()["id"])
    outcome = org._outcome(outcome_id)  # noqa: SLF001

    checks_now = {
        check_id: run_check(org.db, check_id, SKU).detail for check_id in outcome.acceptance_checks
    }
    evidence = [
        {
            "check_id": row["check_id"],
            "success": bool(row["success"]),
            "bound_to_outcome": str(row["outcome_id"]) == outcome_id,
        }
        for row in org.db.connection.execute(
            "SELECT check_id, success, outcome_id FROM evidence WHERE outcome_id = ?",
            (outcome_id,),
        )
    ]

    refusals: dict[str, str] = {}

    # The operator who did the work cannot accept it.
    refusals["operator_self_approval"] = _attempt(org, outcome_id, "operator-course")

    # Evidence cannot be rewritten at all: proof-bearing tables are append-only
    # at the database boundary, so the tamper is refused before acceptance is
    # ever consulted. That is a stronger guarantee than "acceptance notices".
    for statement in (
        "UPDATE evidence SET success = 0",
        "DELETE FROM evidence WHERE check_id = 'cash_reconciles'",
        "UPDATE reviews SET decision = 'changes_requested'",
    ):
        try:
            org.db.connection.execute(statement)
            org.db.connection.commit()
            refusals[statement.split()[1].lower()] = "ALLOWED (this would be a bug)"
        except sqlite3.IntegrityError as error:
            org.db.connection.rollback()
            refusals[f"tamper_{statement.split()[1].lower()}"] = f"refused: {error}"

    # The world moves after verification: the claim itself becomes false.
    org.db.connection.execute("UPDATE inventory SET on_hand = 0 WHERE sku = ?", (SKU,))
    org.db.connection.commit()
    refusals["outcome_no_longer_true"] = _attempt(org, outcome_id)

    return {
        "outcome": outcome.title,
        "declared_checks": outcome.acceptance_checks,
        "checks_when_accepted": checks_now,
        "evidence": evidence,
        "performers_derived_from_ledger": sorted(org.performers_for(outcome_id)),
        "refusals": refusals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(explore_governance(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
