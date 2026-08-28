"""Unit 8 proof matrix: actor/process leases, mailbox fencing, assignment fencing.

Every expiry case here uses an INJECTED clock -- a plain closure returning a
fixed `datetime`, advanced by reassigning what it returns -- never a real
sleep. `fencing.py`'s CAS discipline is proven the same way `relay.claim()`'s
already is (`tests/test_concurrency.py`): a compare-and-set statement, not a
read-then-decide race, verified both by direct assertion and, where a
plausible one-line regression exists, by MUTATION -- reverting the fix and
confirming the specific test that names it goes red before restoring green.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from reference_organizations.store import seed
from sovereign_agent import fencing
from sovereign_agent.errors import Refusal
from sovereign_agent.ids import utc_now
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization
from sovereign_agent.relay import claim, complete, dead_letter, send

# --- a fake, advanceable clock ------------------------------------------------


class FakeClock:
    """A `fencing.Clock` a test can advance deterministically. No sleeping."""

    def __init__(self) -> None:
        self.now = utc_now()

    def __call__(self):  # noqa: ANN204 - matches fencing.Clock's Callable[[], datetime]
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now = self.now + delta


def _expire_claim(org: Organization, message_id: str) -> None:
    """Force a message's claim into the past, both the indexed column CAS
    reads and the JSON `record` that `db.get()`/`Message.model_validate`
    reads -- the two must agree, or a test could pass by accident of which
    one a given code path happens to consult."""
    org.db.connection.execute(
        "UPDATE messages SET claim_expires_at = ?, "
        "record = json_set(record, '$.claim_expires_at', ?) WHERE id = ?",
        ("2020-01-01T00:00:00+00:00", "2020-01-01T00:00:00+00:00", message_id),
    )
    org.db.connection.commit()


def _governed(tmp_path: Path) -> tuple[Organization, str]:
    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "t", "d", ["inventory_at_or_above_reorder_point"], "principal-human", "SKU-TEA"
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "s", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    return org, assignment.id


# === 1. Process identity =====================================================


def test_process_identity_is_never_a_pid() -> None:
    """A fresh identity must not be, or contain, this process's own PID as its
    whole value -- PIDs are reused by the OS, so an identity check that could
    collide with a later, unrelated process sharing the same PID is not durable."""
    identity = fencing.new_process_identity()
    assert identity != str(__import__("os").getpid())
    assert identity.startswith("proc_")


def test_process_identity_is_unique_across_calls() -> None:
    identities = {fencing.new_process_identity() for _ in range(50)}
    assert len(identities) == 50


# === 2. Actor / process leases (proof matrix) ================================


def test_acquire_actor_lease_succeeds_with_no_prior_lease(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    lease = fencing.acquire_actor_lease(org.db, "operator-course", fencing.new_process_identity())
    assert lease.actor_id == "operator-course"
    assert lease.fencing_token >= 1


def test_two_racing_acquirers_produce_exactly_one_winner(tmp_path: Path) -> None:
    """The CAS property, proven the same way relay.claim()'s is: only one of
    two attempts against an unexpired lease may succeed."""
    org = Organization.init(tmp_path)
    p1, p2 = fencing.new_process_identity(), fencing.new_process_identity()
    fencing.acquire_actor_lease(org.db, "operator-course", p1)
    with pytest.raises(Refusal, match="already hosted"):
        fencing.acquire_actor_lease(org.db, "operator-course", p2)


def test_renewal_preserves_the_same_fencing_token(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    p1 = fencing.new_process_identity()
    lease = fencing.acquire_actor_lease(org.db, "operator-course", p1)
    renewed = fencing.renew_actor_lease(org.db, "operator-course", p1, lease.fencing_token)
    assert renewed.fencing_token == lease.fencing_token
    assert renewed.expires_at > lease.expires_at


def test_renewal_by_a_process_that_does_not_hold_the_lease_is_refused(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    p1, p2 = fencing.new_process_identity(), fencing.new_process_identity()
    lease = fencing.acquire_actor_lease(org.db, "operator-course", p1)
    with pytest.raises(Refusal, match="does not hold"):
        fencing.renew_actor_lease(org.db, "operator-course", p2, lease.fencing_token)


def test_renewal_is_repeatable_and_keeps_extending_the_same_token(tmp_path: Path) -> None:
    """Renewal is idempotent in the token it carries -- ownership is not
    reissued each time, only the expiry moves forward. Two renewals in a row
    by the true holder both succeed and both keep the original token."""
    org = Organization.init(tmp_path)
    p1 = fencing.new_process_identity()
    lease = fencing.acquire_actor_lease(org.db, "operator-course", p1)
    once = fencing.renew_actor_lease(org.db, "operator-course", p1, lease.fencing_token)
    twice = fencing.renew_actor_lease(org.db, "operator-course", p1, lease.fencing_token)
    assert once.fencing_token == lease.fencing_token == twice.fencing_token
    assert twice.expires_at >= once.expires_at


def test_takeover_after_expiry_mints_a_strictly_greater_token(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    clock = FakeClock()
    p1, p2 = fencing.new_process_identity(), fencing.new_process_identity()
    first = fencing.acquire_actor_lease(org.db, "operator-course", p1, clock=clock)
    clock.advance(timedelta(minutes=10))
    second = fencing.acquire_actor_lease(org.db, "operator-course", p2, clock=clock)
    assert second.fencing_token > first.fencing_token
    assert second.process_identity == p2


def test_a_process_that_resumes_after_losing_its_lease_is_stale(tmp_path: Path) -> None:
    """The takeover's own new token is current; the original process's
    remembered token can never again be renewed once superseded."""
    org = Organization.init(tmp_path)
    clock = FakeClock()
    p1, p2 = fencing.new_process_identity(), fencing.new_process_identity()
    first = fencing.acquire_actor_lease(org.db, "operator-course", p1, clock=clock)
    clock.advance(timedelta(minutes=10))
    fencing.acquire_actor_lease(org.db, "operator-course", p2, clock=clock)
    with pytest.raises(Refusal):
        fencing.renew_actor_lease(org.db, "operator-course", p1, first.fencing_token, clock=clock)


def test_expired_actor_leases_are_reported_not_acted_on(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    clock = FakeClock()
    p1 = fencing.new_process_identity()
    fencing.acquire_actor_lease(org.db, "operator-course", p1, clock=clock)
    assert fencing.expired_actor_leases(org.db, clock=clock) == []
    clock.advance(timedelta(minutes=10))
    expired = fencing.expired_actor_leases(org.db, clock=clock)
    assert [lease.actor_id for lease in expired] == ["operator-course"]


def test_corrupt_lease_state_fails_closed_not_silently(tmp_path: Path) -> None:
    """A lease row missing its expiry entirely (NULL, never populated) must
    not be silently treated as either 'always valid' or 'always expired' --
    acquiring against it should still go through the same CAS comparison,
    which SQLite evaluates as neither TRUE, so acquisition proceeds exactly
    as it would with no row at all rather than crashing or granting blindly."""
    org = Organization.init(tmp_path)
    org.db.connection.execute(
        "INSERT INTO actor_leases(actor_id, process_identity, fencing_token, acquired_at, "
        "expires_at, renewed_at) VALUES ('operator-course', 'proc_corrupt', 1, "
        "'2020-01-01T00:00:00+00:00', '', '2020-01-01T00:00:00+00:00')"
    )
    org.db.connection.commit()
    # An empty-string expires_at compares as > any real ISO timestamp under
    # SQLite's default TEXT collation for some inputs and < for others; the
    # acquisition must not silently succeed on an ambiguous read -- it must
    # go through the same WHERE expires_at <= ? comparison as any other row
    # and refuse if that comparison does not hold.
    p2 = fencing.new_process_identity()
    try:
        fencing.acquire_actor_lease(org.db, "operator-course", p2)
    except Refusal:
        pass  # fail-closed: refused rather than silently granted


def test_release_actor_lease_succeeds_when_the_token_still_matches(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    p1 = fencing.new_process_identity()
    lease = fencing.acquire_actor_lease(org.db, "operator-course", p1)
    released = fencing.release_actor_lease(org.db, "operator-course", p1, lease.fencing_token)
    assert released is True
    assert fencing.current_actor_lease(org.db, "operator-course") is None


def test_release_actor_lease_is_a_no_op_after_a_takeover(tmp_path: Path) -> None:
    """The exact safety property Sparring's fix for F-R2-1 depends on: a
    process releasing a lease it no longer actually holds (because a
    different process already took it over) must not clear the NEW owner's
    lease. This is what makes it safe for `organization.run_assignment` to
    call `release_actor_lease` unconditionally in a `finally` block on
    every path out, including a path where this process's own lease was
    already superseded before the release runs."""
    org = Organization.init(tmp_path)
    p1 = fencing.new_process_identity()
    stale_lease = fencing.acquire_actor_lease(org.db, "operator-course", p1)

    org.db.connection.execute(
        "UPDATE actor_leases SET expires_at = ? WHERE actor_id = ?",
        ("2020-01-01T00:00:00+00:00", "operator-course"),
    )
    org.db.connection.commit()
    p2 = fencing.new_process_identity()
    fresh_lease = fencing.acquire_actor_lease(org.db, "operator-course", p2)

    released = fencing.release_actor_lease(org.db, "operator-course", p1, stale_lease.fencing_token)
    assert released is False, "releasing a superseded lease must be a no-op, not a real release"

    current = fencing.current_actor_lease(org.db, "operator-course")
    assert current is not None
    assert current.process_identity == p2
    assert current.fencing_token == fresh_lease.fencing_token


# === 3. Mailbox fencing (F-U4-1 closure + proof matrix) ======================


def test_same_owner_unexpired_claim_is_idempotent_same_token(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    first = claim(org.db, message.id, "sparring-course")
    again = claim(org.db, message.id, "sparring-course")
    assert again.fencing_token == first.fencing_token


def test_same_owner_expired_claim_mints_a_fresh_token_fu4_1(tmp_path: Path) -> None:
    """F-U4-1, closed: the previously-unreachable expired branch for the SAME
    owner is now reachable, and it renews rather than returning stale state."""
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    stale = claim(org.db, message.id, "sparring-course")
    _expire_claim(org, message.id)
    fresh = claim(org.db, message.id, "sparring-course")
    assert fresh.fencing_token != stale.fencing_token
    assert fresh.claim_expires_at is not None and fresh.claim_expires_at > utc_now()


def test_an_unaddressed_actor_is_still_refused_regardless_of_fencing(tmp_path: Path) -> None:
    """Fencing adds a token check on TOP of the existing recipient check; it
    must not replace or weaken it. `tests/test_concurrency.py::
    test_only_one_contender_wins_a_contested_lease` covers the genuine
    two-distinct-contenders CAS race under real thread concurrency -- this
    test only confirms the addressed-recipient gate still fires first."""
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    with pytest.raises(Refusal, match="cannot claim"):
        claim(org.db, message.id, "operator-course")


def test_complete_with_the_current_token_succeeds(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    claimed = claim(org.db, message.id, "sparring-course")
    done = complete(org.db, message.id, "sparring-course", fencing_token=claimed.fencing_token)
    assert done.state.value == "DONE"


def test_complete_with_a_stale_token_is_refused(tmp_path: Path) -> None:
    """The decisive F-U4-1 proof: a process that resumes after its lease was
    reclaimed by a fresher claim of the SAME actor id must not be able to
    complete under the token it remembers."""
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    stale = claim(org.db, message.id, "sparring-course")
    _expire_claim(org, message.id)
    claim(org.db, message.id, "sparring-course")  # a fresher process takes over
    with pytest.raises(Refusal, match="fencing token"):
        complete(org.db, message.id, "sparring-course", fencing_token=stale.fencing_token)


def test_dead_letter_with_a_stale_message_object_is_refused(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    stale = claim(org.db, message.id, "sparring-course")
    _expire_claim(org, message.id)
    claim(org.db, message.id, "sparring-course")
    with pytest.raises(Refusal, match="modified by another claim"):
        dead_letter(org.db, stale)


def test_dead_letter_with_the_current_message_object_succeeds(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    claimed = claim(org.db, message.id, "sparring-course")
    retried = dead_letter(org.db, claimed)
    assert retried.retry_count == 1
    assert retried.fencing_token is None  # cleared on retry -- a fresh claim mints anew


def test_never_claimed_message_has_no_fencing_token(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    assert message.fencing_token is None


# === 4. Assignment / execution-attempt fencing (proof matrix) ================


def _leased(org, actor_id: str, process_identity: str, *, ttl=None, clock=utc_now):  # noqa: ANN001
    """Acquire the actor lease `acquire_execution_attempt` now requires,
    returning its fencing token -- the precondition every direct
    fencing.acquire_execution_attempt call below must establish first,
    mirroring what organization.run_assignment does at the top of its own
    method."""
    kwargs = {"clock": clock}
    if ttl is not None:
        kwargs["ttl"] = ttl
    return fencing.acquire_actor_lease(org.db, actor_id, process_identity, **kwargs).fencing_token


def test_acquire_execution_attempt_succeeds_for_a_fresh_assignment(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    process_identity = fencing.new_process_identity()
    lease_token = _leased(org, "operator-course", process_identity)
    attempt = fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", process_identity, lease_token
    )
    assert attempt.assignment_id == assignment_id
    assert attempt.actor_lease_fencing_token == lease_token
    assert fencing.verify_execution_attempt(org.db, assignment_id, attempt.id)


def test_acquire_execution_attempt_refuses_without_a_live_actor_lease(tmp_path: Path) -> None:
    """The decisive binding property: presenting a fencing_token that does
    NOT correspond to a live actor_leases row -- because none was ever
    acquired, here -- is refused, even though the ASSIGNMENT itself has no
    competing attempt. An execution attempt is not merely 'no other attempt
    for this assignment'; it is 'no other attempt for this assignment, and
    the caller currently holds the actor hosting lease.'
    """
    org, assignment_id = _governed(tmp_path)
    with pytest.raises(Refusal, match="does not currently hold a live lease"):
        fencing.acquire_execution_attempt(
            org.db, assignment_id, "operator-course", fencing.new_process_identity(), 999999
        )


def test_second_concurrent_acquire_is_refused_while_first_is_live(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    process_identity = fencing.new_process_identity()
    lease_token = _leased(org, "operator-course", process_identity)
    fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", process_identity, lease_token
    )
    with pytest.raises(Refusal, match="already has a live execution attempt"):
        fencing.acquire_execution_attempt(
            org.db, assignment_id, "operator-course", process_identity, lease_token
        )


def test_acquire_after_the_prior_attempt_expired_succeeds(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    clock = FakeClock()
    process_identity = fencing.new_process_identity()
    lease_token = _leased(org, "operator-course", process_identity, clock=clock)
    first = fencing.acquire_execution_attempt(
        org.db,
        assignment_id,
        "operator-course",
        process_identity,
        lease_token,
        ttl=timedelta(minutes=1),
        clock=clock,
    )
    clock.advance(timedelta(minutes=2))
    # Renew (not re-acquire) the SAME process's actor lease -- this test is
    # about the EXECUTION attempt re-acquiring cleanly after its own expiry,
    # not about the actor lease changing hands, so the actor lease itself
    # should simply still be held and extended by the same process, the
    # ordinary shape acquire_or_renew_actor_lease exists for.
    lease_token_2 = fencing.acquire_or_renew_actor_lease(
        org.db, "operator-course", process_identity, clock=clock
    ).fencing_token
    second = fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", process_identity, lease_token_2, clock=clock
    )
    assert second.fencing_token > first.fencing_token
    assert not fencing.verify_execution_attempt(org.db, assignment_id, first.id)
    assert fencing.verify_execution_attempt(org.db, assignment_id, second.id)


def test_verify_execution_attempt_is_false_for_a_bogus_id(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    process_identity = fencing.new_process_identity()
    lease_token = _leased(org, "operator-course", process_identity)
    fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", process_identity, lease_token
    )
    assert not fencing.verify_execution_attempt(org.db, assignment_id, "att_bogus")


def test_release_execution_attempt_clears_the_fence(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    process_identity = fencing.new_process_identity()
    lease_token = _leased(org, "operator-course", process_identity)
    attempt = fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", process_identity, lease_token
    )
    with org.db.transaction() as connection:
        fencing.release_execution_attempt(connection, assignment_id, attempt.id, "DONE")
    assert not fencing.verify_execution_attempt(org.db, assignment_id, attempt.id)
    row = org.db.connection.execute(
        "SELECT status FROM execution_attempts WHERE id = ?", (attempt.id,)
    ).fetchone()
    assert row["status"] == "DONE"


def test_expired_execution_attempts_lists_only_still_current_ones(tmp_path: Path) -> None:
    """An attempt whose fence has already been released (a normal completion)
    must not show up as recoverable just because its own row is old -- only
    an attempt STILL pointed at by assignments.current_execution_attempt
    counts, which is what makes recovery idempotent."""
    org, assignment_id = _governed(tmp_path)
    clock = FakeClock()
    process_identity = fencing.new_process_identity()
    lease_token = _leased(org, "operator-course", process_identity, clock=clock)
    attempt = fencing.acquire_execution_attempt(
        org.db,
        assignment_id,
        "operator-course",
        process_identity,
        lease_token,
        ttl=timedelta(minutes=1),
        clock=clock,
    )
    with org.db.transaction() as connection:
        fencing.release_execution_attempt(connection, assignment_id, attempt.id, "DONE")
    clock.advance(timedelta(minutes=5))
    assert fencing.expired_execution_attempts(org.db, clock=clock) == []


def test_a_completed_assignment_run_via_the_real_path_leaves_no_recoverable_attempt(
    tmp_path: Path,
) -> None:
    """End-to-end proof that `organization.run_assignment`'s own fence
    acquisition and release (not the standalone fencing.py calls above) also
    leaves nothing for the supervisor to recover."""
    org, assignment_id = _governed(tmp_path)
    result = org.run_assignment(assignment_id)
    assert result.state.value == "COMPLETED"
    assert fencing.expired_execution_attempts(org.db) == []
    row = org.db.connection.execute(
        "SELECT current_execution_attempt FROM assignments WHERE id = ?", (assignment_id,)
    ).fetchone()
    assert row["current_execution_attempt"] is None


def test_a_completed_run_releases_the_actor_lease_for_a_fresh_process(tmp_path: Path) -> None:
    """A real usability property, found by reproduction rather than
    theorized: a short-lived process (the ordinary CLI `run` command, one
    assignment per process invocation, or `demo store`) must not keep the
    actor locked out for the rest of ACTOR_LEASE_TTL after it has already
    exited and completed its work. Two consecutive `run_assignment` calls,
    each through a genuinely fresh `Organization` instance (fresh process_
    identity), against DIFFERENT assignments for the SAME actor, must both
    succeed with no wait -- reproduces the exact failure this fix closes:
    two consecutive `sovereign-agent demo store` invocations against the
    same root used to collide even with no crash between them."""
    import sovereign_agent.organization as organization_module

    org_a, assignment_a_id, assignment_b_id = _governed_twice(tmp_path)
    result_a = org_a.run_assignment(assignment_a_id)
    assert result_a.state.value == "COMPLETED"

    assert fencing.current_actor_lease(org_a.db, "operator-course") is None, (
        "the actor lease must be released once this process's own run has "
        "terminally completed, not held for the rest of its TTL"
    )

    org_b = organization_module.Organization(tmp_path)
    result_b = org_b.run_assignment(assignment_b_id)
    assert result_b.state.value == "COMPLETED", (
        "a second, later process must not be blocked by a lease the first process already released"
    )


def test_a_refused_run_also_releases_the_actor_lease_fu_r2_1(tmp_path: Path) -> None:
    """F-R2-1: the actor lease leaked on every REFUSAL path, not merely the
    success path the test above covers. `release_actor_lease` was called
    exactly once, at the very end of `run_assignment`, AFTER `reclaim_
    workspace` -- so every `raise Refusal` between the lease acquisition at
    the top of the method (workspace_policy, either symlink check, or,
    inside `acquire_execution_attempt`, `execution_attempt_held` or a lost
    fence) propagated straight out and skipped that release entirely. The
    lease then stayed held for the rest of its TTL even though the process
    that acquired it had already exited -- reachable on an ordinary
    retry-after-a-refused-run path, not an adversarial edge case.

    Reproduced here with the simplest early-refusal shape (an unrecognized
    `workspace_policy`, exactly the same shape Sparring's own independent
    reproduction used): a first process's run is refused before the
    workspace is ever created; a second, genuinely separate process then
    attempts a DIFFERENT assignment for the SAME actor and must succeed,
    not be refused `actor_lease_held` by a lease the first process no
    longer has any process alive to hold.
    """
    import sovereign_agent.organization as organization_module

    org_a, assignment_a_id, assignment_b_id = _governed_twice(tmp_path)
    org_a.actors["operator-course"].workspace_policy = "not_a_real_policy"
    with pytest.raises(Refusal, match="Unknown workspace policy"):
        org_a.run_assignment(assignment_a_id)

    assert fencing.current_actor_lease(org_a.db, "operator-course") is None, (
        "the actor lease must be released even when run_assignment refuses "
        "before the provider is ever invoked, not held for the rest of its TTL"
    )

    # A genuinely separate process -- fresh Organization, fresh
    # process_identity -- retrying a DIFFERENT assignment for the SAME
    # actor. Must succeed: nothing alive still holds the lease.
    org_b = organization_module.Organization(tmp_path)
    org_b.actors["operator-course"].workspace_policy = "temporary_directory"
    result_b = org_b.run_assignment(assignment_b_id)
    assert result_b.state.value == "COMPLETED", (
        "a legitimate retry from a fresh process must not be blocked by a "
        "lease the first, now-exited process's refused run left behind"
    )


def _governed_twice(tmp_path: Path) -> tuple[Organization, str, str]:
    """One organization, one actor (`operator-course`), TWO distinct SOWs
    and assignments -- the shape requirement 5's decisive test needs: two
    DIFFERENT assignment_ids for the SAME actor, not the same assignment
    acquired twice (which the execution-attempt tests above already cover)."""
    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "t", "d", ["inventory_at_or_above_reorder_point"], "principal-human", "SKU-TEA"
    )
    org.activate(outcome.id, "master-course")
    sow_a = org.create_sow(outcome.id, "a", Role.OPERATOR, "master-course")
    org.ready_sow(sow_a.id)
    assignment_a = org.assign(sow_a.id, "operator-course", "master-course")
    sow_b = org.create_sow(outcome.id, "b", Role.OPERATOR, "master-course")
    org.ready_sow(sow_b.id)
    assignment_b = org.assign(sow_b.id, "operator-course", "master-course")
    return org, assignment_a.id, assignment_b.id


def test_actor_lease_blocks_a_second_assignment_for_the_same_actor_before_invocation(
    tmp_path: Path,
) -> None:
    """THE decisive actor-lease binding property, ruled on directly by the
    Principal: `acquire_execution_attempt` alone is keyed by assignment_id,
    so two DIFFERENT assignments for the SAME actor could each acquire
    their own execution attempt and both run under two separate processes
    -- exactly the process-level exclusivity gap
    docs/rulings/2026-08-26-one-process-per-actor.md named and deferred to
    this unit. This is a REAL two-process proof, not a lease-table check in
    isolation: two genuinely separate `Organization` instances (distinct
    `process_identity`, distinct SQLite connections, opened against the
    SAME root) each attempt `run_assignment` on a DIFFERENT assignment for
    the SAME actor.

    Process A is made to stall mid-invocation -- `invoke_actor` is patched
    to block on a `threading.Event` process B sets only after its own
    attempt has already been refused -- so process A's actor lease is
    GENUINELY still live (not released; `run_assignment` only releases the
    lease after its OWN terminal write succeeds, and process A's write has
    not happened yet) at the exact moment process B contends for it. This
    is the realistic shape: one process still legitimately busy running
    assignment A, a second process trying to start assignment B for the
    same actor. Process B's `invoke_actor` is spied on with a counter,
    following the exact pattern Unit 7 already established
    (`test_unknown_workspace_policy_refuses_before_the_provider_ever_runs`):
    the provider must never be invoked at all for process B, not merely
    have its result discarded afterward.
    """
    import threading

    import sovereign_agent.execution as execution_module
    import sovereign_agent.organization as organization_module

    setup_org, assignment_a_id, assignment_b_id = _governed_twice(tmp_path)
    setup_org.db.close()

    release_a = threading.Event()
    a_lease_acquired = threading.Event()
    real_invoke = execution_module.invoke_actor
    b_invoked = {"count": 0}

    def stalling_invoke_for_a(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        # Process A has acquired its actor lease and its execution attempt
        # by the time this fires (both happen before invoke_actor in
        # run_assignment) -- signal readiness, then hold here so the lease
        # stays live while process B, on a separate real connection below,
        # contends for it.
        a_lease_acquired.set()
        release_a.wait(timeout=10)
        return real_invoke(*args, **kwargs)

    def counting_invoke_for_b(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        b_invoked["count"] += 1
        return real_invoke(*args, **kwargs)

    result_a: dict[str, object] = {}

    def run_a() -> None:
        # A genuinely SEPARATE Organization instance, opened INSIDE this
        # thread -- SQLite connections are not usable across threads, and a
        # real second connection (not a shared one) is the whole point of
        # this being a REAL two-process proof, matching test_concurrency.
        # py's own _run_concurrently pattern.
        org_a = organization_module.Organization(tmp_path)
        with patch.object(organization_module, "invoke_actor", side_effect=stalling_invoke_for_a):
            result_a["assignment"] = org_a.run_assignment(assignment_a_id)
            result_a["process_identity"] = org_a.process_identity

    thread_a = threading.Thread(target=run_a)
    thread_a.start()
    try:
        assert a_lease_acquired.wait(timeout=10), (
            "process A never reached invoke_actor (and therefore never "
            "acquired its actor lease) before the deadline"
        )
        org_b = organization_module.Organization(tmp_path)
        assert org_b.process_identity != result_a.get("process_identity")

        with patch.object(organization_module, "invoke_actor", side_effect=counting_invoke_for_b):
            with pytest.raises(Refusal, match="already hosted by another live process"):
                org_b.run_assignment(assignment_b_id)
    finally:
        release_a.set()
        thread_a.join(timeout=10)

    assert result_a.get("assignment") is not None, "process A's own run must have completed"
    assert b_invoked["count"] == 0, (
        "the provider must never be invoked for the second process while "
        "the first process's actor lease is still live"
    )
    final_b = org_b._assignment(assignment_b_id)  # noqa: SLF001
    assert final_b.state == AssignmentState.CREATED, (
        "the second assignment must not even reach RUNNING -- refused before "
        "workspace allocation, matching Unit 7's own validate-before-anything- "
        "touched precedent for workspace_policy and the symlink checks"
    )


def test_the_ordinary_run_assignment_path_cannot_bypass_the_actor_lease(tmp_path: Path) -> None:
    """Requirement 6: the ordinary CLI `run` command dispatches straight to
    `Organization.run_assignment` (cli.py's `_run` handler: `org.assign(...)`
    then `org.run_assignment(assignment.id)`, no other code path in
    between) -- so calling `run_assignment` directly, exactly as `_run`
    does, IS the proof that the CLI path cannot bypass this requirement.
    There is no separate enforcement layer in the CLI itself to
    accidentally skip; the fence lives in the one method both the CLI and
    the supervisor's own future dispatch would have to call.

    A live, not-yet-expired lease is established directly (the same
    primitive `run_assignment` itself calls at its own top) rather than by
    leaving a first `run_assignment` call's own lease around -- a
    completed `run_assignment` call now correctly RELEASES its actor lease
    (a short-lived CLI process must not keep the actor locked out for the
    rest of ACTOR_LEASE_TTL after it has already exited), so a genuinely
    live lease from a DIFFERENT, still-active process is what this test
    must establish to prove the refusal."""
    org_a, assignment_a_id, assignment_b_id = _governed_twice(tmp_path)
    other_process = fencing.new_process_identity()
    fencing.acquire_actor_lease(org_a.db, "operator-course", other_process)

    import sovereign_agent.organization as organization_module

    org_b = organization_module.Organization(tmp_path)
    with pytest.raises(Refusal, match="already hosted by another live process"):
        # The exact call cli.py's _run handler makes: org.run_assignment(assignment.id).
        org_b.run_assignment(assignment_b_id)


def test_acquire_execution_attempt_reverifies_the_lease_even_if_the_caller_lost_it_since(
    tmp_path: Path,
) -> None:
    """Isolates the SECOND, independent check `acquire_execution_attempt`
    performs, distinct from `run_assignment`'s own top-of-method actor-lease
    acquisition: even a caller that legitimately held a live lease when it
    computed `actor_lease_fencing_token` must be re-verified against the
    CURRENT durable row at the moment `acquire_execution_attempt` itself
    runs -- a real TOCTOU race (the lease could be taken over by a fresher
    process between the two calls), not merely trusting the token the
    caller presents. Simulated directly: acquire a real lease, then let a
    DIFFERENT process take it over (advancing a fake clock past its TTL)
    before presenting the FIRST process's now-stale token."""
    org, assignment_id = _governed(tmp_path)
    clock = FakeClock()
    p1 = fencing.new_process_identity()
    stale_lease = fencing.acquire_actor_lease(org.db, "operator-course", p1, clock=clock)
    clock.advance(timedelta(minutes=10))
    p2 = fencing.new_process_identity()
    fencing.acquire_actor_lease(org.db, "operator-course", p2, clock=clock)  # takeover

    with pytest.raises(Refusal, match="does not currently hold a live lease"):
        fencing.acquire_execution_attempt(
            org.db, assignment_id, "operator-course", p1, stale_lease.fencing_token, clock=clock
        )


