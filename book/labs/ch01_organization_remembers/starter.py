from __future__ import annotations

import json
import sqlite3
from pathlib import Path

STUDENT_TODO = True
OUTCOME_SCHEMA = "CREATE TABLE IF NOT EXISTS outcomes (id TEXT PRIMARY KEY, state TEXT NOT NULL)"


def render_projection(record: dict[str, str]) -> bytes:
    """Render expected projection bytes without touching the filesystem."""
    # TODO(1): Keep rendering deterministic so verification can compare bytes.
    return (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")


def open_ledger(path: Path) -> sqlite3.Connection:
    """Open the authoritative ledger with named-column access."""
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    # TODO(2): Apply OUTCOME_SCHEMA idempotently without deleting prior authority.
    return connection


def exercise(root: Path) -> dict[str, object]:
    """Separate an authoritative ledger from a derived projection."""
    # TODO(3): Prove rollback, pure drift detection, and explicit reconciliation.
    raise NotImplementedError("Implement rollback, pure verification, and reconciliation")
