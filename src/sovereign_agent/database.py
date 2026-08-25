"""SQLite operational ledger: WAL, foreign keys, forward-only migrations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
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


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.migrate()

    def migrate(self) -> None:
        self.connection.executescript(SCHEMA)
        applied = {
            int(row["version"])
            for row in self.connection.execute("SELECT version FROM schema_migrations")
        }
        if 1 not in applied:
            self.connection.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (1, datetime('now'))"
            )
            self.connection.commit()

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
                "INSERT OR REPLACE INTO messages(id, recipient, record) VALUES (?, ?, ?)",
                (record_id, record["recipient"], payload),
            )
        else:
            self.connection.execute(
                f"INSERT OR REPLACE INTO {table}(id, record) VALUES (?, ?)",
                (record_id, payload),
            )

    def close(self) -> None:
        self.connection.close()
