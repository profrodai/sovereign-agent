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
    from sovereign_agent.assistant_context import context, forget, preferences, remember

    assert preferences(db, "new") == []
    remember(db, "trial", "delivery", "dawn", "first")
    remember(db, "trial", "delivery", "noon", "second")
    remember(db, "trial", "delivery", "midnight", "third")
    remember(db, "foreign", "delivery", "foreign-only", "other")
    remember(db, "trial", "format", "short", "fourth")
    rows = preferences(db, "trial", "MIDNIGHT", maximum=1)
    assert len(rows) == 1 and rows[0]["value"] == "midnight" and rows[0]["source"] == "third"
    assert len(preferences(db, "trial")) == 2
    forget(db, "trial", "delivery")
    db.close()
    db = Database(state / "agent.sqlite")
    text = context(db, "trial", "delivery", allowed=frozenset())[0]["content"]
    assert (
        all(v not in text for v in ("dawn", "noon", "midnight", "foreign-only")) and "short" in text
    )
    for maximum in (0, 101):
        try:
            preferences(db, "trial", maximum=maximum)
        except ValueError:
            pass
        else:
            raise AssertionError("unbounded retrieval")
    db.close()
print(json.dumps({"passed": True}))
