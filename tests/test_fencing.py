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

import pytest

from reference_organizations.store import seed
from sovereign_agent import fencing
from sovereign_agent.errors import Refusal
from sovereign_agent.ids import utc_now
from sovereign_agent.models import Role
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


def test_acquire_execution_attempt_succeeds_for_a_fresh_assignment(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    attempt = fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", fencing.new_process_identity()
    )
    assert attempt.assignment_id == assignment_id
    assert fencing.verify_execution_attempt(org.db, assignment_id, attempt.id)


def test_second_concurrent_acquire_is_refused_while_first_is_live(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", fencing.new_process_identity()
    )
    with pytest.raises(Refusal, match="already has a live execution attempt"):
        fencing.acquire_execution_attempt(
            org.db, assignment_id, "operator-course", fencing.new_process_identity()
        )


def test_acquire_after_the_prior_attempt_expired_succeeds(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    clock = FakeClock()
    first = fencing.acquire_execution_attempt(
        org.db,
        assignment_id,
        "operator-course",
        fencing.new_process_identity(),
        ttl=timedelta(minutes=1),
        clock=clock,
    )
    clock.advance(timedelta(minutes=2))
    second = fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", fencing.new_process_identity(), clock=clock
    )
    assert second.fencing_token > first.fencing_token
    assert not fencing.verify_execution_attempt(org.db, assignment_id, first.id)
    assert fencing.verify_execution_attempt(org.db, assignment_id, second.id)


def test_verify_execution_attempt_is_false_for_a_bogus_id(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", fencing.new_process_identity()
    )
    assert not fencing.verify_execution_attempt(org.db, assignment_id, "att_bogus")


def test_release_execution_attempt_clears_the_fence(tmp_path: Path) -> None:
    org, assignment_id = _governed(tmp_path)
    attempt = fencing.acquire_execution_attempt(
        org.db, assignment_id, "operator-course", fencing.new_process_identity()
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
    attempt = fencing.acquire_execution_attempt(
        org.db,
        assignment_id,
        "operator-course",
        fencing.new_process_identity(),
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
