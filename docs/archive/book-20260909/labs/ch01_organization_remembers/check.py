from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    result = target_module.exercise(root)
    repeated = target_module.exercise(root)
    assert result == {
        "rollback_removed_partial_fact": True,
        "drift_detected": True,
        "verifier_was_pure": True,
        "reconciled": True,
        "ledger_rows": 1,
        "authoritative_state": "ACTIVE",
    }
    assert repeated == result
    projection = json.loads((root / "outcome.json").read_text(encoding="utf-8"))
    with sqlite3.connect(root / "ledger.db") as connection:
        rows = connection.execute("SELECT id, state FROM outcomes").fetchall()
    assert rows == [("out-1", "ACTIVE")]
    assert projection == {"id": "out-1", "state": "ACTIVE"}
    return {
        "drift_was_observed_before_repair": True,
        "projection_matches_ledger_after_reconcile": True,
        "rollback_orphans": 0,
    }
