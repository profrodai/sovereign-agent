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
    from reference_organizations.store.agent import OfflineShopModel
    from reference_organizations.store.evaluation import Case, baseline, evaluate

    cases = (
        Case("hidden_empty", "held-out", (), ()),
        Case("hidden_edge", "held-out", (("EDGE", 9, 0, 9, 137),), ()),
        Case("hidden_reserved", "held-out", (("NEW", 11, 5, 14, 137),), (("NEW", 8),)),
    )
    for case in cases:
        assert baseline(case) == list(case.expected)
        report = evaluate(OfflineShopModel, cases=(case,))
        assert report["passed"] is True
    # Deliberately false expected values detect an oracle that simply copies the answer field.
    poison = Case("poison", "held-out", (("DIFFERENT", 15, 4, 18, 91),), (("DIFFERENT", 999),))
    assert baseline(poison) == [("DIFFERENT", 7)]
    assert evaluate(OfflineShopModel, cases=(poison,))["passed"] is False
    db.close()
print(json.dumps({"passed": True}))
