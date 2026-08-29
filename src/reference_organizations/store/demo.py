"""Deterministic simulated store demos: manual replenishment, and Pulse.

`run_simulated`'s loop, end to end -- unchanged since Unit 5, describing
accurately what was true when it was written:

    sale -> inventory falls below the reorder point -> durable signal
      -> governed outcome and SOW -> assignment to an operator actor
      -> provider PROPOSES a bounded restock -> Python VALIDATES it
      -> inventory + cash + event commit atomically
      -> deterministic checks execute -> check-bound evidence is stored
      -> an independent reviewer reviews -> the Principal accepts

Nothing in THAT loop wakes itself up. A human runs it -- `create_sow`,
`ready_sow`, and `assign` are called directly, by this function, not by
anything reading a signal.

Unit 9, additive: `run_pulse_simulated` below runs the SAME loop through the
genuine `sovereign_agent.pulse` mechanism instead -- the SOW and assignment
are created by `Organization.create_pulse_work` after a real wake-gate
decision, never by a manual `create_sow`/`ready_sow`/`assign` call from this
module. Both demos share every step after that (the same Scripted provider,
the same `apply_restock` boundary, the same verify/review/accept chain).
"""

from __future__ import annotations

import json
from pathlib import Path

from reference_organizations.store import (
    RestockProposal,
    apply_restock,
    below_reorder,
    record_sale,
    seed,
)
from reference_organizations.store.pulse_gate import store_wake_gate
from sovereign_agent.errors import Refusal
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization
from sovereign_agent.pulse import run_pulse_once

SKU = "SKU-TEA"


def propose_restock_from_report(report_path: Path, sku: str) -> RestockProposal:
    """Read the provider's proposal. Refuse anything malformed.

    The provider is an intelligence, not an authority. It may ask for a quantity.
    It does not get to name the price, pick the SKU's cost, or decide which
    checks will judge its work. A malformed report is a refusal, never a guess.
    """
    if not report_path.is_file():
        raise Refusal(
            "The provider wrote no report.",
            "A silent actor has not done the work.",
            str(report_path),
            "Re-run the assignment.",
        )
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise Refusal(
            f"The provider report is not valid JSON: {error}.",
            "A malformed report fails closed. It never becomes a guessed success.",
            str(report_path),
            "Fix the provider or re-run the assignment.",
        ) from error
    requested = payload.get("proposed_restock_units")
    if not isinstance(requested, int):
        raise Refusal(
            f"The provider proposed {requested!r} units, which is not a whole number.",
            "The effect boundary only accepts a proposal it can check.",
            str(report_path),
            "Have the provider propose an integer quantity.",
        )
    return RestockProposal(sku=sku, quantity=requested)


def run_simulated(root: Path) -> str:
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

    signal = record_sale(org.db, SKU, 2, 400)
    if not below_reorder(org.db):
        raise RuntimeError("fixture sale should cross the reorder point")

    sow = org.create_sow(
        outcome.id,
        scope=f"Manually dispatched replenishment after signal {signal.id}",
        role=Role.OPERATOR,
        actor_id="master-course",
        # This SOW must actually restock. Declaring it means acceptance checks
        # that THIS execution did it, rather than that the shelf happens to be
        # full because of work done last week.
        required_effect_kind="replenishment",
    )
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    assignment = org.run_assignment(assignment.id)

    # The provider proposed. Python decides.
    report_path = (
        root / ".sovereign" / "runs" / assignment.workspace_id / ".sovereign-out" / "report.json"
    )
    proposal = propose_restock_from_report(report_path, SKU)
    apply_restock(org.db, proposal, assignment.id, signal.id)

    # Verify FIRST: a reviewer with no evidence in front of them is rubber-stamping.
    org.verify_outcome(outcome.id, "verifier-course")
    org.review(sow.id, "sparring-course")
    org.accept(outcome.id, "principal-human")
    return org.status_text(outcome.id)


def run_pulse_simulated(root: Path) -> str:
    """The same slice as `run_simulated`, but PROACTIVE: no `create_sow`,
    `ready_sow`, or `assign` call anywhere in this function. The SOW and
    assignment come from a real wake-gate decision, through the genuine
    production Pulse mechanism, exactly as the governing SOW's reference
    Store proof requires (section 7)."""
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

    signal = record_sale(org.db, SKU, 2, 400)
    if not below_reorder(org.db):
        raise RuntimeError("fixture sale should cross the reorder point")

    report = run_pulse_once(org, store_wake_gate)
    created = [item for item in report.items if item.signal_id == signal.id]
    if not created or created[0].status != "created" or created[0].sow_id is None:
        raise RuntimeError(f"pulse should have created work for {signal.id}: {report.items}")
    sow_id = created[0].sow_id
    assignment_id = created[0].assignment_id
    assert assignment_id is not None
    assignment = org._assignment(assignment_id)  # noqa: SLF001 -- demo, same module family
    if assignment.state != AssignmentState.COMPLETED:
        raise RuntimeError(f"pulse-created assignment did not complete: {assignment.state}")

    report_path = (
        root / ".sovereign" / "runs" / assignment.workspace_id / ".sovereign-out" / "report.json"
    )
    proposal = propose_restock_from_report(report_path, SKU)
    apply_restock(org.db, proposal, assignment.id, signal.id)

    org.verify_outcome(outcome.id, "verifier-course")
    org.review(sow_id, "sparring-course")
    org.accept(outcome.id, "principal-human")
    return org.status_text(outcome.id)
