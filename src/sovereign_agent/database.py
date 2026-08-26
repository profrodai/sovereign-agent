"""SQLite operational ledger: WAL, foreign keys, forward-only migrations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

MIGRATION_1 = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outcomes (
    id TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sows (
    id TEXT PRIMARY KEY,
    outcome_id TEXT NOT NULL,
    record TEXT NOT NULL,
    FOREIGN KEY(outcome_id) REFERENCES outcomes(id)
);
CREATE TABLE IF NOT EXISTS rulings (
    id TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS actors (
    id TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    sow_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    record TEXT NOT NULL,
    FOREIGN KEY(sow_id) REFERENCES sows(id),
    FOREIGN KEY(actor_id) REFERENCES actors(id)
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    recipient TEXT NOT NULL,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS receipts (
    id TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS acceptance (
    outcome_id TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
    sku TEXT PRIMARY KEY,
    on_hand INTEGER NOT NULL,
    reserved INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cash_entries (
    id TEXT PRIMARY KEY,
    amount_cents INTEGER NOT NULL,
    record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    dedupe_key TEXT NOT NULL UNIQUE,
    record TEXT NOT NULL
);
"""

MIGRATION_2 = """
-- Append-only enforcement lives at the database boundary, not in Python habit.
-- Without these, `UPDATE events` and `DELETE FROM events` both succeed.
CREATE TRIGGER IF NOT EXISTS events_no_update
BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'events are append-only: update refused');
END;
CREATE TRIGGER IF NOT EXISTS events_no_delete
BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'events are append-only: delete refused');
END;

-- Evidence must be bound to what it proves. Columns are indexed rather than
-- buried in the JSON record so acceptance can query bindings directly.
-- REFERENCES on ALTER ADD COLUMN IS enforced by SQLite: a fabricated
-- outcome id is refused by the database, not merely by Python.
ALTER TABLE evidence ADD COLUMN outcome_id TEXT REFERENCES outcomes(id);
ALTER TABLE evidence ADD COLUMN check_id TEXT NOT NULL DEFAULT '';
ALTER TABLE evidence ADD COLUMN success INTEGER NOT NULL DEFAULT 0;
-- Digest of the exact inputs the check read. An event counter cannot detect a
-- silent UPDATE to inventory, so staleness is measured over the read state itself.
ALTER TABLE evidence ADD COLUMN state_digest TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS evidence_binding
    ON evidence(outcome_id, check_id);
"""

MIGRATION_3 = """
-- `recursive_triggers` is a PER-CONNECTION pragma, not a property of the schema.
-- The BEFORE DELETE guard therefore only stopped `INSERT OR REPLACE` on
-- connections the application itself opened. Anyone using a plain `sqlite3`
-- shell -- including a learner following Chapter 1 -- could silently overwrite
-- an event and leave the row count unchanged.
--
-- This guard needs no pragma: it refuses an INSERT whose id already exists, so
-- append-only holds from ANY client. Enforcement now matches the claim.
CREATE TRIGGER IF NOT EXISTS events_no_replace
BEFORE INSERT ON events
WHEN EXISTS (SELECT 1 FROM events WHERE id = NEW.id)
BEGIN
    SELECT RAISE(ABORT, 'events are append-only: replace refused');
END;
"""


MIGRATION_4 = """
-- A preflight scan of the event log is not an idempotency key: two callers can
-- both pass the scan before either writes, and both then order stock. The
-- database has to be the one saying "this already happened".
CREATE TABLE IF NOT EXISTS effect_keys (
    key TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


MIGRATION_5 = """
-- Claiming a lease by reading a JSON blob, deciding in Python, then writing the
-- blob back is a read-then-write race: two workers both read NEW and both win.
-- A compare-and-set needs the state in a column the UPDATE can test.
ALTER TABLE messages ADD COLUMN state TEXT NOT NULL DEFAULT 'NEW';
ALTER TABLE messages ADD COLUMN claim_owner TEXT;
ALTER TABLE messages ADD COLUMN claim_expires_at TEXT;
UPDATE messages SET
    state = COALESCE(json_extract(record, '$.state'), 'NEW'),
    claim_owner = json_extract(record, '$.claim_owner'),
    claim_expires_at = json_extract(record, '$.claim_expires_at');
