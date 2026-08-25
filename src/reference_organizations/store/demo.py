"""Deterministic simulated store demo: manual replenishment, no Pulse.

The loop this runs, end to end:

    sale -> inventory falls below the reorder point -> durable signal
      -> governed outcome and SOW -> assignment to an operator actor
      -> provider PROPOSES a bounded restock -> Python VALIDATES it
      -> inventory + cash + event commit atomically
      -> deterministic checks execute -> check-bound evidence is stored
      -> an independent reviewer reviews -> the Principal accepts

Nothing here wakes itself up. A human runs it. Proactive waking is Pulse, and
Pulse arrives in Unit 9 — this demo does not pretend to have it.
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
from sovereign_agent.errors import Refusal
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization

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

    org.review(sow.id, "sparring-course", "operator-course")
    org.verify_outcome(outcome.id, "verifier-course")
    org.accept(outcome.id, "principal-human")
    return org.status_text(outcome.id)