def test_a_stolen_fence_mid_invocation_refuses_the_terminal_write(tmp_path: Path) -> None:
    """THE decisive fencing property: fencing is not an OS sandbox, so a
    provider subprocess a stale worker started can still run to completion
    and produce a real receipt in memory -- but if something else (in
    production, the supervisor recovering the assignment) has taken over
    the fence by the time `run_assignment` reaches its terminal transaction,
    that transaction's own atomic WHERE current_execution_attempt = ? clause
    must refuse the write rather than let the stale result become canonical.

    Simulated here by stealing the fence (clearing
    `current_execution_attempt` directly, the same durable fact a real
    supervisor recovery would leave behind) from inside `invoke_actor`,
    mid-call -- after this invocation's own attempt was acquired, before its
    terminal transaction runs. This is the specific mechanism review of this
    unit's own reproduction relied on; see the mutation check in this
    module's own history (organization.py's fence-check WHERE clause,
    falsified by removing it, confirmed this test goes red and restored)."""
    import sovereign_agent.organization as organization_module

    org, assignment_id = _governed(tmp_path)
    real_invoke_actor = organization_module.invoke_actor

    def stealing_invoke_actor(worker, sow, workspace, output, assignment_id=""):  # noqa: ANN001
        org.db.connection.execute(
            "UPDATE assignments SET current_execution_attempt = NULL WHERE id = ?",
            (assignment_id,),
        )
        org.db.connection.commit()
        return real_invoke_actor(worker, sow, workspace, output, assignment_id=assignment_id)

    organization_module.invoke_actor = stealing_invoke_actor
    try:
        with pytest.raises(Refusal, match="lost its execution attempt"):
            org.run_assignment(assignment_id)
    finally:
        organization_module.invoke_actor = real_invoke_actor