"""


MIGRATION_6 = """
-- A review that leaves no record is a claim nobody can check later. Acceptance
-- could not consult reviews because there was nothing durable to consult.
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    sow_id TEXT NOT NULL,
    outcome_id TEXT NOT NULL,
    reviewer_actor_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    record TEXT NOT NULL,
    FOREIGN KEY(sow_id) REFERENCES sows(id),
    FOREIGN KEY(outcome_id) REFERENCES outcomes(id)
);
CREATE INDEX IF NOT EXISTS reviews_by_outcome ON reviews(outcome_id);
-- Receipts must name the execution they describe, or they cannot be tied to it.
ALTER TABLE receipts ADD COLUMN assignment_id TEXT;
ALTER TABLE receipts ADD COLUMN status TEXT NOT NULL DEFAULT '';
"""


MIGRATION_7 = """
-- effect_keys held ONE concatenated string while the code called it a key on
-- (assignment, sku). Structured columns with a composite constraint make the
-- schema say what the docstring claimed.
CREATE TABLE IF NOT EXISTS effects (
    id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    subject TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(assignment_id, kind, subject),
    FOREIGN KEY(assignment_id) REFERENCES assignments(id)
);

-- A verification is a BATCH of evidence produced by one run of the checks.
-- Without it, review binds to "whatever evidence existed" and acceptance uses
-- "whatever evidence exists now", and nothing forces those to be the same set.
CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    outcome_id TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    aggregate_digest TEXT NOT NULL,
    passed INTEGER NOT NULL,
    record TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(outcome_id) REFERENCES outcomes(id)
);
CREATE INDEX IF NOT EXISTS verifications_by_outcome ON verifications(outcome_id);

ALTER TABLE evidence ADD COLUMN verification_id TEXT REFERENCES verifications(id);
ALTER TABLE reviews ADD COLUMN verification_id TEXT REFERENCES verifications(id);
"""


MIGRATION_8 = """
-- Sparring's unprompted find: Receipt.assignment_id defaulted to "",
-- _latest_assignment_id returned "", and this column was nullable -- "the
-- performer who never worked" in a new costume. It refused every way Sparring
-- pushed it, but only via guards three layers from the default. SQLite cannot
-- add a NOT NULL constraint in place, so this rebuilds the table.
CREATE TABLE receipts_v2 (
    id TEXT PRIMARY KEY,
    record TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    status TEXT NOT NULL,
    CHECK (assignment_id <> '')
);
INSERT INTO receipts_v2(id, record, assignment_id, status)
    SELECT id, record, COALESCE(NULLIF(assignment_id, ''), 'asg_unattributed_legacy'),
           COALESCE(status, '')
    FROM receipts;
DROP TABLE receipts;
ALTER TABLE receipts_v2 RENAME TO receipts;
CREATE INDEX IF NOT EXISTS receipts_by_assignment ON receipts(assignment_id);
"""


MIGRATION_9 = """
-- The effect edge existed but could only be followed through the JSON payload,
-- so acceptance never followed it: the authorization graph and the acceptance
-- graph met at the SUBJECT (any two outcomes about one SKU shared effects)
-- rather than at the execution. A structured FK makes the edge queryable.
ALTER TABLE effects ADD COLUMN outcome_id TEXT REFERENCES outcomes(id);
UPDATE effects SET outcome_id = json_extract(payload, '$.outcome_id')
    WHERE outcome_id IS NULL;
