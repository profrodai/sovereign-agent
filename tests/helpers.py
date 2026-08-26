"""Shared helpers for building a governed organization in tests.

Effects now require a real, completed, authorized assignment, so tests can no
longer invent an `assignment_id` string. That is the point of the fix: a test
that could fabricate authority was testing a system that let anyone fabricate it.
"""

from __future__ import annotations

from pathlib import Path

from reference_organizations.store import seed
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization

STORE_CHECKS = [
    "inventory_at_or_above_reorder_point",
    "cash_reconciles",
    "replenishment_event_exists",
]


def governed_assignment(
    root: Path, subject: str = "SKU-TEA", checks: list[str] | None = None
) -> tuple[Organization, str, str, str]:
    """Seed a store and run one assignment to completion.

    Returns (organization, outcome_id, sow_id, assignment_id) where the
    assignment genuinely completed and carries a successful receipt — the only
    kind that can authorize an effect.
    """
    org = Organization.init(root)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        checks if checks is not None else STORE_CHECKS,
        "principal-human",
        subject,
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "replenish", Role.OPERATOR, "master-course", "replenishment")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    assignment = org.run_assignment(assignment.id)
    return org, outcome.id, sow.id, assignment.id
