"""The pilot-start mechanism (Unit 11, governing ruling Holding 1).

Lives outside `sovereign_agent`'s own budget, matching `pulse_gate.py`'s own
placement: this is Store-specific domain logic ("start a 30-day Store
pilot") built on top of core primitives (`Database`, `append_event`), not a
general organizational mechanism `sovereign_agent` itself needs to know
about.

Builds and proves the mechanism. Never invokes it against the real named
pilot organization -- that is a separate, later, separately-authorized act
(see the governing SOW section 4 and "Authorization"), entirely outside this
unit's own implementation. Chapter 12's own exercise invokes this module
only against a disposable, exercise-scoped identity.

One durable act, atomically, in ONE `db.immediate()` transaction:

1. A first-class, queryable `pilots` row (migration 16) -- structured
   columns, not unindexed JSON, matching the discipline migration 15 already
   established for Pulse attribution.
2. An append-only `pilot.started` event.

Idempotent replay and fail-closed refusal are BOTH plain `INSERT`s racing a
constraint at the SQLite boundary -- never a preflight `SELECT` a concurrent
caller could slip past, the same discipline `create_pulse_work`'s own
`pulse_wake_decisions` INSERT already uses:

- `pilots.pilot_id` is the CAS key for IDEMPOTENT REPLAY: inserting the SAME
  pilot_id twice collides on `pilots`' own PRIMARY KEY. The second caller
  reads back the FIRST caller's own row and returns it, `idempotent_replay
  = True` -- never a second row, never a second event.
- `active_pilot`'s own singleton PRIMARY KEY (always 1) is the CAS key for
  REFUSING AN INCOMPATIBLE PILOT: once one pilot_id occupies that slot, a
  DIFFERENT pilot_id's own `active_pilot` INSERT collides, and this
  function raises `Refusal` -- which rolls back the WHOLE transaction
  (`db.immediate()`'s own contract), so the `pilots` row this attempt tried
  to insert is rolled back with it. Nothing partial is ever left behind.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.events import append_event
from sovereign_agent.ids import utc_now


@dataclass(frozen=True)
class PilotRecord:
    """A pilot-start act's own durable row, read back after the fact."""

    pilot_id: str
    started_at: str
    store_org_id: str
    pilot_profile_id: str
    evidence_namespace: str
    idempotent_replay: bool


def _read_pilot(db: Database, pilot_id: str) -> PilotRecord:
    row = db.connection.execute(
        "SELECT pilot_id, started_at, store_org_id, pilot_profile_id, evidence_namespace "
        "FROM pilots WHERE pilot_id = ?",
        (pilot_id,),
    ).fetchone()
    if row is None:
        raise Refusal(
            f"No pilot record exists for {pilot_id!r}.",
            "A replay must resolve to an existing durable row.",
            "sqlite3 .sovereign/organization.db 'select * from pilots'",
            "Call start_pilot again with a fresh pilot_id.",
        )
    return PilotRecord(
        pilot_id=str(row["pilot_id"]),
        started_at=str(row["started_at"]),
        store_org_id=str(row["store_org_id"]),
        pilot_profile_id=str(row["pilot_profile_id"]),
        evidence_namespace=str(row["evidence_namespace"]),
        idempotent_replay=True,
    )


def start_pilot(
    db: Database,
    *,
    pilot_id: str,
    store_org_id: str,
    pilot_profile_id: str,
    evidence_namespace: str,
) -> PilotRecord:
    """Start a pilot, or safely replay an identical prior start.

    Refuses (fail closed) when a DIFFERENT pilot is already active. Proven
    with real, separate database connections in `tests/test_pilot.py` --
    idempotent replay, incompatible-pilot refusal, and terminal atomicity
    are each their own test, plus a genuine two-connection concurrency race
    for both the same-id and different-id cases.
    """
    now = utc_now()
    try:
        with db.immediate() as connection:
            try:
                connection.execute(
                    "INSERT INTO pilots(pilot_id, started_at, store_org_id, "
                    "pilot_profile_id, evidence_namespace, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        pilot_id,
                        now.isoformat(),
                        store_org_id,
                        pilot_profile_id,
                        evidence_namespace,
                        now.isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as error:
                if "pilots" not in str(error):
                    raise
                # Same pilot_id already durable. Read the canonical row
                # FIRST and compare the identity-defining fields before
                # trusting this as a replay: a colliding pilot_id whose
                # store_org_id/pilot_profile_id/evidence_namespace differ
                # from the durable row is a DIFFERENT request that must
                # fail closed, never silently return someone else's data.
                existing = _read_pilot(db, pilot_id)
                if (
                    existing.store_org_id != store_org_id
                    or existing.pilot_profile_id != pilot_profile_id
                    or existing.evidence_namespace != evidence_namespace
                ):
                    raise Refusal(
                        f"Pilot {pilot_id!r} already exists with different identity.",
                        "A pilot_id collision is only a safe replay when "
                        "store_org_id, pilot_profile_id, and evidence_namespace "
                        "all match the durable row exactly; otherwise this is an "
                        "incompatible start under a reused id, not a replay.",
                        "sqlite3 .sovereign/organization.db 'select * from pilots'",
                        "Use a fresh pilot_id, or replay with the original request's "
                        "exact store_org_id/pilot_profile_id/evidence_namespace.",
                        category="pilot_identity_conflict",
                    ) from error
                return existing

            try:
                connection.execute(
                    "INSERT INTO active_pilot(slot_id, pilot_id) VALUES (1, ?)", (pilot_id,)
                )
            except sqlite3.IntegrityError as error:
                if "active_pilot" not in str(error):
                    raise
                # A DIFFERENT pilot already occupies the one active slot.
                # Raising here rolls back this WHOLE transaction -- the
                # `pilots` insert above is rolled back with it, so no
                # orphaned pilot row is ever left behind by a refused start.
                active = connection.execute(
                    "SELECT pilot_id FROM active_pilot WHERE slot_id = 1"
                ).fetchone()
                active_id = str(active["pilot_id"]) if active is not None else "<unknown>"
                raise Refusal(
                    f"Pilot {active_id!r} is already active.",
                    "Only one pilot may be active at a time; a second, "
                    "different pilot-start attempt fails closed rather "
                    "than silently proceeding or silently no-opping.",
                    "sqlite3 .sovereign/organization.db 'select * from active_pilot'",
                    "Use the active pilot's own identity, or wait for it to end.",
                    category="pilot_already_active",
                ) from error

            append_event(
                db,
                "pilot.started",
                {
                    "pilot_id": pilot_id,
                    "store_org_id": store_org_id,
                    "pilot_profile_id": pilot_profile_id,
                    "evidence_namespace": evidence_namespace,
                    "started_at": now.isoformat(),
                },
            )
    except Refusal:
        raise
    return PilotRecord(
        pilot_id=pilot_id,
        started_at=now.isoformat(),
        store_org_id=store_org_id,
        pilot_profile_id=pilot_profile_id,
        evidence_namespace=evidence_namespace,
        idempotent_replay=False,
    )


def active_pilot_id(db: Database) -> str | None:
    """The pilot_id presently occupying the one active slot, if any."""
    row = db.connection.execute("SELECT pilot_id FROM active_pilot WHERE slot_id = 1").fetchone()
    return str(row["pilot_id"]) if row is not None else None
