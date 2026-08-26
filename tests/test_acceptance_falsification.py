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

from .helpers import governed_assignment


def accepted_org(tmp_path: Path) -> tuple[Organization, str]:
    """A truthfully accepted store, then reopened for tampering."""
    run_simulated(tmp_path)
    org = Organization(tmp_path)
    outcome_id = str(org.db.connection.execute("SELECT id FROM outcomes").fetchone()["id"])
    return org, outcome_id


def tamper(org: Organization, statement: str, parameters: tuple = ()) -> None:
    """Force a change the append-only guards refuse, to test acceptance itself.

    Proof tables carry BEFORE UPDATE/DELETE/REPLACE triggers, so a tampered
    ledger is not reachable through the database. These tests still matter:
    acceptance must be independently sound, not merely shielded. Dropping the
    guard for one statement is defence-in-depth testing — it asks "if the
    database were compromised, does acceptance still refuse?"
    """
    table = statement.split()[1] if statement.upper().startswith("UPDATE") else statement.split()[2]
    for guard in ("update", "delete", "replace"):
        org.db.connection.execute(f"DROP TRIGGER IF EXISTS {table}_no_{guard}")
    try:
        org.db.connection.execute(statement, parameters)
        org.db.connection.commit()
    finally:
        from sovereign_agent.database import _append_only_triggers

        for piece in _append_only_triggers(table).split("END;"):
            if piece.strip():
                org.db.connection.execute(piece + "END;")
        org.db.connection.commit()


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
    tamper(org, "UPDATE evidence SET success = 0")
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="reports failure"):
        org.accept(outcome_id, "principal-human")


def test_refuses_when_a_required_check_has_no_evidence(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    # Delete from the FINAL observation, which is the batch acceptance rests on.
    tamper(
        org,
        "DELETE FROM evidence WHERE check_id = 'cash_reconciles' AND verification_id = "
        "(SELECT id FROM verifications WHERE outcome_id = ? AND (sow_id IS NULL OR sow_id = '') "
        "ORDER BY rowid DESC LIMIT 1)",
        (outcome_id,),
    )
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
    """A SOW's batch must be bound to that SOW's own execution.

    The outcome-level batch is deliberately unbound — it is the final
    observation of the world, not a record of one unit of work — so this proves
    the binding where binding is the point.
    """
    org, outcome_id = accepted_org(tmp_path)
    sow_id = org.sows_for(outcome_id)[0].id
    verification = org.verification_for_sow(sow_id)
    assert verification is not None and verification.assignment_id

    tamper(
        org,
        "UPDATE evidence SET assignment_id = 'asg_SOME_OTHER_RUN' WHERE verification_id = ?",
        (verification.id,),
    )
    # The external truth verifier is the gate that walks each SOW's evidence
    # against its execution, so that is where the rebinding is caught.
    import subprocess
    import sys

    org.db.close()
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(repo_root / "scripts" / "verify_store_outcome.py"), str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert result.returncode == 1
    assert "bound elsewhere" in result.stdout, result.stdout


def test_refuses_evidence_belonging_to_another_outcome(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    other = org.create_outcome("other", "d", ["cash_reconciles"], "principal-human")
    tamper(
        org, "UPDATE evidence SET outcome_id = ? WHERE check_id = 'cash_reconciles'", (other.id,)
    )
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="not the evidence supporting acceptance"):
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
    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    for quantity, expected in [(0, "not positive"), (-5, "not positive"), (999, "exceeds")]:
        with pytest.raises(Refusal, match=expected):
            apply_restock(org.db, RestockProposal("SKU-TEA", quantity), assignment_id)
    # A SKU the outcome is not about is refused by the subject gate before the
    # catalog is even consulted -- an earlier and stronger refusal than
    # "Unknown SKU", because the effect is unauthorized regardless of whether
    # the product exists.
    with pytest.raises(Refusal, match="but the outcome is about SKU-TEA"):
        apply_restock(org.db, RestockProposal("SKU-GHOST", 1), assignment_id)


def test_restock_beyond_available_cash_is_refused(tmp_path: Path) -> None:
    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    org.db.connection.execute("DELETE FROM cash_entries")
    org.db.connection.commit()
    with pytest.raises(Refusal, match="cash is available"):
        apply_restock(org.db, RestockProposal("SKU-TEA", 10), assignment_id)


def test_replenishment_is_idempotent_per_assignment(tmp_path: Path) -> None:
    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    first = apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id, signal.id)
    second = apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id, signal.id)
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


