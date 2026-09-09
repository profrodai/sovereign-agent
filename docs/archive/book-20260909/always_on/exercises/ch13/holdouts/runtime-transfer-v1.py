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
    from sovereign_agent.assistant_context import activate_skill, skill_snapshot, stage_skill

    for name in ("candidate", "other"):
        p = state / (name + ".toml")
        p.write_text(
            "name=" + json.dumps(name) + '\nversion="1"\ninstructions="Use GBP"\nrequires=[]\n'
        )
        stage_skill(db, p)

    def activate(name, callback):
        return activate_skill(
            db, name, "1", evaluate=callback, required_cases=frozenset({"hidden"})
        )

    for values in ({}, {"hidden": False}, {"hidden": 1}):
        try:
            activate("candidate", lambda s, values=values: values)
        except ValueError:
            pass
        else:
            raise AssertionError("incomplete evaluation accepted")
    assert skill_snapshot(db)[1] == ()

    def concurrent(s):
        activate("other", lambda s: {"hidden": True})
        return {"hidden": True}

    try:
        activate("candidate", concurrent)
    except PermissionError:
        pass
    else:
        raise AssertionError("stale evaluation activated")
    assert [s.name for s in skill_snapshot(db)[1]] == ["other"]
    activate("candidate", lambda s: {"hidden": True})
    assert [s.name for s in skill_snapshot(db)[1]] == ["candidate", "other"]
    db.close()
print(json.dumps({"passed": True}))
