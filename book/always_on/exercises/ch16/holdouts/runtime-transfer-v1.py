"""Instructor transfer cases exercise the actual copied runtime, with independent answers."""

import json
import tempfile
import time
from pathlib import Path

from reference_organizations.store.agent import seed_lucy
from sovereign_agent.database import Database

with tempfile.TemporaryDirectory(prefix="lucy-transfer-") as directory:
    state = Path(directory)
    db = Database(state / "agent.sqlite")
    seed_lucy(db)
    from reference_organizations.store.operating_report import operating_report
    from sovereign_agent.assistant_orders import SpendingPolicy, approve, propose
    from sovereign_agent.assistant_work import claim, enqueue

    assert operating_report(db)["spending"]["order_totals_match"] is True
    enqueue(db, "hidden", "trial", "Brief")
    work = claim(db, "worker")
    i = propose(db, work, "SKU-STRAWBERRY", 4, target="fixture")
    digest = db.connection.execute(
        "SELECT digest FROM assistant_orders WHERE id=?", (i,)
    ).fetchone()[0]
    approve(
        db,
        i,
        digest,
        actor="lucy",
        policy=SpendingPolicy(frozenset({"lucy"})),
        expires=time.time() + 60,
    )
    report = operating_report(db)
    assert (
        report["spending"]["order_totals_match"] is True
        and report["spending"]["reserved_pence"] == 1100
    )
    with db.immediate() as c:
        c.execute("UPDATE assistant_spending SET reserved_pence=1101")
    report = operating_report(db)
    assert report["spending"]["order_totals_match"] is False
    assert "Spending ledger and retained order totals disagree." in report["exceptions"]
    assert "Spending ledger and retained order totals disagree." in report["text"]
    assert db.connection.in_transaction is False
    with db.immediate() as c:
        c.execute("UPDATE assistant_control SET paused=1")
    assert operating_report(db)["paused"] is True
    db.close()
print(json.dumps({"passed": True}))
