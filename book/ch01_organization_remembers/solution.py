"""Chapter 1: where the organization keeps its memory.

Imports the production package. Nothing here reimplements storage — the point of
the exercise is to observe the real ledger, not a teaching replica of one.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import reference_organizations.store as store
from reference_organizations.store import RestockProposal, apply_restock, record_sale, seed
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization


def observe_memory(root: Path) -> dict[str, Any]:
    """Show operational state, then prove a failed restock leaves no trace."""
    # An effect needs a real, completed, authorized assignment behind it: the
    # organization refuses to change the world on the say-so of an id nobody
    # issued. Chapter 2 explains why; here we just need a legitimate one.
    org = Organization.init(root)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        ["inventory_at_or_above_reorder_point"],
        "principal-human",
        "SKU-TEA",
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "replenish", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.run_assignment(org.assign(sow.id, "operator-course", "master-course").id)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)

    def snapshot() -> dict[str, int]:
        inventory = org.db.connection.execute(
            "SELECT on_hand FROM inventory WHERE sku = 'SKU-TEA'"
        ).fetchone()
        purchases = org.db.connection.execute(
            "SELECT COUNT(*) AS c FROM cash_entries WHERE amount_cents < 0"
        ).fetchone()
        events = org.db.connection.execute(
            "SELECT COUNT(*) AS c FROM events WHERE kind = 'replenishment.committed'"
        ).fetchone()
        return {
            "on_hand": int(inventory["on_hand"]),
            "purchase_entries": int(purchases["c"]),
            "replenishment_events": int(events["c"]),
        }

    before = snapshot()
    rollback_error = ""
    with patch.object(store, "append_event", side_effect=RuntimeError("injected power cut")):
        try:
            apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment.id, signal.id)
        except RuntimeError as error:
            rollback_error = str(error)
    after_rollback = snapshot()

    committed = apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment.id, signal.id)
    after_success = snapshot()

    append_only: dict[str, str] = {}
    for label, statement in (
        ("update", "UPDATE events SET kind = 'TAMPERED'"),
        ("delete", "DELETE FROM events"),
    ):
        try:
            org.db.connection.execute(statement)
            append_only[label] = "ALLOWED (this would be a bug)"
        except Exception as error:  # noqa: BLE001 - we are demonstrating the refusal
            org.db.connection.rollback()
            append_only[label] = f"refused: {error}"

    return {
        "before_failed_restock": before,
        "rollback_error": rollback_error,
        "after_rollback": after_rollback,
        "nothing_survived_rollback": before == after_rollback,
        "after_successful_restock": after_success,
        "cash_balance_cents": store.cash_balance_cents(org.db),
        "purchase_total_cents": committed["total_cost_cents"],
        "append_only_enforcement": append_only,
        "schema_versions": sorted(org.db.applied_versions()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(observe_memory(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
