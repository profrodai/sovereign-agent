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
    from sovereign_agent.assistant_orders import SpendingPolicy, approve, propose
    from sovereign_agent.assistant_work import claim, enqueue

    enqueue(db, "hidden", "trial", "Draft")
    work = claim(db, "worker")
    policy = SpendingPolicy(frozenset({"lucy"}), total_pence=2600)
    a = propose(db, work, "SKU-VANILLA", 6, target="fixture")
    b = propose(db, work, "SKU-STRAWBERRY", 4, target="fixture")

    def do(i, policy=policy, digest=None):
        actual = db.connection.execute(
            "SELECT digest FROM assistant_orders WHERE id=?", (i,)
        ).fetchone()[0]
        approve(
            db,
            i,
            actual if digest is None else digest,
            actor="lucy",
            policy=policy,
            expires=time.time() + 60,
        )

    do(a)
    do(a)
    assert (
        db.connection.execute("SELECT reserved_pence FROM assistant_spending").fetchone()[0] == 1500
    )
    try:
        do(b, SpendingPolicy(frozenset({"lucy"}), total_pence=2599))
    except PermissionError:
        pass
    else:
        raise AssertionError("one pence overflow admitted")
    assert (
        db.connection.execute("SELECT reserved_pence FROM assistant_spending").fetchone()[0] == 1500
    )
    do(b)
    assert (
        db.connection.execute("SELECT reserved_pence FROM assistant_spending").fetchone()[0] == 2600
    )
    try:
        do(a, digest="wrong")
    except PermissionError:
        pass
    else:
        raise AssertionError("wrong digest accepted")
    db.close()
print(json.dumps({"passed": True}))