def test_an_outcome_with_no_subject_fails_closed(tmp_path: Path) -> None:
    """A subjectless outcome must not pass; an unanswerable question is not a yes."""
    from sovereign_agent.checks import run_check

    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome("no subject", "d", ["cash_reconciles"], "principal-human")
    assert outcome.subject == ""
    for check_id in ("inventory_at_or_above_reorder_point", "cash_reconciles"):
        assert not run_check(org.db, check_id, "").success


def test_refuses_when_the_execution_receipt_failed(tmp_path: Path) -> None:
    """ACCEPTED must depend on the work having succeeded.

    Reported on PR #24: acceptance never inspected receipts, so setting the only
    receipt to status="failed" still produced an accepted outcome.
    """
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("UPDATE receipts SET status = 'failed'")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    # Editing the column alone is caught as a disagreement between the two
    # representations, before the status is even consulted.
    with pytest.raises(Refusal, match="its index says failed"):
        org.accept(outcome_id, "principal-human")


def test_refuses_a_receipt_whose_record_says_failed(tmp_path: Path) -> None:
    """Editing the canonical record alone must also be refused.

    Acceptance previously read only the indexed column, so a record saying
    "failed" still accepted while the external verifier called the same state
    unverifiable: an accepted state already known to be false by another tool.
    """
    import json

    org, outcome_id = accepted_org(tmp_path)
    row = org.db.connection.execute("SELECT id, record FROM receipts").fetchone()
    record = json.loads(row["record"])
    record["status"] = "failed"
    org.db.connection.execute(
        "UPDATE receipts SET record = ? WHERE id = ?", (json.dumps(record), row["id"])
    )
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="says failed, its index says completed"):
        org.accept(outcome_id, "principal-human")


def test_refuses_a_receipt_that_agrees_on_failure(tmp_path: Path) -> None:
    """Both representations saying "failed" is refused on the merits."""
    import json

    org, outcome_id = accepted_org(tmp_path)
    row = org.db.connection.execute("SELECT id, record FROM receipts").fetchone()
    record = json.loads(row["record"])
    record["status"] = "failed"
    org.db.connection.execute(
        "UPDATE receipts SET record = ?, status = 'failed' WHERE id = ?",
        (json.dumps(record), row["id"]),
    )
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="receipt reports status failed"):
        org.accept(outcome_id, "principal-human")


def test_refuses_a_receipt_belonging_to_another_execution(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("UPDATE receipts SET assignment_id = 'asg_OTHER'")
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="No receipt for execution"):
        org.accept(outcome_id, "principal-human")


def test_refuses_when_no_review_record_exists(tmp_path: Path) -> None:
    """A status field that once changed is not a review."""
    org, outcome_id = accepted_org(tmp_path)
    tamper(org, "DELETE FROM reviews")
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="no review of its current verification"):
        org.accept(outcome_id, "principal-human")


def test_refuses_when_the_review_requested_changes(tmp_path: Path) -> None:
    org, outcome_id = accepted_org(tmp_path)
    tamper(org, "UPDATE reviews SET decision = 'changes_requested'")
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="disagrees with its index on decision"):
        org.accept(outcome_id, "principal-human")


def test_the_reviewer_cannot_also_accept(tmp_path: Path) -> None:
    """Review and acceptance are separate acts by separate actors."""
    import json

    org, outcome_id = accepted_org(tmp_path)
    # Edit BOTH representations so they agree; otherwise the disagreement check
    # fires first and this stops testing separation.
    row = org.db.connection.execute("SELECT id, record FROM reviews").fetchone()
    record = json.loads(row["record"])
    record["reviewer_actor_id"] = "principal-human"
    tamper(
        org,
        "UPDATE reviews SET reviewer_actor_id = 'principal-human', record = ? WHERE id = ?",
        (json.dumps(record), row["id"]),
    )
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="reviewed this work and cannot also accept"):
        org.accept(outcome_id, "principal-human")


def test_the_review_record_binds_evidence_and_performers(tmp_path: Path) -> None:
    """A review must record what was read, not merely that it happened."""
    import json

    org, outcome_id = accepted_org(tmp_path)
    row = org.db.connection.execute(
        "SELECT record FROM reviews WHERE outcome_id = ?", (outcome_id,)
    ).fetchone()
    review = json.loads(row["record"])
    assert review["reviewer_actor_id"] == "sparring-course"
    assert review["performer_actor_ids"] == ["operator-course"]
    assert len(review["evidence_refs"]) == 3
    assert review["decision"] == "accepted"
    assert review["state_digest"]


