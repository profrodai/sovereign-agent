"""Instructor transfer cases exercise the actual copied runtime, with independent answers."""

import json
import tempfile
from pathlib import Path

from reference_organizations.store.agent import seed_lucy
from sovereign_agent.database import Database

with tempfile.TemporaryDirectory(prefix="lucy-transfer-") as directory:
    state = Path(directory)
    db = Database(state / "agent.sqlite")
    seed_lucy(db)
    import hashlib

    from sovereign_agent.assistant_service import backup, health, restore
    from sovereign_agent.assistant_work import claim, enqueue

    enqueue(db, "hidden", "trial", "Brief")
    snapshot = backup(db, state / "copy.sqlite")
    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    for _ in range(2):
        before = db.path.with_suffix(".authority").read_text()
        restore(db, snapshot)
        assert health(db)["paused"] is True and claim(db, "hidden-worker") is None
        assert db.path.with_suffix(".authority").read_text() != before
        assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == digest
    for bad in (db.path, state / "missing.sqlite"):
        try:
            restore(db, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid restore input")
    assert health(db)["paused"] is True
    db.close()
print(json.dumps({"passed": True}))