CREATE INDEX IF NOT EXISTS effects_by_outcome ON effects(outcome_id, assignment_id);
"""


MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, MIGRATION_1),
    (2, MIGRATION_2),
    (3, MIGRATION_3),
    (4, MIGRATION_4),
    (5, MIGRATION_5),
    (6, MIGRATION_6),
    (7, MIGRATION_7),
    (8, MIGRATION_8),
    (9, MIGRATION_9),
)


def _split_statements(script: str) -> list[str]:
    """Split a migration into executable statements.

    `sqlite3` refuses more than one statement per `execute()`, and migrations
    contain CREATE TRIGGER bodies with internal semicolons. `sqlite3.complete_statement`
    knows where a statement genuinely ends, including inside BEGIN ... END.
    """
    statements: list[str] = []
    buffer = ""
    for line in script.splitlines(keepends=True):
        if not line.strip() or line.lstrip().startswith("--"):
            continue
        buffer += line
        if sqlite3.complete_statement(buffer):
            statements.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        statements.append(buffer.strip())
    return statements


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        # Without recursive triggers, `INSERT OR REPLACE` deletes the old row
        # WITHOUT firing the BEFORE DELETE guard, silently defeating append-only.
        self.connection.execute("PRAGMA recursive_triggers = ON")
        self.migrate()

    def applied_versions(self) -> set[int]:
        """Versions already recorded. Empty when the ledger table does not exist yet."""
        try:
            rows = self.connection.execute("SELECT version FROM schema_migrations").fetchall()
        except sqlite3.OperationalError:
            return set()
        return {int(row["version"]) for row in rows}

    def migrate(self) -> None:
        """Apply pending migrations in order. Forward-only; never downgrades.

        Each migration's DDL **and** its version stamp go inside one explicit
        `BEGIN IMMEDIATE`, so a failure part way through leaves the database
        exactly as it was. SQLite rolls DDL back like any other statement.

        This deliberately does not use `executescript()`. That helper COMMITs
        any open transaction before it runs, which silently defeated the
        rollback this docstring promises: a migration that created a table and
        then hit invalid SQL left the table behind, unstamped, so reopening
        re-ran it and failed forever.
        """
        applied = self.applied_versions()
        for version, script in MIGRATIONS:
            if version in applied:
                continue
            previous = self.connection.isolation_level
            self.connection.isolation_level = None
            try:
                self.connection.execute("BEGIN IMMEDIATE")
                for statement in _split_statements(script):
                    self.connection.execute(statement)
                self.connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) "
                    "VALUES (?, datetime('now'))",
                    (version,),
                )
                self.connection.execute("COMMIT")
            except Exception:
                self.connection.execute("ROLLBACK")
                raise
            finally:
                self.connection.isolation_level = previous

    @contextmanager
    def immediate(self) -> Iterator[sqlite3.Connection]:
        """A write transaction that takes its lock UP FRONT.

        `BEGIN IMMEDIATE` acquires the reserved lock before any statement runs,
        so two connections cannot both read a row, both decide to act, and both
        write. Deferred transactions -- SQLite's default -- allow exactly that.
        """
        previous = self.connection.isolation_level
        self.connection.isolation_level = None
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            yield self.connection
            self.connection.execute("COMMIT")
        except Exception:
            self.connection.execute("ROLLBACK")
            raise
        finally:
            self.connection.isolation_level = previous

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def get(self, table: str, key: str, value: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            f"SELECT record FROM {table} WHERE {key} = ?", (value,)
        ).fetchone()
        return json.loads(row["record"]) if row else None

    def put(
        self,
        table: str,
        record_id: str,
        record: dict[str, Any],
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = json.dumps(record, default=str)
        if table == "outcomes":
            self.connection.execute(
                "INSERT OR REPLACE INTO outcomes(id, record) VALUES (?, ?)",
                (record_id, payload),
            )
        elif table == "sows":
            self.connection.execute(
                "INSERT OR REPLACE INTO sows(id, outcome_id, record) VALUES (?, ?, ?)",
                (record_id, extra["outcome_id"] if extra else record["outcome_id"], payload),
            )
        elif table == "actors":
            self.connection.execute(
                "INSERT OR REPLACE INTO actors(id, record) VALUES (?, ?)",
                (record_id, payload),
            )
        elif table == "assignments":
            self.connection.execute(
                "INSERT OR REPLACE INTO assignments(id, sow_id, actor_id, record) "
                "VALUES (?, ?, ?, ?)",
                (record_id, record["sow_id"], record["actor_id"], payload),
            )
        elif table == "messages":
            self.connection.execute(
                "INSERT OR REPLACE INTO messages(id, recipient, record, state, claim_owner, "
                "claim_expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record_id,
                    record["recipient"],
                    payload,
                    record.get("state", "NEW"),
                    record.get("claim_owner"),
                    record.get("claim_expires_at"),
                ),
            )
        else:
            self.connection.execute(
                f"INSERT OR REPLACE INTO {table}(id, record) VALUES (?, ?)",
                (record_id, payload),
            )

    def put_serialized(self, table: str, record_id: str, payload: str) -> None:
        """Persist already-canonical JSON without changing its bytes."""
        json.loads(payload)
        if table != "receipts":
            raise ValueError("put_serialized is restricted to canonical receipts")
        record = json.loads(payload)
        self.connection.execute(
            "INSERT OR REPLACE INTO receipts(id, record, assignment_id, status) "
            "VALUES (?, ?, ?, ?)",
            (record_id, payload, record.get("assignment_id"), record.get("status", "")),
        )

    def close(self) -> None:
        self.connection.close()
