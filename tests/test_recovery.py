"""Governed failure must be recoverable.

If `changes_requested` is terminal, the book teaches Andrea that the recovery
from a refusal is to delete the organization and start over — the opposite of
what Chapter 2 says refusal is for. Reported on PR #24 round 2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reference_organizations.store import RestockProposal, apply_restock, record_sale, seed
from sovereign_agent.errors import Refusal
from sovereign_agent.models import Role, SowState
from sovereign_agent.organization import Organization


def failing_outcome(tmp_path: Path) -> tuple[Organization, str, str, str]:
    """A store where the work has run but the shelf was never restocked."""
    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        ["inventory_at_or_above_reorder_point"],
        "principal-human",
        "SKU-TEA",
    )
    org.activate(outcome.id, "master-course")
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    sow = org.create_sow(outcome.id, "replenish", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    assignment = org.run_assignment(assignment.id)
    return org, outcome.id, sow.id, signal.id


def test_red_repair_reassign_verify_review_accept(tmp_path: Path) -> None:
    """The whole recovery cycle, end to end."""
    org, outcome_id, sow_id, signal_id = failing_outcome(tmp_path)

    org.verify_outcome(outcome_id, "verifier-course")
    first = org.review(sow_id, "sparring-course")
    assert first.decision == "changes_requested"
    assert org._sow(sow_id).state == SowState.CHANGES_REQUESTED  # noqa: SLF001

    # Recovery is a NEW assignment: repaired work is new work, and the ledger
    # should say so rather than quietly reusing the failed execution.
    second = org.assign(sow_id, "operator-course", "master-course")
    second = org.run_assignment(second.id)
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), second.id, signal_id)

    org.verify_outcome(outcome_id, "verifier-course")
    again = org.review(sow_id, "sparring-course")
    assert again.decision == "accepted"
    assert again.verification_id != first.verification_id

    org.accept(outcome_id, "principal-human")
    row = org.db.connection.execute(
        "SELECT on_hand, reorder_point FROM inventory WHERE sku = 'SKU-TEA'"
    ).fetchone()
    assert int(row["on_hand"]) >= int(row["reorder_point"])


def test_failed_evidence_does_not_poison_later_reviews(tmp_path: Path) -> None:
    """Review reads the CURRENT batch only.

    Scanning every historical evidence row meant one failed check made every
    later review fail forever, however thoroughly the world was repaired.
    """
    org, outcome_id, sow_id, signal_id = failing_outcome(tmp_path)
    org.verify_outcome(outcome_id, "verifier-course")
    assert org.review(sow_id, "sparring-course").decision == "changes_requested"

    second = org.run_assignment(org.assign(sow_id, "operator-course", "master-course").id)
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), second.id, signal_id)
    org.verify_outcome(outcome_id, "verifier-course")

    failed_rows = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM evidence WHERE success = 0"
    ).fetchone()
    assert int(failed_rows["c"]) > 0, "the failed evidence must still be on the record"
    assert org.review(sow_id, "sparring-course").decision == "accepted"


def test_acceptance_is_refused_while_changes_are_outstanding(tmp_path: Path) -> None:
    org, outcome_id, sow_id, _signal_id = failing_outcome(tmp_path)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")
    with pytest.raises(Refusal):
        org.accept(outcome_id, "principal-human")


def test_history_is_preserved_across_recovery(tmp_path: Path) -> None:
    """Recovery supersedes; it never deletes."""
    org, outcome_id, sow_id, signal_id = failing_outcome(tmp_path)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")
    second = org.run_assignment(org.assign(sow_id, "operator-course", "master-course").id)
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), second.id, signal_id)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")

    verifications = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM verifications WHERE outcome_id = ?", (outcome_id,)
    ).fetchone()
    reviews = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE outcome_id = ?", (outcome_id,)
    ).fetchone()
    assert int(verifications["c"]) == 2
    assert int(reviews["c"]) == 2, "the changes_requested review must remain on the record"
