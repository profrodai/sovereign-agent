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
    from sovereign_agent.assistant_context import activate_skill, context, stage_skill

    p = state / "skill.toml"
    p.write_text(
        'name="transfer"\nversion="1"\ninstructions="UNIQUE_GUIDANCE"\nrequires=["read_a","read_b"]\n'
    )
    stage_skill(db, p)
    assert (
        "UNIQUE_GUIDANCE"
        not in context(db, "trial", "brief", allowed=frozenset({"read_a", "read_b"}))[0]["content"]
    )
    activate_skill(
        db,
        "transfer",
        "1",
        evaluate=lambda s: {"independent": True},
        required_cases=frozenset({"independent"}),
    )
    assert (
        "UNIQUE_GUIDANCE"
        not in context(db, "trial", "brief", allowed=frozenset({"read_a"}))[0]["content"]
    )
    assert (
        "UNIQUE_GUIDANCE"
        in context(db, "trial", "brief", allowed=frozenset({"read_a", "read_b"}))[0]["content"]
    )
    p = state / "empty.toml"
    p.write_text(
        'name="unrestricted"\nversion="1"\ninstructions="EMPTY_REQUIREMENTS"\nrequires=[]\n'
    )
    stage_skill(db, p)
    activate_skill(
        db,
        "unrestricted",
        "1",
        evaluate=lambda s: {"independent": True},
        required_cases=frozenset({"independent"}),
    )
    assert "EMPTY_REQUIREMENTS" in context(db, "trial", "brief", allowed=frozenset())[0]["content"]
    db.close()
print(json.dumps({"passed": True}))