def test_evidence_is_stale_when_events_change_but_inventory_does_not(tmp_path: Path) -> None:
    """The digest must cover what each check READS, not a fixed pair of facts.

    Reported on PR #24: the shared digest hashed only the inventory row and the
    cash total, so appending a replenishment event changed what
    `cash_reconciles` and `replenishment_event_exists` observed while the digest
    stayed identical. This appends an EXACT duplicate, so every check still
    passes -- only the observation changed.
    """
    import json

    from sovereign_agent.events import append_event

    org, outcome_id = accepted_org(tmp_path)
    payload = json.loads(
        org.db.connection.execute(
            "SELECT payload FROM events WHERE kind = 'replenishment.committed'"
        ).fetchone()["payload"]
    )
    with org.db.transaction():
        append_event(org.db, "replenishment.committed", payload)

    from sovereign_agent.checks import run_check

    assert run_check(org.db, "cash_reconciles", "SKU-TEA").success, "precondition: still passes"
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="stale"):
        org.accept(outcome_id, "principal-human")


def test_reserved_stock_is_not_available_stock(tmp_path: Path) -> None:
    """A fully reserved shelf is an empty shelf.

    Raised by Sparring as latent: the check loaded `reserved`, digested it, and
    never consulted it. Nothing writes `reserved` today, so it would have become
    a lie the day reservations landed, in a diff that never touched checks.py.
    """
    from sovereign_agent.checks import run_check

    org = Organization.init(tmp_path)
    seed(org.db)
    org.db.connection.execute(
        "UPDATE inventory SET on_hand = 8, reserved = 8 WHERE sku = 'SKU-TEA'"
    )
    org.db.connection.commit()
    result = run_check(org.db, "inventory_at_or_above_reorder_point", "SKU-TEA")
    assert not result.success, "8 reserved out of 8 on hand leaves nothing available"
    assert result.observed["available"] == 0


def test_retargeting_the_subject_alone_is_refused(tmp_path: Path) -> None:
    """Documented limit, claim A. Kept as a test so the doc cannot drift.

    docs/persistence-boundary.md described a subject-retargeting attack that the
    code had already started refusing, and the description survived as
    present-tense doctrine for two Sparring rounds because nobody re-ran it.
    A threat model that cries wolf teaches the next reader to discount it, so
    each documented claim is pinned by a test.
    """
    org, outcome_id = accepted_org(tmp_path)
    org.db.connection.execute("UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA'")
    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.subject', 'SKU-DECOY') WHERE id = ?",
        (outcome_id,),
    )
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="Checks failing at acceptance time"):
        org.accept(outcome_id, "principal-human")


def _seed_decoy(org: Organization) -> str:
    """Stock a decoy product directly.

    Effects are now bound to an assignment whose outcome names a matching
    subject, so a decoy restock cannot be applied through `apply_restock` under
    a tea outcome -- which is the protection being demonstrated elsewhere. Here
    the decoy stock is written directly, because the point of these tests is
    what ACCEPTANCE does about a retargeted subject, not how the stock arrived.
    """
    import json

    org.db.connection.execute(
        "INSERT OR REPLACE INTO products(sku, record) VALUES ('SKU-DECOY', ?)",
        (json.dumps({"sku": "SKU-DECOY", "name": "d", "unit_cost_cents": 1, "price_cents": 2}),),
    )
    org.db.connection.execute(
        "INSERT OR REPLACE INTO inventory(sku, on_hand, reserved, reorder_point, record) "
        "VALUES ('SKU-DECOY', 9, 0, 1, '{}')"
    )
    assignment_id = str(
        org.db.connection.execute("SELECT id FROM assignments LIMIT 1").fetchone()["id"]
    )
    payload = json.dumps(
        {
            "sku": "SKU-DECOY",
            "qty": 5,
            "unit_cost_cents": 1,
            "total_cost_cents": 5,
            "on_hand": 9,
            "cash_id": "cash_decoy",
            "assignment_id": assignment_id,
        }
    )
    org.db.connection.execute(
        "INSERT INTO cash_entries(id, amount_cents, record) VALUES ('cash_decoy', -5, ?)",
        (
            json.dumps(
                {
                    "reason": "purchase",
                    "sku": "SKU-DECOY",
                    "qty": 5,
                    "unit_cost_cents": 1,
                    "assignment_id": assignment_id,
                }
            ),
        ),
    )
    org.db.connection.execute(
        "INSERT INTO events(id, kind, payload, created_at) "
        "VALUES ('evt_decoy', 'replenishment.committed', ?, '2026-01-01T00:00:00Z')",
        (payload,),
    )
    org.db.connection.commit()
    return assignment_id


