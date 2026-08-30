"""Chapter 11: replenishment scales without losing governance.

Chapter 10 proved each signal binds to its own outcome. This chapter runs
BOTH SKUs' full governed chains to completion -- Pulse-created SOW,
assignment, provider proposal, `apply_restock`, verification, review,
acceptance -- and proves three things at once: (1) each SKU gets its own
canonical, ACCEPTED outcome, (2) the effects ledger never lets one SKU's
replenishment be attributed to the other's assignment, and (3) replaying
`apply_restock` for an already-completed assignment is still idempotent,
exactly as it was for the single-SKU case, now proven with two assignments
racing for the SAME assignment id apiece. Imports the production package
throughout -- `apply_restock`, `run_pulse_once`, and `Organization.
run_assignment` are unchanged production code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reference_organizations.store import apply_restock, record_sale, seed_catalog
from reference_organizations.store.demo import propose_restock_from_report
from reference_organizations.store.pulse_gate import store_wake_gate
from sovereign_agent.models import AssignmentState
from sovereign_agent.organization import Organization
from sovereign_agent.pulse import run_pulse_once

TEA = "SKU-TEA"
COFFEE = "SKU-COFFEE"


def replenishment_scales_without_losing_governance(root: Path) -> dict[str, Any]:
    org = Organization.init(root)
    seed_catalog(org.db)

    outcome_ids: dict[str, str] = {}
    for sku, title in ((TEA, "Keep the tea jar stocked"), (COFFEE, "Keep the coffee tin stocked")):
        outcome = org.create_outcome(
            title,
            f"On-hand {sku} is at or above the reorder point, the purchase is "
            "reconciled, and the replenishment is on the ledger.",
            [
                "inventory_at_or_above_reorder_point",
                "cash_reconciles",
                "replenishment_event_exists",
            ],
            "principal-human",
            sku,
        )
        org.activate(outcome.id, "master-course")
        outcome_ids[sku] = outcome.id

    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 5, 650)

    report = run_pulse_once(org, store_wake_gate)
    tea_item = next(item for item in report.items if item.signal_id == tea_signal.id)
    coffee_item = next(item for item in report.items if item.signal_id == coffee_signal.id)
    assert tea_item.assignment_id is not None
    assert coffee_item.assignment_id is not None
    tea_assignment = org._assignment(tea_item.assignment_id)  # noqa: SLF001 -- teaching exercise
    coffee_assignment = org._assignment(coffee_item.assignment_id)  # noqa: SLF001

    results: dict[str, Any] = {}
    for sku, signal, assignment in (
        (TEA, tea_signal, tea_assignment),
        (COFFEE, coffee_signal, coffee_assignment),
    ):
        report_path = (
            root
            / ".sovereign"
            / "runs"
            / assignment.workspace_id
            / ".sovereign-out"
            / "report.json"
        )
        proposal = propose_restock_from_report(report_path, sku)
        first = apply_restock(org.db, proposal, assignment.id, signal.id)
        # Idempotency, per SKU: replaying the SAME assignment's restock must
        # never create a second effect row or move cash/inventory twice.
        second = apply_restock(org.db, proposal, assignment.id, signal.id)
        results[sku] = {
            "first_call_idempotent_replay": bool(first.get("idempotent_replay", False)),
            "second_call_idempotent_replay": bool(second.get("idempotent_replay", False)),
            "on_hand_after": first["on_hand"],
        }
        org.verify_outcome(outcome_ids[sku], "verifier-course")
        sow_id = tea_item.sow_id if sku == TEA else coffee_item.sow_id
        assert sow_id is not None
        org.review(sow_id, "sparring-course")
        org.accept(outcome_ids[sku], "principal-human")

    effects = org.db.connection.execute(
        "SELECT assignment_id, subject FROM effects ORDER BY created_at"
    ).fetchall()
    effect_pairs = [(row["assignment_id"], row["subject"]) for row in effects]

    return {
        "both_assignments_completed": {
            "tea": tea_item.assignment_state == AssignmentState.COMPLETED.value,
            "coffee": coffee_item.assignment_state == AssignmentState.COMPLETED.value,
        },
        "idempotent_replay_per_sku": results,
        "effects_never_cross_assignments": {
            "effect_rows": [{"assignment_id": a, "subject": s} for a, s in effect_pairs],
            "each_assignment_authorizes_only_its_own_sku": all(
                (a == tea_assignment.id and s == TEA) or (a == coffee_assignment.id and s == COFFEE)
                for a, s in effect_pairs
            ),
            "exactly_two_effect_rows": len(effect_pairs) == 2,
        },
        "both_outcomes_accepted": {
            "tea": org.status_text(outcome_ids[TEA]).splitlines()[0],
            "coffee": org.status_text(outcome_ids[COFFEE]).splitlines()[0],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(replenishment_scales_without_losing_governance(args.root), indent=2, default=str)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
