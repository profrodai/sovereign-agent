# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 4 learner file: durable state for Lucy's shop, built on SQLite.

The completed comparison copy of what the chapter builds. Save your own version at this path in
your checkout; the Chapter 4 checkpoint loads it. Python 3.12 or newer (Colab runs 3.13): the
driver's ``autocommit=True`` mode lets this file own every transaction boundary explicitly.

The invariant the store keeps: for every product, the stock row equals the sum of that product's
events. Every change is one event and one stock update, committed together or not at all.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class StoreError(Exception):
    """A state change the store refused. The database is unchanged."""


class EventConflictError(StoreError):
    """An event identity that already exists with different content."""


class UnsupportedSchemaError(StoreError):
    """A database written by a newer program than this one."""


class NestedTransactionError(StoreError):
    """A transaction opened while another is still open on the same store."""


@dataclass(frozen=True)
class StockEvent:
    """One change to one product's stock, in whole tubs. Its identity never changes meaning."""

    event_id: str
    sku: str
    delta: int
    reason: str

    def payload(self) -> str:
        """The event's content as canonical text, so equal events compare equal byte for byte."""
        return json.dumps(
            {"sku": self.sku, "delta": self.delta, "reason": self.reason},
            sort_keys=True,
            separators=(",", ":"),
        )


# Each migration moves the schema from version k - 1 to version k, and runs inside the same
# transaction that records version k: a crash leaves either the old version or the new one.
MIGRATIONS: dict[int, tuple[str, ...]] = {
    1: (
        "CREATE TABLE stock ( sku TEXT PRIMARY KEY, tubs INTEGER NOT NULL CHECK (tubs >= 0))",
        "CREATE TABLE events ("
        " event_id TEXT PRIMARY KEY,"
        " sku TEXT NOT NULL,"
        " delta INTEGER NOT NULL,"
        " payload TEXT NOT NULL)",
        "CREATE TRIGGER events_no_update BEFORE UPDATE ON events"
        " BEGIN SELECT RAISE(ABORT, 'events are append-only'); END",
        "CREATE TRIGGER events_no_delete BEFORE DELETE ON events"
        " BEGIN SELECT RAISE(ABORT, 'events are append-only'); END",
    ),
    2: ("ALTER TABLE events ADD COLUMN reason TEXT NOT NULL DEFAULT 'unrecorded'",),
}
SCHEMA_VERSION = max(MIGRATIONS)


class StateStore:
    """Lucy's stock and its event log in one SQLite file.

    The store owns its connection and every transaction boundary. Callers get ``immediate()``
    for a group of writes and ``apply()`` for the one change the shop makes: an event plus its
    stock update.
    """

    def __init__(self, path: str | Path, *, busy_timeout_s: float = 1.0) -> None:
        self.path = Path(path)
        # autocommit=True: the driver never opens a transaction on its own. Every BEGIN, COMMIT
        # and ROLLBACK below is ours, so what is atomic is decided here, not by a default.
        self.connection = sqlite3.connect(self.path, autocommit=True, timeout=busy_timeout_s)
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        self._open = False

    def close(self) -> None:
        self.connection.close()

    @contextmanager
    def immediate(self) -> Iterator[sqlite3.Connection]:
        """One write transaction: commit on success, roll back and re-raise on any exception."""
        if self._open:
            raise NestedTransactionError("a transaction is already open on this store")
        # IMMEDIATE takes the write lock now, so a busy database fails here, before any work.
        self.connection.execute("BEGIN IMMEDIATE")
        self._open = True
        try:
            yield self.connection
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise
        else:
            try:
                self.connection.execute("COMMIT")
            except BaseException:
                # A failed commit is not a success: undo what is still pending, then report it.
                if self.connection.in_transaction:
                    self.connection.execute("ROLLBACK")
                raise
        finally:
            self._open = False

    def schema_version(self) -> int:
        exists = self.connection.execute(
            "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'meta'"
        ).fetchone()
        if not exists:
            return 0
        row = self.connection.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        return int(row[0]) if row else 0

    def initialize(self) -> tuple[int, int]:
        """Bring the schema to SCHEMA_VERSION. Refuse a newer database before changing anything."""
        with self.immediate() as db:
            before = self.schema_version()
            if before > SCHEMA_VERSION:
                raise UnsupportedSchemaError(
                    f"database is version {before}; this program supports up to {SCHEMA_VERSION}"
                )
            db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER)")
            for version in range(before + 1, SCHEMA_VERSION + 1):
                for statement in MIGRATIONS[version]:
                    db.execute(statement)
            db.execute(
                "INSERT INTO meta (key, value) VALUES ('schema_version', ?)"
                " ON CONFLICT (key) DO UPDATE SET value = excluded.value",
                (SCHEMA_VERSION,),
            )
        return before, SCHEMA_VERSION

    def apply(self, event: StockEvent, *, between: Callable[[], None] | None = None) -> str:
        """Record an event and its stock change together. Returns "applied" or "duplicate".

        ``between`` runs after the event is written and before the stock is updated; tests use
        it to fail at the worst moment. Inside the transaction, that failure leaves nothing.
        """
        payload = event.payload()
        with self.immediate() as db:
            row = db.execute(
                "SELECT payload FROM events WHERE event_id = ?", (event.event_id,)
            ).fetchone()
            if row is not None:
                if row[0] == payload:
                    return "duplicate"
                raise EventConflictError(
                    f"event {event.event_id} already exists with other content"
                )
            db.execute(
                "INSERT INTO events (event_id, sku, delta, payload, reason) VALUES (?, ?, ?, ?, ?)",
                (event.event_id, event.sku, event.delta, payload, event.reason),
            )
            if between is not None:
                between()
            db.execute(
                "INSERT INTO stock (sku, tubs) VALUES (?, ?)"
                " ON CONFLICT (sku) DO UPDATE SET tubs = tubs + excluded.tubs",
                (event.sku, event.delta),
            )
        return "applied"

    def stock(self) -> dict[str, int]:
        return dict(self.connection.execute("SELECT sku, tubs FROM stock ORDER BY sku"))


def observe(path: str | Path) -> dict[str, object]:
    """What a separate reader sees on disk: stock, events, per-product event sums, and version.

    It opens its own connection and never calls the store's methods, so it cannot inherit a
    mistake the store makes about its own state.
    """
    reader = sqlite3.connect(path, autocommit=True)
    try:
        stock = dict(reader.execute("SELECT sku, tubs FROM stock ORDER BY sku"))
        events = [row[0] for row in reader.execute("SELECT event_id FROM events ORDER BY rowid")]
        sums = dict(reader.execute("SELECT sku, SUM(delta) FROM events GROUP BY sku ORDER BY sku"))
        version = reader.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[
            0
        ]
    finally:
        reader.close()
    return {"stock": stock, "events": events, "sums": sums, "version": version}
