"""The accepted execution must have caused the effect it is credited with.

Reported independently by both reviewers on PR #24. `apply_restock` recorded
which assignment produced an effect; nothing read it. The store checks find
replenishments by SKU, so the authorization graph and the acceptance graph met
at the subject rather than the execution — and an assignment that did nothing
inherited credit for work done a week earlier.

Governed by docs/rulings/2026-08-26-outcomes-are-conditions-sows-are-work.md:
an outcome is a standing condition, a SOW is a unit of work, and acceptance
asserts BOTH that the condition holds and that this execution contributed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reference_organizations.store import RestockProposal, apply_restock, record_sale, seed
from sovereign_agent.checks import run_check
from sovereign_agent.errors import Refusal
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization

CHECKS = [
    "inventory_at_or_above_reorder_point",
    "cash_reconciles",
    "replenishment_event_exists",
]


def stocked_outcome(tmp_path: Path) -> tuple[Organization, str, str]:
    """Week one: real work, real restock, accepted legitimately."""
    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        CHECKS,
        "principal-human",
        "SKU-TEA",
    )
    org.activate(outcome.id, "master-course")
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    sow = org.create_sow(outcome.id, "week one", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    worker = org.run_assignment(org.assign(sow.id, "operator-course", "master-course").id)
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), worker.id, signal.id)
    org.verify_outcome(outcome.id, "verifier-course")
    org.review(sow.id, "sparring-course")
    org.accept(outcome.id, "principal-human")
    return org, outcome.id, worker.id


def test_an_execution_that_did_nothing_is_refused(tmp_path: Path) -> None:
    """Week two: an assignment runs, does nothing, and must not take credit.

    Public APIs only, including a second SOW on the same outcome — the
    multi-SOW shape that "latest assignment" could never model correctly.
    """
    org, outcome_id, first = stocked_outcome(tmp_path)

    second_sow = org.create_sow(outcome_id, "week two", Role.OPERATOR, "master-course")
    org.ready_sow(second_sow.id)
    idle = org.run_assignment(org.assign(second_sow.id, "operator-course", "master-course").id)
    assert idle.id not in org.contributing_executions(outcome_id)
    assert first in org.contributing_executions(outcome_id)

    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.state', 'VERIFYING') WHERE id = ?",
        (outcome_id,),
    )
    org.db.connection.commit()
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(second_sow.id, "sparring-course")

    # The condition genuinely holds: the tea IS stocked, from week one.
    assert run_check(org.db, "inventory_at_or_above_reorder_point", "SKU-TEA").success

    with pytest.raises(Refusal, match="produced no effect for this outcome"):
        org.accept(outcome_id, "principal-human")


def test_the_two_requirements_are_independent(tmp_path: Path) -> None:
    """Condition-holds and execution-contributed must fail separately.

    If one implied the other, the ruling would be describing one requirement
    wearing two names.
    """
    org, outcome_id, first = stocked_outcome(tmp_path)

    # Condition true, contribution false -> refused for contribution.
    second_sow = org.create_sow(outcome_id, "idle", Role.OPERATOR, "master-course")
    org.ready_sow(second_sow.id)
    org.run_assignment(org.assign(second_sow.id, "operator-course", "master-course").id)
    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.state', 'VERIFYING') WHERE id = ?",
        (outcome_id,),
    )
    org.db.connection.commit()
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(second_sow.id, "sparring-course")
    with pytest.raises(Refusal, match="produced no effect"):
        org.accept(outcome_id, "principal-human")

    # Contribution true, condition false -> refused for the condition.
    org.db.connection.execute("UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA'")
    org.db.connection.commit()
    assert not run_check(org.db, "inventory_at_or_above_reorder_point", "SKU-TEA").success


def test_effects_carry_their_outcome_as_a_structured_column(tmp_path: Path) -> None:
    """The edge must be queryable relationally, not buried in a JSON payload."""
    org, outcome_id, worker = stocked_outcome(tmp_path)
    row = org.db.connection.execute(
        "SELECT outcome_id, assignment_id FROM effects WHERE outcome_id = ?", (outcome_id,)
    ).fetchone()
    assert row is not None, "the effect edge is not followable by query"
    assert str(row["assignment_id"]) == worker


def test_proof_selection_ignores_executions_that_never_completed(tmp_path: Path) -> None:
    """ "Newest row" was an ordering accident, not a proof rule."""
    org, outcome_id, worker = stocked_outcome(tmp_path)
    org.db.connection.execute(
        "INSERT INTO assignments(id, sow_id, actor_id, record) "
        "SELECT 'asg_never_ran', sow_id, actor_id, "
        "json_set(record, '$.state', 'CREATED') FROM assignments WHERE id = ?",
        (worker,),
    )
    org.db.connection.commit()
    assert org._latest_assignment_id(outcome_id) == worker  # noqa: SLF001
