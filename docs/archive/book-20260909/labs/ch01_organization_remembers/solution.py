from __future__ import annotations

import json
import sqlite3
from pathlib import Path

STUDENT_TODO = False


def _render(row: sqlite3.Row) -> bytes:
    return (json.dumps({"id": row["id"], "state": row["state"]}, sort_keys=True) + "\n").encode()


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    database = root / "ledger.db"
    projection = root / "outcome.json"
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS outcomes (id TEXT PRIMARY KEY, state TEXT NOT NULL)"
    )

    rolled_back = False
    try:
        with connection:
            connection.execute("INSERT INTO outcomes VALUES ('out-failed', 'ACTIVE')")
            raise RuntimeError("simulated fault between writes")
    except RuntimeError:
        rolled_back = (
            connection.execute("SELECT COUNT(*) FROM outcomes WHERE id = 'out-failed'").fetchone()[
                0
            ]
            == 0
        )

    with connection:
        connection.execute("INSERT OR IGNORE INTO outcomes VALUES ('out-1', 'ACTIVE')")
    row = connection.execute("SELECT id, state FROM outcomes WHERE id = 'out-1'").fetchone()
    expected = _render(row)
    projection.write_bytes(expected)
    projection.write_text('{"id": "out-1", "state": "ACCEPTED"}\n', encoding="utf-8")

    before_verify = projection.read_bytes()
    drift_detected = before_verify != _render(row)
    verifier_was_pure = projection.read_bytes() == before_verify
    projection.write_bytes(_render(row))
    reconciled = projection.read_bytes() == _render(row)
    ledger_rows = connection.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
    connection.close()
    return {
        "rollback_removed_partial_fact": rolled_back,
        "drift_detected": drift_detected,
        "verifier_was_pure": verifier_was_pure,
        "reconciled": reconciled,
        "ledger_rows": ledger_rows,
        "authoritative_state": "ACTIVE",
    }
