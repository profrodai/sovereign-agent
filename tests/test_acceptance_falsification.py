"""Acceptance must REFUSE a false claim.

Every test here is a way of lying to the organization. Each one must fail to
work. A test suite that only demonstrates the happy path cannot tell you whether
`ACCEPTED` means anything — the defect this unit exists to fix passed 59 such
tests.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from reference_organizations.store import RestockProposal, apply_restock, record_sale, seed
from reference_organizations.store.demo import propose_restock_from_report, run_simulated
from sovereign_agent.errors import Refusal
from sovereign_agent.organization import Organization


def accepted_org(tmp_path: Path) -> tuple[Organization, str]:
    """A truthfully accepted store, then reopened for tampering."""
    run_simulated(tmp_path)
    org = Organization(tmp_path)
    outcome_id = str(org.db.connection.execute("SELECT id FROM outcomes").fetchone()["id"])
    return org, outcome_id


def reopen_for_acceptance(org: Organization, outcome_id: str) -> None:
    """Put the outcome back into VERIFYING so accept() can be re-attempted."""
    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.state', 'VERIFYING') WHERE id = ?",
        (outcome_id,),
    )
    org.db.connection.commit()


def test_refuses_when_inventory_is_below_reorder_point(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("UPDATE inventory SET on_hand = 1 WHERE sku = 'SKU-TEA'")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="failing at acceptance time"):
        org.accept(outcome_id, "principal-human")


def test_refuses_when_evidence_reports_failure(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("UPDATE evidence SET success = 0")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="reports failure"):
        org.accept(outcome_id, "principal-human")


def test_refuses_when_a_required_check_has_no_evidence(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("DELETE FROM evidence WHERE check_id = 'cash_reconciles'")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="No evidence for declared check"):
        org.accept(outcome_id, "principal-human")


def test_refuses_stale_evidence_even_when_checks_still_pass(tmp_path: Path) -> None:
    """The subtle one: state moved AFTER verification, but the claim is still true.

    Inventory goes UP, so every check still passes. The evidence nevertheless
    describes a world that no longer exists, and acceptance says so. An event
    counter could not detect this, because a plain UPDATE appends no event.
    """
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("UPDATE inventory SET on_hand = 20 WHERE sku = 'SKU-TEA'")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="stale"):
        org.accept(outcome_id, "principal-human")


def test_refuses_evidence_bound_to_another_execution(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("UPDATE evidence SET assignment_id = 'asg_SOME_OTHER_RUN'")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="not bound to this execution"):
        org.accept(outcome_id, "principal-human")


def test_refuses_evidence_belonging_to_another_outcome(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    other = org.create_outcome("other", "d", ["cash_reconciles"], "principal-human")
    org.db.connection.execute(
        "UPDATE evidence SET outcome_id = ? WHERE check_id = 'cash_reconciles'", (other.id,)
    )
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="No evidence for declared check"):
        org.accept(outcome_id, "principal-human")


def test_fabricated_evidence_row_is_refused_by_the_database(tmp_path: Path) -> None:
    """A made-up evidence id cannot even be inserted: the FK refuses it."""
    org, _ = accepted_org(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):
        org.db.connection.execute(
            "INSERT INTO evidence(id, assignment_id, record, outcome_id, check_id, "
            "success, state_digest) VALUES "
            "('evd_fake', 'asg', '{}', 'out_GHOST', 'c', 1, 'd')"
        )
        org.db.connection.commit()


def test_operator_cannot_accept_its_own_work(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal):
        org.accept(outcome_id, "operator-course")


def test_performer_is_derived_from_the_ledger_not_supplied(tmp_path: Path) -> None:
    """accept() takes no performer argument, so no caller can name a stand-in."""
    import inspect

    signature = inspect.signature(Organization.accept)
    assert "performer_id" not in signature.parameters
    org, outcome_id = accepted_org(tmp_path)
    assert "operator-course" in org.performers_for(outcome_id)


def test_refuses_an_outcome_with_no_sows(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    outcome = org.create_outcome("t", "d", ["cash_reconciles"], "principal-human")
    org.activate(outcome.id, "master-course")
    with pytest.raises(Refusal, match="No SOW exists"):
        org.accept(outcome.id, "principal-human")


def test_malformed_provider_report_is_refused(tmp_path: Path) -> None:
    bad = tmp_path / "report.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(Refusal, match="not valid JSON"):
        propose_restock_from_report(bad, "SKU-TEA")


def test_absent_provider_report_is_refused(tmp_path: Path) -> None:
    with pytest.raises(Refusal, match="wrote no report"):
        propose_restock_from_report(tmp_path / "missing.json", "SKU-TEA")


def test_non_integer_proposal_is_refused(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text('{"proposed_restock_units": "lots"}', encoding="utf-8")
    with pytest.raises(Refusal, match="not a whole number"):
        propose_restock_from_report(report, "SKU-TEA")


def test_unbounded_or_invalid_restock_is_refused(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    for quantity, expected in [(0, "not positive"), (-5, "not positive"), (999, "exceeds")]:
        with pytest.raises(Refusal, match=expected):
            apply_restock(org.db, RestockProposal("SKU-TEA", quantity), "asg_x")
    with pytest.raises(Refusal, match="Unknown SKU"):
        apply_restock(org.db, RestockProposal("SKU-GHOST", 1), "asg_x")


def test_restock_beyond_available_cash_is_refused(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    org.db.connection.execute("DELETE FROM cash_entries")
    org.db.connection.commit()
    with pytest.raises(Refusal, match="cash is available"):
        apply_restock(org.db, RestockProposal("SKU-TEA", 10), "asg_x")


def test_replenishment_is_idempotent_per_assignment(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    first = apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_once", signal.id)
    second = apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_once", signal.id)
    assert second.get("idempotent_replay") is True
    assert first["on_hand"] == second["on_hand"]
    row = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'replenishment.committed'"
    ).fetchone()
    assert row["c"] == 1, "a replayed assignment must not order stock twice"


def test_acceptance_cannot_be_pointed_at_a_different_subject(tmp_path: Path) -> None:
    """The outcome owns its subject; the caller does not get to choose it.

    Found by the Master while attacking its own fix. An earlier version took the
    SKU as a parameter to verify/accept. With a second, well-stocked product in
    the catalogue you could accept the tea outcome by pointing acceptance at the
    decoy while the tea shelf sat at zero — the same defect this unit exists to
    fix, reintroduced one level up.
    """
    import json

    org, outcome_id = accepted_org(tmp_path)

    org.db.connection.execute(
        "INSERT OR REPLACE INTO products(sku, record) VALUES ('SKU-DECOY', ?)",
        (json.dumps({"sku": "SKU-DECOY", "name": "d", "unit_cost_cents": 1, "price_cents": 2}),),
    )
    org.db.connection.execute(
        "INSERT OR REPLACE INTO inventory(sku, on_hand, reserved, reorder_point, record) "
        "VALUES ('SKU-DECOY', 1, 0, 1, '{}')"
    )
    org.db.connection.commit()
    apply_restock(org.db, RestockProposal("SKU-DECOY", 5), "asg_decoy")

    org.db.connection.execute("UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA'")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)

    assert org._outcome(outcome_id).subject == "SKU-TEA"  # noqa: SLF001
    with pytest.raises(Refusal, match="inventory_at_or_above_reorder_point"):
        org.accept(outcome_id, "principal-human")


def test_verify_and_accept_take_no_subject_argument() -> None:
    """A caller-supplied subject is a caller-supplied world. Keep it out."""
    import inspect

    for method in (Organization.verify_outcome, Organization.accept):
        assert "subject" not in inspect.signature(method).parameters
