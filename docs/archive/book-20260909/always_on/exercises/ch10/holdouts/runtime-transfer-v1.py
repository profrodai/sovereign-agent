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
    from dataclasses import replace

    from sovereign_agent.assistant_work import claim, enqueue, observe

    enqueue(db, "hidden", "trial", "Brief")
    work = claim(db, "worker")
    observe(db, work, {"role": "assistant", "content": "current"})
    for invalid in (
        replace(work, epoch="unseen-stale-epoch"),
        replace(work, owner="foreign"),
        replace(work, generation=work.generation + 1),
    ):
        try:
            observe(db, invalid, {"role": "assistant", "content": "forbidden"})
        except PermissionError:
            pass
        else:
            raise AssertionError("stale authority wrote")
    assert db.connection.execute("SELECT count(*) FROM assistant_transcript").fetchone()[0] == 1
    marker = db.path.with_suffix(".authority")
    original = marker.read_text()
    marker.unlink()
    try:
        observe(db, work, {"role": "assistant", "content": "missing marker"})
    except PermissionError:
        pass
    else:
        raise AssertionError("missing marker accepted")
    marker.write_text(original)
    observe(db, work, {"role": "assistant", "content": "still current"})
    assert db.connection.execute("SELECT count(*) FROM assistant_transcript").fetchone()[0] == 2
    db.close()
print(json.dumps({"passed": True}))