def test_evidence_about_one_subject_is_not_evidence_about_another(tmp_path: Path) -> None:
    """Documented limit, claim B: a stocked decoy still cannot reuse tea's evidence."""
    org, outcome_id = accepted_org(tmp_path)
    _seed_decoy(org)
    org.db.connection.execute("UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA'")
    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.subject', 'SKU-DECOY') WHERE id = ?",
        (outcome_id,),
    )
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    with pytest.raises(Refusal, match="stale"):
        org.accept(outcome_id, "principal-human")


def test_the_documented_residual_limit_is_real(tmp_path: Path) -> None:
    """Documented limit, claim C — asserts the limit EXISTS, not that it is safe.

    Retarget plus re-verification produces internally consistent evidence and
    accepts, while the real subject sits below its reorder point. No digest of a
    check's own reads can detect the QUESTION changing underneath it. Closing it
    needs tamper-evident governance rows, which is out of scope for Unit 6.5.

    If the limit is ever closed, `accept()` raises and this test ERRORS rather
    than failing its assert — the guard fires either way, and either outcome
    means the documentation must be re-derived rather than left describing a
    threat that no longer exists. (Precision noted by Sparring.)
    """
    org, outcome_id = accepted_org(tmp_path)
    _seed_decoy(org)
    org.db.connection.execute("UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA'")
    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.subject', 'SKU-DECOY') WHERE id = ?",
        (outcome_id,),
    )
    tamper(org, "DELETE FROM evidence WHERE outcome_id = ?", (outcome_id,))
    org.db.connection.commit()
    reopen_for_acceptance(org, outcome_id)
    org.verify_outcome(outcome_id, "verifier-course")
    sow_id = org.sows_for(outcome_id)[0].id
    org.db.connection.execute(
        "UPDATE sows SET record = json_set(record, '$.state', 'REVIEW') WHERE id = ?", (sow_id,)
    )
    org.db.connection.commit()
    org.review(sow_id, "sparring-course")
    org.verify_outcome_condition(outcome_id, "verifier-course")
    org.accept(outcome_id, "principal-human")

    row = org.db.connection.execute(
        "SELECT on_hand, reorder_point FROM inventory WHERE sku = 'SKU-TEA'"
    ).fetchone()
    assert int(row["on_hand"]) < int(row["reorder_point"]), (
        "the residual limit documented in docs/persistence-boundary.md no longer "
        "reproduces; re-derive the document against current behaviour"
    )


def test_an_effect_cannot_name_a_fabricated_assignment(tmp_path: Path) -> None:
    """The completed assignment must be the one that caused the effect.

    Reported on PR #24 round 2: `apply_restock` took any string as its
    assignment_id, so the ledger could show that SOME assignment completed and
    that SOME replenishment happened while nothing tied them together. Two true
    facts arranged so their conjunction implies something false.
    """
    org, _outcome_id, _sow_id, _assignment_id = governed_assignment(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    with pytest.raises(Refusal, match="not in the ledger"):
        apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_FAKE", signal.id)


def test_an_effect_requires_a_completed_assignment(tmp_path: Path) -> None:
    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    org.db.connection.execute(
        "UPDATE assignments SET record = json_set(record, '$.state', 'RUNNING') WHERE id = ?",
        (assignment_id,),
    )
    org.db.connection.commit()
    with pytest.raises(Refusal, match="not COMPLETED"):
        apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id)


def test_an_effect_requires_a_successful_receipt(tmp_path: Path) -> None:
    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    org.db.connection.execute("UPDATE receipts SET status = 'failed'")
    org.db.connection.commit()
    with pytest.raises(Refusal, match="receipt for"):
        apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id)


def test_an_effect_must_move_the_outcomes_subject(tmp_path: Path) -> None:
    """An effect on another product does not deliver this outcome."""
    import json

    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    org.db.connection.execute(
        "INSERT OR REPLACE INTO products(sku, record) VALUES ('SKU-B', ?)",
        (json.dumps({"sku": "SKU-B", "name": "b", "unit_cost_cents": 10, "price_cents": 20}),),
    )
    org.db.connection.execute(
        "INSERT OR REPLACE INTO inventory(sku, on_hand, reserved, reorder_point, record) "
        "VALUES ('SKU-B', 0, 0, 1, '{}')"
    )
    org.db.connection.commit()
    with pytest.raises(Refusal, match="but the outcome is about SKU-TEA"):
        apply_restock(org.db, RestockProposal("SKU-B", 3), assignment_id)


def test_an_effect_requires_an_actor_with_authority(tmp_path: Path) -> None:
    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    org.db.connection.execute(
        "UPDATE actors SET record = json_set(record, '$.authority', json('[\"read\"]')) "
        "WHERE id = 'operator-course'"
    )
    org.db.connection.commit()
    with pytest.raises(Refusal, match="lacks authority"):
        apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id)
