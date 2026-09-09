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
    from sovereign_agent.assistant_work import schedule, tick

    schedule(db, "transfer", "trial", "Brief me", first_due=200, interval_seconds=7)
    assert tick(db, now=199) == []
    assert len(tick(db, now=235)) == 1
    assert tick(db, now=235) == []
    assert db.connection.execute("SELECT next_due FROM assistant_jobs").fetchone()[0] == 242
    assert len(tick(db, now=1000)) == 1
    assert tick(db, now=1000) == []
    assert db.connection.execute("SELECT next_due FROM assistant_jobs").fetchone()[0] == 1005
    with db.immediate() as c:
        c.execute("UPDATE assistant_control SET paused=1")
    assert tick(db, now=2000) == []
    assert db.connection.execute("SELECT count(*) FROM assistant_work").fetchone()[0] == 2
    db.close()
print(json.dumps({"passed": True}))
