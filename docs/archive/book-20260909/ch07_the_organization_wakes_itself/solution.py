"""Chapter 7: the organization wakes itself.

Runs the SAME sale-crosses-reorder scenario Chapter 0 dispatched entirely by
hand -- but this time no `create_sow`, `ready_sow`, or `assign` call appears
anywhere in this file. The SOW and assignment come from a real wake-gate
decision, through the genuine production Pulse mechanism
(`sovereign_agent.pulse.run_pulse_once`), exactly as
`reference_organizations.store.demo.run_pulse_simulated` already proves in
this project's own test suite. Imports the production package throughout --
the pulse.work_created event and the pulse_origins/pulse_wake_decisions rows
this chapter's own README quotes are read back from the ledger after this
function runs, never asserted without having actually produced them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reference_organizations.store import below_reorder, record_sale, seed
from reference_organizations.store.pulse_gate import store_wake_gate
from sovereign_agent.models import AssignmentState
from sovereign_agent.organization import Organization
from sovereign_agent.pulse import run_pulse_once

SKU = "SKU-TEA"


def the_organization_wakes_itself(root: Path) -> dict[str, Any]:
    org = Organization.init(root)
    seed(org.db)
    outcome = org.create_outcome(
        title="Keep the tea jar stocked",
        desired_state=(
            "On-hand tea is at or above the reorder point, the purchase is "
            "reconciled, and the replenishment is on the ledger."
        ),
        checks=[
            "inventory_at_or_above_reorder_point",
            "cash_reconciles",
            "replenishment_event_exists",
        ],
        owner="principal-human",
        subject=SKU,
    )
    org.activate(outcome.id, "master-course")

    # Nobody calls create_sow, ready_sow, or assign. A sale is committed --
    # exactly the kind of thing that already happens without anyone thinking
    # about governance -- and it crosses the reorder point.
    signal = record_sale(org.db, SKU, 2, 400)
    if not below_reorder(org.db):
        raise RuntimeError("fixture sale should cross the reorder point")

    events_before = _event_kinds(org)

    # THIS is the organization waking itself: one deterministic pass reads
    # the durable signal, asks the Store's own wake gate whether it
    # qualifies, and -- because it does -- creates governed work atomically
    # and runs it through the exact same run_assignment path a human-
    # dispatched assignment uses.
    report = run_pulse_once(org, store_wake_gate)

    created = [item for item in report.items if item.signal_id == signal.id]
    if not created or created[0].status != "created" or created[0].sow_id is None:
        raise RuntimeError(f"pulse should have created work for {signal.id}: {report.items}")
    sow_id = created[0].sow_id
    assignment_id = created[0].assignment_id
    assert assignment_id is not None
    assignment = org._assignment(assignment_id)  # noqa: SLF001 -- teaching exercise, same module family
    if assignment.state != AssignmentState.COMPLETED:
        raise RuntimeError(f"pulse-created assignment did not complete: {assignment.state}")

    events_after = _event_kinds(org)
    new_event_kinds = sorted(set(events_after) - set(events_before))

    origin = org.pulse_origin_for_sow(sow_id)
    assert origin is not None

    wake_decision_row = org.db.connection.execute(
        "SELECT source_signal_id, source_event_id FROM pulse_wake_decisions WHERE id = ?",
        (origin.wake_decision_id,),
    ).fetchone()

    return {
        "sale_committed_no_human_dispatch": {
            "signal_id": signal.id,
            "below_reorder_after_sale": True,
        },
        "pulse_report": {
            "status": created[0].status,
            "sow_id": sow_id,
            "assignment_id": assignment_id,
            "assignment_state": assignment.state.value,
        },
        "durable_pulse_event": {
            "new_event_kinds_this_run": new_event_kinds,
            "pulse_work_created_present": "pulse.work_created" in new_event_kinds,
        },
        "structured_origin": {
            "origin_kind": origin.origin_kind,
            "sow_id": origin.sow_id,
            "assignment_id": origin.assignment_id,
            "wake_decision_id": origin.wake_decision_id,
            "pulse_event_id": origin.pulse_event_id,
            "wake_decision_source_signal_id": wake_decision_row["source_signal_id"],
            "wake_decision_source_event_id": wake_decision_row["source_event_id"],
            "wake_decision_traces_back_to_this_signal": wake_decision_row["source_signal_id"]
            == signal.id,
        },
    }


def _event_kinds(org: Organization) -> list[str]:
    return [
        str(row["kind"]) for row in org.db.connection.execute("SELECT kind FROM events").fetchall()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(the_organization_wakes_itself(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
