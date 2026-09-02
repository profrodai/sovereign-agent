"""Heartbeat: a durable liveness record, deliberately separate from work.

A heartbeat proves exactly one thing: the process that recorded it was alive
at that moment, with the database reachable. It does NOT prove that any work
progressed, that the Pulse fired, or that the organization is healthy — and
this module never pretends otherwise.

Two deliberate separations keep that claim honest:

- Heartbeats live in their own append-only table, NOT in the `events` ledger.
  The ledger records governed work; a liveness tick recorded there would let
  "the process is running" masquerade as "something happened". Presence is
  not behavior.
- This is NOT the Pulse. The book's chapters use "heartbeat" informally for
  the organization waking ITSELF to create work (`sovereign-agent pulse`,
  Unit 9). This mechanism is the opposite direction: it creates no work, ever
  — it only lets an outside watcher ask "was this organization's runtime
  alive recently?" and get a durable, timestamped answer instead of an
  inference from silence.

Staleness is likewise stated precisely: a fresh beat proves liveness at its
timestamp; the ABSENCE of a fresh beat proves only that no beat was recorded
— the recorder may be dead, wedged, or merely cut off from the database. The
verdict names which claim it is making.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.organization import Organization

#: Default staleness threshold, in seconds. Watchers may override per call.
DEFAULT_STALE_AFTER_SECONDS = 900


@dataclass(frozen=True)
class HeartbeatStatus:
    """The last recorded beat, and the honest verdict it supports."""

    verdict: str  # "ALIVE" | "STALE" | "NO_BEATS"
    last_beat_id: str | None
    last_beat_at: datetime | None
    source: str | None
    age_seconds: float | None
    stale_after_seconds: int

    def line(self) -> str:
        if self.verdict == "NO_BEATS":
            return "NO_BEATS: no heartbeat has ever been recorded here"
        assert self.last_beat_at is not None and self.age_seconds is not None
        stamp = self.last_beat_at.isoformat()
        base = (
            f"last beat {self.last_beat_id} from {self.source!r} at {stamp}, "
            f"{self.age_seconds:.0f}s ago"
        )
        if self.verdict == "ALIVE":
            return f"ALIVE: {base} (threshold {self.stale_after_seconds}s)"
        return (
            f"STALE: {base} exceeds {self.stale_after_seconds}s -- no beat was "
            "recorded in the window; that proves silence, not death"
        )


def record_heartbeat(org: Organization, source: str = "cli") -> str:
    """Append one liveness record and return its id.

    A plain INSERT into an append-only table: no update path exists, so the
    history of beats is a record, not a mutable "last seen" field.
    """
    beat_id = new_id("beat")
    with org.db.transaction():
        org.db.connection.execute(
            "INSERT INTO heartbeats (beat_id, source, created_at) VALUES (?, ?, ?)",
            (beat_id, source, utc_now().isoformat()),
        )
    return beat_id


def heartbeat_status(
    org: Organization, stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS
) -> HeartbeatStatus:
    """Read the newest beat and judge it against the threshold."""
    row = org.db.connection.execute(
        "SELECT beat_id, source, created_at FROM heartbeats"
        " ORDER BY created_at DESC, beat_id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return HeartbeatStatus(
            verdict="NO_BEATS",
            last_beat_id=None,
            last_beat_at=None,
            source=None,
            age_seconds=None,
            stale_after_seconds=stale_after_seconds,
        )
    last_at = datetime.fromisoformat(row["created_at"])
    age = (utc_now() - last_at).total_seconds()
    verdict = "ALIVE" if age <= stale_after_seconds else "STALE"
    return HeartbeatStatus(
        verdict=verdict,
        last_beat_id=row["beat_id"],
        last_beat_at=last_at,
        source=row["source"],
        age_seconds=age,
        stale_after_seconds=stale_after_seconds,
    )
