"""Chapter 10: one signal wakes one need.

Chapter 7 proved the wake gate correctly maps a signal to governed work for
ONE SKU. This chapter proves the same gate, given signals from TWO
different SKUs, binds each signal to exactly its own SKU's outcome -- never
the other one's, and never both at once. Two outcomes exist in this
chapter's organization (one per SKU); the wake gate must pick correctly
between them for each signal, using the signal's own `subject_ref`, not
order of arrival or any other coincidence. Imports the production package
throughout -- `store_wake_gate` and `run_pulse_once` are the exact same
functions Chapter 7 already exercised for one SKU.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reference_organizations.store import record_sale, seed_catalog
from reference_organizations.store.pulse_gate import store_wake_gate
from sovereign_agent.organization import Organization
from sovereign_agent.pulse import run_pulse_once

TEA = "SKU-TEA"
COFFEE = "SKU-COFFEE"


def one_signal_wakes_one_need(root: Path) -> dict[str, Any]:
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

    # Cross BOTH SKUs' own reorder points, so both signals genuinely
    # qualify -- neither the tea nor the coffee gate decision is a "no
    # decision" result.
    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 5, 650)

    # The wake gate is called DIRECTLY here, once per signal, before any
    # Pulse pass runs -- so this exercise can show the gate's own decision,
    # not just the pass's aggregate report.
    tea_decision = store_wake_gate(org, tea_signal)
    coffee_decision = store_wake_gate(org, coffee_signal)
    assert tea_decision is not None
    assert coffee_decision is not None

    report = run_pulse_once(org, store_wake_gate)
    tea_item = next(item for item in report.items if item.signal_id == tea_signal.id)
    coffee_item = next(item for item in report.items if item.signal_id == coffee_signal.id)

    return {
        "two_signals_two_outcomes": {
            "tea_signal_id": tea_signal.id,
            "coffee_signal_id": coffee_signal.id,
            "tea_outcome_id": outcome_ids[TEA],
            "coffee_outcome_id": outcome_ids[COFFEE],
        },
        "gate_decisions": {
            "tea_signal_maps_to_tea_outcome": tea_decision.outcome_id == outcome_ids[TEA],
            "coffee_signal_maps_to_coffee_outcome": coffee_decision.outcome_id
            == outcome_ids[COFFEE],
            "tea_decision_outcome_id": tea_decision.outcome_id,
            "coffee_decision_outcome_id": coffee_decision.outcome_id,
            "decisions_never_cross": tea_decision.outcome_id != coffee_decision.outcome_id,
        },
        "pulse_pass_result": {
            "tea_status": tea_item.status,
            "coffee_status": coffee_item.status,
            "tea_sow_id": tea_item.sow_id,
            "coffee_sow_id": coffee_item.sow_id,
            "each_signal_got_its_own_sow": tea_item.sow_id != coffee_item.sow_id,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(one_signal_wakes_one_need(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
