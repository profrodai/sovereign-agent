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
    from reference_organizations.store.agent import NoArguments
    from sovereign_agent.model_turn import ToolCall
    from sovereign_agent.tool_dispatch import Dispatcher, ExecutableTool

    seen = []

    def handler(args):
        seen.append("handler")
        return {"answer": 17}

    tool = ExecutableTool("hidden_read", "Read", NoArguments, handler)
    call = ToolCall(id="transfer", name="hidden_read", arguments={})
    assert Dispatcher([tool], allowed=frozenset()).invoke(call) == {
        "ok": False,
        "error": "tool_not_allowed",
    }
    assert seen == []
    assert Dispatcher([tool], allowed=frozenset({"hidden_read"})).invoke(call)["value"] == {
        "answer": 17
    }
    assert seen == ["handler"]
    write = ExecutableTool("hidden_read", "Write", NoArguments, handler, consequential=True)
    assert (
        Dispatcher([write], allowed=frozenset({"hidden_read"})).invoke(call)["error"]
        == "write_authority_required"
    )
    assert seen == ["handler"]

    def guard(call):
        seen.append("guard")

    assert (
        Dispatcher([write], allowed=frozenset({"hidden_read"}), before_write=guard).invoke(call)[
            "ok"
        ]
        is True
    )
    assert seen == ["handler", "guard", "handler"]
    bad = ToolCall(id="bad", name="hidden_read", arguments={"synthetic_secret": "never-echo"})
    result = Dispatcher([tool], allowed=frozenset({"hidden_read"})).invoke(bad)
    assert result == {"ok": False, "error": "invalid_arguments"} and "never-echo" not in json.dumps(
        result
    )
    db.close()
print(json.dumps({"passed": True}))
