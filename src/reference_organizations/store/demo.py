"""Deterministic simulated store demo: manual replenishment, no Pulse."""

from __future__ import annotations

from pathlib import Path

from reference_organizations.store import below_reorder, cash_balance_cents, record_sale, seed
from sovereign_agent.evidence import record_check
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization


def run_simulated(root: Path) -> str:
    org = Organization.init(root)
    seed(org.db)
    outcome = org.create_outcome(
        title="Keep the tea jar stocked",
        desired_state="On-hand tea stays at or above the reorder point after a sale.",
        checks=["inventory_non_negative", "cash_reconciles", "replenishment_sow_accepted"],
        owner="principal-human",
    )
    org.activate(outcome.id, "master-course")
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
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
    evidence = record_check(
        assignment.id,
        "inventory_non_negative",
        ["sqlite", "inventory"],
        0 if cash_balance_cents(org.db) >= 0 else 1,
    )
    with org.db.transaction():
        org.db.connection.execute(
            "INSERT INTO evidence(id, assignment_id, record) VALUES (?, ?, ?)",
            (evidence.id, assignment.id, evidence.model_dump_json()),
        )
    org.review(sow.id, "sparring-course", "operator-course")
    org.verify_outcome(outcome.id, "verifier-course")
    org.accept(outcome.id, "principal-human", "operator-course", [evidence.id])
    return org.status_text(outcome.id)
