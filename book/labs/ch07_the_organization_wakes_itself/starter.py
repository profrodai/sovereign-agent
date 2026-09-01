"""Starter for Chapter 7's manual Pulse transaction lab."""

from __future__ import annotations

import sqlite3
from pathlib import Path

STUDENT_TODO = True

# TODO(1): Add wake_decisions, work, and origins to SCHEMA. Which source
# identifier needs a UNIQUE constraint to make one decision canonical?

SCHEMA = """
CREATE TABLE inventory (
    sku TEXT PRIMARY KEY,
    on_hand INTEGER NOT NULL,
    reserved INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL
);
CREATE TABLE events (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE signals (
    id TEXT PRIMARY KEY,
    source_event_id TEXT NOT NULL REFERENCES events(id),
    sku TEXT NOT NULL
);
"""


def connect(path: Path) -> sqlite3.Connection:
    """Open one contender's independent connection."""
    connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def manual_tick(connection: sqlite3.Connection, signal_id: str) -> tuple[str | None, bool]:
    """Return (canonical_work_id, created_by_this_call)."""
    # TODO(2): Acquire the write lock before re-reading available inventory.
    # A gate result observed before this transaction is only historical data.
    # TODO(3): Create decision, work, Pulse event, and origin in one transaction.
    # On replay or a lost race, return the already-canonical work id with False.
    raise NotImplementedError("implement one canonical manual Pulse tick")


def exercise(root: Path) -> dict[str, object]:
    """Build and probe a revalidated, canonical manual Pulse tick.

    Required observations are documented in README.md and expected.json.
    Use two independent SQLite connections for the contention experiment.
    """
    # TODO(4): Seed a formerly qualifying signal, resolve its condition, and
    # prove transaction-time revalidation creates no work.
    # TODO(5): Race two threads using separate connections, then query the
    # complete signal -> event -> decision -> work -> Pulse-event chain.
    raise NotImplementedError("assemble the Chapter 7 experiments")
