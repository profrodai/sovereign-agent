"""The accepted execution must have caused the effect it is credited with.

Governed by docs/rulings/2026-08-26-outcomes-are-conditions-sows-are-work.md:
an outcome is a standing condition, a SOW is a unit of work, and acceptance
asserts BOTH that the condition holds and that the bound execution contributed
the effect its SOW declares.

The independence matrix below exists because the first version of this file did
not prove independence. Its "contribution false" case always had an older
contributor, so it missed the empty-contributor bypass entirely; and its
"condition false" case only called `run_check()` and never `accept()`. Both
reviewers found that when asked to attack it. Every case here calls `accept()`.
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


def build(tmp_path: Path, checks: list[str] | None = None) -> tuple[Organization, str]:
    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        checks if checks is not None else CHECKS,
        "principal-human",
        "SKU-TEA",
    )
    org.activate(outcome.id, "master-course")
    return org, outcome.id


def run_sow(org: Organization, outcome_id: str, scope: str, effect: str | None) -> tuple[str, str]:
    sow = org.create_sow(outcome_id, scope, Role.OPERATOR, "master-course", effect)
    org.ready_sow(sow.id)
    assignment = org.run_assignment(org.assign(sow.id, "operator-course", "master-course").id)
    return sow.id, assignment.id


def reopen(org: Organization, outcome_id: str) -> None:
    org.db.connection.execute(
        "UPDATE outcomes SET record = json_set(record, '$.state', 'VERIFYING') WHERE id = ?",
        (outcome_id,),
    )
    org.db.connection.commit()


# --- the matrix -------------------------------------------------------------


def test_condition_true_contribution_true_accepts(tmp_path: Path) -> None:
    org, outcome_id = build(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    sow_id, assignment_id = run_sow(org, outcome_id, "replenish", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id, signal.id)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")
    org.verify_outcome_condition(outcome_id, "verifier-course")
    org.accept(outcome_id, "principal-human")


def test_condition_true_but_no_effects_exist_at_all_is_refused(tmp_path: Path) -> None:
    """The empty-contributor case: nobody did anything, and the shelf was fine.

    This is the case the previous guard skipped, because it was written as
    `if contributors and execution_id not in contributors` — so zero
    contributors, the strongest form of "this execution did nothing", made the
    requirement vacuous.
    """
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    sow_id, _assignment_id = run_sow(org, outcome_id, "idle", "replenishment")
    assert org.contributing_executions(outcome_id) == set()
    assert run_check(org.db, "inventory_at_or_above_reorder_point", "SKU-TEA").success

    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")
    with pytest.raises(Refusal, match="produced no replenishment effect"):
        org.accept(outcome_id, "principal-human")


def test_condition_true_but_another_execution_contributed_is_refused(tmp_path: Path) -> None:
    """Week one did the work; week two must not inherit the credit."""
    org, outcome_id = build(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    first_sow, first = run_sow(org, outcome_id, "week one", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), first, signal.id)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(first_sow, "sparring-course")
    org.accept(outcome_id, "principal-human")

    second_sow, second = run_sow(org, outcome_id, "week two", "replenishment")
    assert second not in org.contributing_executions(outcome_id)
    assert run_check(org.db, "inventory_at_or_above_reorder_point", "SKU-TEA").success

    reopen(org, outcome_id)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(second_sow, "sparring-course")
    with pytest.raises(Refusal, match="produced no replenishment effect"):
        org.accept(outcome_id, "principal-human")


def test_condition_false_but_contribution_true_is_refused(tmp_path: Path) -> None:
    """The execution really did restock, then the world moved against it."""
    org, outcome_id = build(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    sow_id, assignment_id = run_sow(org, outcome_id, "replenish", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id, signal.id)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")

    assert assignment_id in org.contributing_executions(outcome_id)
    org.db.connection.execute("UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA'")
    org.db.connection.commit()

    with pytest.raises(Refusal, match="Checks failing at acceptance time"):
        org.accept(outcome_id, "principal-human")


def test_condition_false_and_contribution_false_refuses_deterministically(
    tmp_path: Path,
) -> None:
    """Both wrong: the refusal must be stable, and must name the world first.

    Precedence matters for teaching. "The shelf is empty" is the fact a learner
    can act on; "this execution contributed nothing" is only meaningful once the
    world is right.
    """
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    record_sale(org.db, "SKU-TEA", 2, 400)  # drops below the reorder point
    sow_id, _assignment_id = run_sow(org, outcome_id, "idle", "replenishment")
    assert not run_check(org.db, "inventory_at_or_above_reorder_point", "SKU-TEA").success
    assert org.contributing_executions(outcome_id) == set()

    org.verify_outcome(outcome_id, "verifier-course")
    review = org.review(sow_id, "sparring-course")
    # The failing world is caught upstream: the review itself decides
    # changes_requested, so the SOW never reaches an acceptable state. That is
    # the right precedence — a learner is told the shelf is empty, which they
    # can act on, rather than a contribution technicality they cannot.
    assert review.decision == "changes_requested"
    for _ in range(2):
        with pytest.raises(Refusal, match="SOWs remain open"):
            org.accept(outcome_id, "principal-human")


# --- cross-SOW proof borrowing ----------------------------------------------


def test_one_sow_cannot_borrow_another_sows_proof(tmp_path: Path) -> None:
    """SOW A does nothing; SOW B does the work. A must not be accepted on B.

    Reported at 62a8a6c: `review()` loaded the OUTCOME's latest verification and
    never checked that its assignment belonged to the reviewed SOW.
    """
    org, outcome_id = build(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    idle_sow, _idle = run_sow(org, outcome_id, "idle", "replenishment")
    real_sow, real = run_sow(org, outcome_id, "real", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), real, signal.id)

    org.verify_outcome(outcome_id, "verifier-course")

    # Each SOW now gets its OWN verification, bound to its OWN execution, so a
    # batch cannot be borrowed in the first place.
    idle_verification = org.verification_for_sow(idle_sow)
    real_verification = org.verification_for_sow(real_sow)
    assert idle_verification is not None and real_verification is not None
    assert idle_verification.id != real_verification.id
    assert real_verification.assignment_id == real
    assert idle_verification.assignment_id != real

    # Both can be reviewed on their own batches; the idle SOW is then refused at
    # acceptance for the real reason: its execution changed nothing.
    org.review(idle_sow, "sparring-course")
    org.review(real_sow, "sparring-course")
    with pytest.raises(Refusal, match="produced no replenishment effect"):
        org.accept(outcome_id, "principal-human")


def test_every_sow_needs_its_own_completed_execution(tmp_path: Path) -> None:
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    sow_id, assignment_id = run_sow(org, outcome_id, "replenish", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id, signal.id)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")

    # A second SOW that never ran must block acceptance of the outcome. It is
    # caught by the SOW-state gate first, which is the earlier and clearer
    # refusal; the no-completed-execution guard backs it up for a SOW that has
    # been marked accepted without ever having run.
    unrun = org.create_sow(outcome_id, "never run", Role.OPERATOR, "master-course")
    with pytest.raises(Refusal, match="SOWs remain open"):
        org.accept(outcome_id, "principal-human")

    org.db.connection.execute(
        "UPDATE sows SET record = json_set(record, '$.state', 'ACCEPTED') WHERE id = ?",
        (unrun.id,),
    )
    org.db.connection.commit()
    with pytest.raises(Refusal, match="has no completed execution"):
        org.accept(outcome_id, "principal-human")


# --- structural guarantees ---------------------------------------------------


def test_effects_carry_their_outcome_as_a_structured_column(tmp_path: Path) -> None:
    org, outcome_id = build(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    _sow_id, assignment_id = run_sow(org, outcome_id, "replenish", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment_id, signal.id)
    row = org.db.connection.execute(
        "SELECT outcome_id, assignment_id FROM effects WHERE outcome_id = ?", (outcome_id,)
    ).fetchone()
    assert row is not None and str(row["assignment_id"]) == assignment_id


def test_proof_selection_is_per_sow_not_row_order(tmp_path: Path) -> None:
    """Each SOW resolves to its own execution, whatever order rows were written."""
    org, outcome_id = build(tmp_path)
    first_sow, first = run_sow(org, outcome_id, "one", None)
    second_sow, second = run_sow(org, outcome_id, "two", None)
    assert org.completed_assignment_for_sow(first_sow) == first
    assert org.completed_assignment_for_sow(second_sow) == second


def test_a_sow_with_no_declared_effect_need_not_change_the_world(tmp_path: Path) -> None:
    """Not every legitimate SOW is effectful; the requirement is declared."""
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    sow_id, _assignment_id = run_sow(org, outcome_id, "investigate", None)
    org.verify_outcome(outcome_id, "verifier-course")
    org.review(sow_id, "sparring-course")
    org.verify_outcome_condition(outcome_id, "verifier-course")
    org.accept(outcome_id, "principal-human")


@pytest.mark.parametrize("verify_order", [(0, 1), (1, 0)])
@pytest.mark.parametrize("review_order", [(0, 1), (1, 0)])
@pytest.mark.parametrize("world_moves_between", [False, True])
def test_acceptance_is_independent_of_verify_and_review_order(
    tmp_path: Path,
    verify_order: tuple[int, int],
    review_order: tuple[int, int],
    world_moves_between: bool,
) -> None:
    """Enumerate the orderings instead of claiming they were enumerated.

    I reported "all four permutations accept identically" from a throwaway probe
    and shipped a test exercising ONE fixed ordering while its name said "in
    either order". The reviewer caught the gap. This is the claim as a test, and
    it includes the case the reviewer's reproduction needed: the world moving
    BETWEEN the two verifications, which is what made the oracle disagree with
    the core.

    Both the core and the release oracle must agree in every combination.
    """
    import subprocess
    import sys

    repo_root = Path(__file__).resolve().parent.parent
    org, outcome_id = build(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)

    effectful_sow, effectful = run_sow(org, outcome_id, "replenish", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), effectful, signal.id)
    investigation_sow, _idle = run_sow(org, outcome_id, "investigate", None)
    sow_ids = (effectful_sow, investigation_sow)

    org.verify_sow(sow_ids[verify_order[0]], "verifier-course")
    if world_moves_between:
        # A legitimate sale: inventory and cash change, the outcome stays true.
        record_sale(org.db, "SKU-TEA", 1, 400)
    org.verify_sow(sow_ids[verify_order[1]], "verifier-course")

    for index in review_order:
        org.review(sow_ids[index], "sparring-course")

    org.verify_outcome_condition(outcome_id, "verifier-course")
    org.accept(outcome_id, "principal-human")
    org.db.close()

    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(repo_root / "scripts" / "verify_store_outcome.py"), str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert result.returncode == 0, (
        f"core accepted but the oracle rejected: verify={verify_order} "
        f"review={review_order} world_moves={world_moves_between}\n" + result.stdout
    )


def test_two_completed_sows_are_each_verifiable_and_reviewable(tmp_path: Path) -> None:
    """Complete both SOWs first, then verify and review each, in either order.

    Reported on PR #24 round 5: `verify_outcome()` picked a SOW implicitly by row
    order — and `sows_for()` has no ordering contract — so with two completed
    SOWs one became PERMANENTLY unreviewable, and re-verifying chose the same
    one again. The caller could not name the work being verified.
    """
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    first_sow, first = run_sow(org, outcome_id, "first", None)
    second_sow, second = run_sow(org, outcome_id, "second", None)

    # Verify in the opposite order to the runs, by name.
    org.verify_sow(second_sow, "verifier-course")
    org.verify_sow(first_sow, "verifier-course")

    assert org.verification_for_sow(first_sow).assignment_id == first
    assert org.verification_for_sow(second_sow).assignment_id == second

    # Review in yet another order; neither is blocked by the other.
    org.review(first_sow, "sparring-course")
    org.review(second_sow, "sparring-course")
    assert all(sow.state.value == "ACCEPTED" for sow in org.sows_for(outcome_id))


def test_a_verification_names_the_sow_it_is_about(tmp_path: Path) -> None:
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    sow_id, assignment_id = run_sow(org, outcome_id, "work", None)
    org.verify_sow(sow_id, "verifier-course")
    verification = org.verification_for_sow(sow_id)
    assert verification is not None
    assert verification.sow_id == sow_id
    assert verification.assignment_id == assignment_id
    # The relational chain must close: verification -> assignment -> sow.
    row = org.db.connection.execute(
        "SELECT sow_id FROM assignments WHERE id = ?", (verification.assignment_id,)
    ).fetchone()
    assert str(row["sow_id"]) == verification.sow_id


def test_verifying_a_sow_with_no_completed_execution_is_refused(tmp_path: Path) -> None:
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    sow = org.create_sow(outcome_id, "never run", Role.OPERATOR, "master-course")
    with pytest.raises(Refusal, match="no completed execution to verify"):
        org.verify_sow(sow.id, "verifier-course")


def test_core_and_the_truth_verifier_agree_on_a_multi_sow_organization(
    tmp_path: Path,
) -> None:
    """The control plane must never mint a state its own oracle calls false.

    Reported on PR #24 round 5: the core permitted per-SOW executions while
    `verify_store_outcome.py` still assumed one latest execution owned every
    evidence row, so a legitimate two-SOW organization was ACCEPTED by the core
    and rejected by the release gate. Whichever is right, shipping both is
    indefensible.
    """
    import subprocess
    import sys

    repo_root = Path(__file__).resolve().parent.parent
    org, outcome_id = build(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)

    effectful_sow, effectful = run_sow(org, outcome_id, "replenish", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), effectful, signal.id)
    investigation_sow, _idle = run_sow(org, outcome_id, "investigate", None)

    org.verify_sow(effectful_sow, "verifier-course")
    org.verify_sow(investigation_sow, "verifier-course")
    org.review(effectful_sow, "sparring-course")
    org.review(investigation_sow, "sparring-course")
    org.verify_outcome_condition(outcome_id, "verifier-course")
    org.accept(outcome_id, "principal-human")
    org.db.close()

    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(repo_root / "scripts" / "verify_store_outcome.py"), str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert result.returncode == 0, (
        "core accepted a multi-SOW organization its own verifier rejects:\n"
        + result.stdout
        + result.stderr
    )


def test_a_sow_must_produce_its_declared_deliverable(tmp_path: Path) -> None:
    """For a non-effectful SOW the deliverable IS the proof.

    Holding 2 of docs/rulings/2026-08-26-amendment-conditional-effects.md.
    Judging an investigation by the outcome's inventory checks would be a check
    named for one fact measuring another — this unit's signature defect, one
    scope up.
    """
    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    sow_id, assignment_id = run_sow(org, outcome_id, "investigate", None)
    org.verify_sow(sow_id, "verifier-course")
    org.review(sow_id, "sparring-course")

    assignment = org._assignment(assignment_id)  # noqa: SLF001
    deliverable = (
        tmp_path
        / ".sovereign"
        / "runs"
        / assignment.workspace_id
        / ".sovereign-out"
        / "report.json"
    )
    assert deliverable.is_file(), "precondition: the deliverable was produced"
    deliverable.unlink()

    with pytest.raises(Refusal, match="promised report.json and did not produce it"):
        org.accept(outcome_id, "principal-human")


def test_corroboration_detects_inconsistency_but_does_not_authenticate(
    tmp_path: Path,
) -> None:
    """States the LIMITATION as a fact, so nobody re-derives it as a bug.

    Governed by docs/rulings/2026-08-26-sqlite-writers-are-inside-the-boundary.md.

    An earlier version of this test was named "a forged effect row does not
    credit idle work" and asserted only the half that passes. Both reviewers
    showed the other half: two coordinated fresh appends are mutually consistent
    and equally forged, and acceptance takes them. Asserting only the convenient
    half is how a limitation gets mistaken for a defence.
    """
    import json

    org, outcome_id = build(tmp_path, ["inventory_at_or_above_reorder_point"])
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    real_sow, real = run_sow(org, outcome_id, "real", "replenishment")
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), real, signal.id)
    idle_sow, idle = run_sow(org, outcome_id, "idle", "replenishment")

    # (a) An effect with NO witnessing event is an incomplete record and is not
    #     counted. This is what corroboration genuinely buys.
    org.db.connection.execute(
        "INSERT INTO effects(id, assignment_id, kind, subject, payload, created_at, outcome_id) "
        "SELECT 'eff_orphan', ?, kind, subject, payload, created_at, outcome_id "
        "FROM effects LIMIT 1",
        (idle,),
    )
    org.db.connection.commit()
    assert "replenishment" not in org.effect_kinds_for_execution(idle), (
        "an effect with no witnessing event must not count as work done"
    )

    # (b) Add the matching event and the two agree — because they were written
    #     to agree, not because anything happened. Corroboration cannot tell the
    #     difference, and this asserts that plainly.
    org.db.connection.execute(
        "INSERT INTO events(id, kind, payload, created_at) "
        "VALUES ('evt_forged', 'replenishment.committed', ?, 't')",
        (json.dumps({"assignment_id": idle, "sku": "SKU-TEA"}),),
    )
    org.db.connection.commit()
    assert "replenishment" in org.effect_kinds_for_execution(idle), (
        "two coordinated fresh appends are mutually consistent; corroboration "
        "detects inconsistency and does not authenticate. If this ever fails, "
        "the trust boundary changed and the ruling must be re-derived."
    )
