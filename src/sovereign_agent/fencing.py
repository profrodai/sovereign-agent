"""Process identity, actor leases, and execution-attempt fencing.

Unit 4 proved one thing precisely: two *distinct* actors contending for one
mailbox message produce exactly one winner. It also, deliberately, left one
thing unproven: a second *process* hosting the *same* actor id was not
defended against, because defending against it means inventing process
lifecycle -- and Unit 4 had no supervisor to own that
(`docs/rulings/2026-08-26-one-process-per-actor.md`,
`docs/rulings/2026-08-26-deferral-unit4-fencing.md`).

This module is that process lifecycle. It answers three questions, always by
compare-and-set against SQLite -- the same discipline `relay.claim()` already
uses, never a read-then-write race:

1. **Which process may host actor X right now?** `acquire_actor_lease` /
   `renew_actor_lease` / `current_actor_lease`.
2. **Which attempt may still write assignment Y's terminal state?**
   `acquire_execution_attempt` / `verify_execution_attempt`.
3. **What names this process, durably, across its own restarts?**
   `new_process_identity` -- a fresh random id, never a PID. PIDs are reused
   by the operating system; a stale process that resumes after its lease
   expired must not be able to pass a "same PID" check against a *new*
   process the OS later assigned that same number.

Every acquisition and renewal takes a `clock: Callable[[], datetime]`
(default `sovereign_agent.ids.utc_now`) so lease-expiry tests never depend on
a real sleep -- inject a fake clock, advance it, assert the CAS behaves.

**Fencing is not an OS sandbox.** A worker that has lost its lease or its
execution attempt can still write files to disk -- nothing here stops a
subprocess from writing bytes. What fencing guarantees is narrower and
different: those bytes never become canonical. A stale attempt's write to
`assignments.current_execution_attempt`, to a mailbox message's terminal
state, or to a workspace reclaim is refused by the same compare-and-set that
would refuse a second actor's claim. See `docs/v1-unit8-supervisor-fencing-
recovery.md` for the full contract.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.ids import new_id, utc_now

Clock = Callable[[], datetime]

ACTOR_LEASE_TTL = timedelta(minutes=5)
EXECUTION_ATTEMPT_TTL = timedelta(minutes=15)


def new_process_identity() -> str:
    """A fresh, durable identity for this process instance.

    Never a PID: PIDs are reused by the operating system, so "same PID" is
    not evidence of "same process instance" once enough time (or enough
    process churn) has passed. `uuid4` needs no coordination and never
    repeats in practice.
    """
    return f"proc_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class ActorLease:
    """A durable claim that one process instance may host one actor.

    `fencing_token` is drawn from `lease_tokens`, a single monotonic counter
    shared by every lease and every execution attempt in this database.
    Renewal keeps the same token (ownership is preserved); a takeover after
    expiry always mints a fresh, strictly greater one, so a resumed stale
    process can never present a token that still compares as current.
    """

    actor_id: str
    process_identity: str
    fencing_token: int
    acquired_at: datetime
    expires_at: datetime
    renewed_at: datetime


@dataclass(frozen=True)
class ExecutionAttempt:
    """A durable claim that one process instance may run one assignment.

    Bound to the `RUNNING` transition: `organization.run_assignment` acquires
    one before invoking a provider, and the terminal transaction that follows
    checks `verify_execution_attempt` inside the same SQLite transaction that
    writes the assignment's terminal state, so a stale attempt cannot win the
    write even if its provider subprocess is still running and reaches that
    line.

    `actor_lease_fencing_token` binds this attempt to the actor lease that
    was live at the moment it was acquired -- `acquire_execution_attempt`
    requires a caller to already hold a current, unexpired actor lease and
    records its token here, connecting the two mechanisms rather than
    leaving them as independent CAS tables that merely happen to agree.
    """

    id: str
    assignment_id: str
    actor_id: str
    process_identity: str
    fencing_token: int
    actor_lease_fencing_token: int
    acquired_at: datetime
    expires_at: datetime
    status: str


def _mint_token(db: Database, kind: str, clock: Clock) -> int:
    """Insert one row into the shared monotonic counter, return its token.

    Callers always do this inside the same `db.immediate()` transaction as
    the CAS it is fencing, so the mint and the write it authorizes commit or
    roll back together.
    """
    cursor = db.connection.execute(
        "INSERT INTO lease_tokens(kind, created_at) VALUES (?, ?)",
        (kind, clock().isoformat()),
    )
    token = cursor.lastrowid
    assert token is not None
    return int(token)


def current_actor_lease(db: Database, actor_id: str) -> ActorLease | None:
    row = db.connection.execute(
        "SELECT * FROM actor_leases WHERE actor_id = ?", (actor_id,)
    ).fetchone()
    if row is None:
        return None
    return ActorLease(
        actor_id=row["actor_id"],
        process_identity=row["process_identity"],
        fencing_token=int(row["fencing_token"]),
        acquired_at=datetime.fromisoformat(row["acquired_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]),
        renewed_at=datetime.fromisoformat(row["renewed_at"]),
    )


def acquire_actor_lease(
    db: Database,
    actor_id: str,
    process_identity: str,
    *,
    ttl: timedelta = ACTOR_LEASE_TTL,
    clock: Clock = utc_now,
) -> ActorLease:
    """Take an exclusive lease on hosting `actor_id`, or refuse.

    Compare-and-set, not read-then-write: the same shape as
    `relay.claim()`. Succeeds when no row exists yet, or the existing row's
    lease has expired -- in either case a fresh fencing token is minted, so
    a process that resumes after losing the lease can never reuse the old
    token. Two racing acquirers each attempt this inside `db.immediate()`;
    exactly one wins, because SQLite's reserved lock serializes them.
    """
    now = clock()
    with db.immediate() as connection:
        token = _mint_token(db, "actor", clock)
        expires_at = now + ttl
        cursor = connection.execute(
            "UPDATE actor_leases SET process_identity = ?, fencing_token = ?, "
            "acquired_at = ?, expires_at = ?, renewed_at = ? "
            "WHERE actor_id = ? AND expires_at <= ?",
            (
                process_identity,
                token,
                now.isoformat(),
                expires_at.isoformat(),
                now.isoformat(),
                actor_id,
                now.isoformat(),
            ),
        )
        if cursor.rowcount == 0:
            try:
                connection.execute(
                    "INSERT INTO actor_leases(actor_id, process_identity, fencing_token, "
                    "acquired_at, expires_at, renewed_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        actor_id,
                        process_identity,
                        token,
                        now.isoformat(),
                        expires_at.isoformat(),
                        now.isoformat(),
                    ),
                )
            except Exception as error:
                raise Refusal(
                    f"Actor {actor_id!r} is already hosted by another live process.",
                    "Only one unexpired lease may host an actor at a time.",
                    "sovereign-agent supervisor --root PATH --once",
                    "Wait for the current lease to expire, or run the supervisor "
                    "to recover an abandoned one.",
                    category="actor_lease_held",
                ) from error
    leased = current_actor_lease(db, actor_id)
    assert leased is not None
    return leased


def renew_actor_lease(
    db: Database,
    actor_id: str,
    process_identity: str,
    fencing_token: int,
    *,
    ttl: timedelta = ACTOR_LEASE_TTL,
    clock: Clock = utc_now,
) -> ActorLease:
    """Extend an already-held lease. Preserves the fencing token: renewal is
    not a takeover, so ownership -- and the token that proves it -- does not
    change.

    Refuses (fail closed) if the presented token or process identity does not
    match the durable row exactly, which covers both a stale process trying
    to renew a lease it no longer holds and a corrupt/mismatched caller.
    """
    now = clock()
    expires_at = now + ttl
    with db.immediate() as connection:
        cursor = connection.execute(
            "UPDATE actor_leases SET expires_at = ?, renewed_at = ? "
            "WHERE actor_id = ? AND process_identity = ? AND fencing_token = ?",
            (expires_at.isoformat(), now.isoformat(), actor_id, process_identity, fencing_token),
        )
        if cursor.rowcount == 0:
            raise Refusal(
                f"Cannot renew a lease on {actor_id!r} this process does not hold.",
                "Renewal preserves ownership; it does not grant it. The lease may "
                "have expired and been taken over, or the token presented is stale.",
                "sovereign-agent supervisor --root PATH --once",
                "Re-acquire the lease before continuing.",
                category="actor_lease_lost",
            )
    leased = current_actor_lease(db, actor_id)
    assert leased is not None
    return leased


def release_actor_lease(
    db: Database, actor_id: str, process_identity: str, fencing_token: int
) -> bool:
    """Give up this process's own hosting lease on `actor_id`, if it still
    holds it.

    Called at the natural end of `organization.run_assignment` -- the same
    place `release_execution_attempt` runs -- so a short-lived process (the
    ordinary CLI `run` command, one assignment per process invocation) does
    not keep the actor locked out for the rest of `ACTOR_LEASE_TTL` after it
    has already exited. A long-running process (the supervisor, or a CLI
    process invoked again moments later) simply re-acquires on its next
    call via `acquire_or_renew_actor_lease` -- cheap, since "no current
    lease" is the fast successful-acquisition path, not a Refusal.

    Compare-and-set, like every other write in this module: only removes
    the row if BOTH `process_identity` and `fencing_token` still match the
    durable one, so a process that already lost the lease to a takeover
    cannot release (and thereby clear) a DIFFERENT process's now-current
    lease out from under it. Returns whether anything was actually released.
    """
    with db.immediate() as connection:
        cursor = connection.execute(
            "DELETE FROM actor_leases WHERE actor_id = ? AND process_identity = ? "
            "AND fencing_token = ?",
            (actor_id, process_identity, fencing_token),
        )
    return cursor.rowcount == 1


def acquire_or_renew_actor_lease(
    db: Database,
    actor_id: str,
    process_identity: str,
    *,
    ttl: timedelta = ACTOR_LEASE_TTL,
    clock: Clock = utc_now,
) -> ActorLease:
    """The idiom `organization.run_assignment` actually needs: extend this
    process's own lease if it already holds one, or take a fresh one if not.

    `acquire_actor_lease` alone is not enough here -- its CAS only succeeds
    when no row exists or the existing row's lease has EXPIRED, so calling
    it a second time from a process that already holds a live lease on this
    actor (the ordinary shape of that process running a second assignment
    for the same actor before the first lease's TTL lapses) would fail with
    `actor_lease_held`, refusing a process to run its OWN actor's next
    assignment. This function checks who currently holds the lease first: if
    it is this exact `process_identity`, it renews (same token, extended
    expiry); otherwise it attempts a fresh acquisition, which correctly
    refuses if a DIFFERENT live process holds it, or succeeds if the lease
    is absent or expired.

    There is a real, unavoidable race between the read and the renew/acquire
    below -- another process could take over between them. That race is not
    a defect: whichever call (the renew or the fresh acquire) actually runs
    is itself a compare-and-set against the current row, so it still fails
    closed if the lease changed hands in between; this function's own
    "which branch to take" read is an optimization to avoid the common-case
    Refusal, not the enforcement itself.
    """
    current = current_actor_lease(db, actor_id)
    if current is not None and current.process_identity == process_identity:
        return renew_actor_lease(
            db, actor_id, process_identity, current.fencing_token, ttl=ttl, clock=clock
        )
    return acquire_actor_lease(db, actor_id, process_identity, ttl=ttl, clock=clock)


def current_execution_attempt(db: Database, assignment_id: str) -> ExecutionAttempt | None:
    row = db.connection.execute(
        "SELECT ea.* FROM execution_attempts ea "
        "JOIN assignments a ON a.current_execution_attempt = ea.id "
        "WHERE a.id = ?",
        (assignment_id,),
    ).fetchone()
    if row is None:
        return None
    return _attempt_from_row(row)


# A row written before migration 14 added this column (or, in principle,
# any other row this application never itself produces with a NULL here --
# fencing.acquire_execution_attempt always supplies a real integer) has no
# real binding to compare against. -1 can never equal a genuine token:
# lease_tokens is an AUTOINCREMENT counter starting at 1 and only ever
# increasing, so this sentinel always fails an equality check against a
# real lease's fencing_token -- fail-closed, not a crash on a legacy shape.
_NO_ACTOR_LEASE_BINDING = -1


def _attempt_from_row(row: sqlite3.Row) -> ExecutionAttempt:
    raw_lease_token = row["actor_lease_fencing_token"]
    return ExecutionAttempt(
        id=row["id"],
        assignment_id=row["assignment_id"],
        actor_id=row["actor_id"],
        process_identity=row["process_identity"],
        fencing_token=int(row["fencing_token"]),
        actor_lease_fencing_token=(
            int(raw_lease_token) if raw_lease_token is not None else _NO_ACTOR_LEASE_BINDING
        ),
        acquired_at=datetime.fromisoformat(row["acquired_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]),
        status=row["status"],
    )


def acquire_execution_attempt(
    db: Database,
    assignment_id: str,
    actor_id: str,
    process_identity: str,
    actor_lease_fencing_token: int,
    *,
    ttl: timedelta = EXECUTION_ATTEMPT_TTL,
    clock: Clock = utc_now,
) -> ExecutionAttempt:
    """Bind a fresh fencing token to one attempt at running `assignment_id`,
    itself bound to the actor lease the caller already holds.

    `actor_lease_fencing_token` is REQUIRED, no default: a caller must
    already hold a current, unexpired lease on `actor_id` (via
    `acquire_actor_lease`/`renew_actor_lease`, called by `organization.
    run_assignment` before anything else is touched -- the same
    validate-first slot Unit 7 established for `workspace_policy` and the
    symlink checks) before it may acquire an execution attempt at all. This
    is what connects the two CAS mechanisms: an execution attempt is not
    merely "no other attempt is live for this ONE assignment" -- it is
    "no other attempt is live for this assignment, acquired by a process
    that currently holds the actor's own hosting lease, right now." The
    presented token is re-verified against the durable `actor_leases` row
    inside this SAME `db.immediate()` transaction, not merely trusted from
    an earlier call -- a lease acquired moments ago and since taken over by
    a fresher process (a genuine race, not a hypothetical one) must not let
    a stale token still mint a valid execution attempt. Only once that
    check passes is the token recorded on the attempt row, both as the
    enforcement and as a durable, queryable fact of what was true at
    acquisition time.

    Called once per invocation, before the provider runs, inside the same
    `db.immediate()` transaction that moves the assignment to `RUNNING`
    (the caller, `organization.run_assignment`, does both together). Succeeds
    only when the assignment has no current attempt (`current_execution_
    attempt IS NULL`) -- the normal case for a fresh run -- or its current
    attempt has already expired, which is the shape a supervisor recovery
    leaves behind: the assignment is eligible to be retried as an explicit,
    governed act, never automatically.
    """
    now = clock()
    with db.immediate() as connection:
        lease_row = connection.execute(
            "SELECT fencing_token, expires_at FROM actor_leases WHERE actor_id = ?",
            (actor_id,),
        ).fetchone()
        lease_current = (
            lease_row is not None
            and int(lease_row["fencing_token"]) == actor_lease_fencing_token
            and lease_row["expires_at"] > now.isoformat()
        )
        if not lease_current:
            raise Refusal(
                f"{actor_id!r} does not currently hold a live lease with "
                f"fencing token {actor_lease_fencing_token}.",
                "An execution attempt may only be acquired by a process that "
                "still holds its actor's hosting lease at the moment of "
                "acquisition -- the presented token is checked against the "
                "durable actor_leases row inside this same transaction, not "
                "merely trusted from an earlier, possibly superseded call.",
                "sovereign-agent supervisor --root PATH --once",
                "Re-acquire the actor lease before retrying.",
                category="actor_lease_lost",
            )
        row = connection.execute(
            "SELECT a.current_execution_attempt AS attempt_id, ea.expires_at AS expires_at "
            "FROM assignments a LEFT JOIN execution_attempts ea "
            "ON ea.id = a.current_execution_attempt WHERE a.id = ?",
            (assignment_id,),
        ).fetchone()
        if row is None:
            raise Refusal(
                f"Assignment {assignment_id!r} does not exist.",
                "An execution attempt can only be acquired for a real assignment.",
                "sovereign-agent status",
                "Check the assignment id.",
                category="assignment_missing",
            )
        current_expires = row["expires_at"]
        still_live = current_expires is not None and current_expires > now.isoformat()
        if still_live:
            raise Refusal(
                f"Assignment {assignment_id!r} already has a live execution attempt.",
                "Only one execution attempt may be active for an assignment at a "
                "time -- a second invocation while the first has not expired would "
                "let two workers both believe they may run it.",
                "sovereign-agent status",
                "Wait for the current attempt to finish or expire.",
                category="execution_attempt_held",
            )
        token = _mint_token(db, "execution", clock)
        attempt_id = new_id("att")
        expires_at = now + ttl
        connection.execute(
            "INSERT INTO execution_attempts(id, assignment_id, actor_id, process_identity, "
            "fencing_token, actor_lease_fencing_token, acquired_at, expires_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                attempt_id,
                assignment_id,
                actor_id,
                process_identity,
                token,
                actor_lease_fencing_token,
                now.isoformat(),
                expires_at.isoformat(),
                "ACTIVE",
            ),
        )
        connection.execute(
            "UPDATE assignments SET current_execution_attempt = ? WHERE id = ?",
            (attempt_id, assignment_id),
        )
    attempt = current_execution_attempt(db, assignment_id)
    assert attempt is not None
    return attempt


def verify_execution_attempt(db: Database, assignment_id: str, attempt_id: str) -> bool:
    """True iff `attempt_id` is still the assignment's current attempt.

    This is the fence check the terminal transaction in `run_assignment`
    runs, atomically, before committing COMPLETED/BLOCKED/FAILED. It does not
    additionally check expiry: a worker that still holds the current attempt
    row is the one authorized to finish it, whether or not the TTL clock has
    technically ticked past `expires_at` -- expiry only matters for a
    *second* acquisition (`acquire_execution_attempt` above) or for the
    supervisor deciding whether to recover an assignment nobody is finishing.
    """
    row = db.connection.execute(
        "SELECT current_execution_attempt FROM assignments WHERE id = ?",
        (assignment_id,),
    ).fetchone()
    return row is not None and row["current_execution_attempt"] == attempt_id


def release_execution_attempt(
    connection: sqlite3.Connection, assignment_id: str, attempt_id: str, status: str
) -> None:
    """Clear the fence and mark the attempt's final status.

    Called inside the SAME transaction as the terminal write it accompanies
    -- both `run_assignment`'s own successful terminal commit and the
    supervisor's recovery commit call this with the connection they are
    already inside, never opening a second transaction. `status` is `"DONE"`
    for a worker's own successful terminal write, `"RECOVERED"` for a
    supervisor hard-kill recovery.
    """
    connection.execute(
        "UPDATE execution_attempts SET status = ? WHERE id = ? AND assignment_id = ?",
        (status, attempt_id, assignment_id),
    )
    connection.execute(
        "UPDATE assignments SET current_execution_attempt = NULL "
        "WHERE id = ? AND current_execution_attempt = ?",
        (assignment_id, attempt_id),
    )


def expired_execution_attempts(db: Database, clock: Clock = utc_now) -> list[ExecutionAttempt]:
    """Every ACTIVE attempt whose lease has expired -- the supervisor's worklist.

    An assignment shows up here only while `current_execution_attempt` still
    points at that (now-expired) row; once recovery clears the pointer the
    assignment stops appearing, which is what makes recovery idempotent to
    re-run.
    """
    now = clock()
    rows = db.connection.execute(
        "SELECT ea.* FROM execution_attempts ea "
        "JOIN assignments a ON a.current_execution_attempt = ea.id "
        "WHERE ea.status = 'ACTIVE' AND ea.expires_at <= ?",
        (now.isoformat(),),
    ).fetchall()
    return [_attempt_from_row(row) for row in rows]


def expired_actor_leases(db: Database, clock: Clock = utc_now) -> list[ActorLease]:
    """Every actor lease past its expiry -- reported by the supervisor, not acted on.

    Expiry alone is not a fault: the lease simply becomes acquirable again by
    the next `acquire_actor_lease` call, lazily, exactly like a mailbox claim.
    This is read-only bookkeeping so a supervisor tick can say truthfully
    what it observed.
    """
    now = clock()
    rows = db.connection.execute(
        "SELECT * FROM actor_leases WHERE expires_at <= ?", (now.isoformat(),)
    ).fetchall()
    leases = []
    for row in rows:
        leases.append(
            ActorLease(
                actor_id=row["actor_id"],
                process_identity=row["process_identity"],
                fencing_token=int(row["fencing_token"]),
                acquired_at=datetime.fromisoformat(row["acquired_at"]),
                expires_at=datetime.fromisoformat(row["expires_at"]),
                renewed_at=datetime.fromisoformat(row["renewed_at"]),
            )
        )
    return leases
