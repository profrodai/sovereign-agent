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
    import copy
    import runpy

    m = runpy.run_path("book/always_on/learner/ch02.py")
    shop = copy.deepcopy(m["SHOP"])
    shop["products"][0]["on_hand"] = 1
    factory = m["build_tools"]
    tools = factory(shop)
    call = m["ToolCall"]
    r = tools.invoke(
        call(id="valid", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 7})
    )
    assert r["ok"] is True and r["value"]["total_pence"] == 1750 and r["value"]["status"] == "DRAFT"
    for quantity in (6, 8, True, 0, -1, "7"):
        assert (
            tools.invoke(
                call(
                    id="bad",
                    name="draft_order",
                    arguments={"sku": "SKU-VANILLA", "quantity": quantity},
                )
            )["ok"]
            is False
        )
    shop["products"][0]["on_hand"] = 999
    assert (
        tools.invoke(
            call(id="copy", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 7})
        )["ok"]
        is True
    )
    assert (
        factory({"products": []}).invoke(call(id="empty", name="list_stock", arguments={}))["value"]
        == []
    )
    try:
        factory({"products": [shop["products"][0], shop["products"][0]]})
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate identity admitted")
    db.close()
print(json.dumps({"passed": True}))
