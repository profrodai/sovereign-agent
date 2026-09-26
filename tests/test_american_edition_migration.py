"""Migration 27 moves a file written in pence and "cancelled" to cents and "canceled"."""

import json

from reference_organizations.store.agent import seed_lucy
from sovereign_agent import database
from sovereign_agent.assistant_work import cancel, claim, enqueue
from sovereign_agent.database import Database
from sovereign_agent.models import OutcomeState


def columns(db, table):
    return {row[1] for row in db.connection.execute(f"PRAGMA table_info({table})")}


def test_a_migration_26_file_upgrades_with_its_data(tmp_path, monkeypatch):
    path = tmp_path / "agent.sqlite"
    with monkeypatch.context() as patch:
        patch.setattr(
            database, "MIGRATIONS", tuple(item for item in database.MIGRATIONS if item[0] <= 26)
        )
        db = Database(path)
        seed_lucy(db)
        enqueue(db, "morning", "lucy", "Replenish vanilla")
        work = claim(db, "worker")
        with db.immediate() as connection:
            connection.execute(
                "INSERT INTO assistant_spending(id,limit_pence,reserved_pence,spent_pence) "
                "VALUES (1,20000,1500,700)"
            )
            # What the runtime before migration 27 wrote when it canceled work.
            connection.execute(
                "UPDATE assistant_work SET status='CANCELLED',cancelled=1 WHERE id=?", (work.id,)
            )
            connection.execute(
                "INSERT INTO outcomes(id, record) VALUES (?, ?)",
                ("outcome-1", json.dumps({"id": "outcome-1", "state": "CANCELLED"})),
            )
        assert 27 not in db.applied_versions()
        db.close()

    db = Database(path)
    assert 27 in db.applied_versions()
    assert {"limit_cents", "reserved_cents", "spent_cents"} <= columns(db, "assistant_spending")
    assert not {c for c in columns(db, "assistant_spending") if c.endswith("_pence")}
    assert {"estimated_cost_cents", "canceled"} <= columns(db, "assistant_work")
    assert {"estimated_call_cents", "budget_cents"} <= columns(db, "assistant_delegations")
    assert tuple(
        db.connection.execute(
            "SELECT limit_cents,reserved_cents,spent_cents FROM assistant_spending"
        ).fetchone()
    ) == (20000, 1500, 700)
    assert tuple(
        db.connection.execute(
            "SELECT status,canceled FROM assistant_work WHERE id=?", (work.id,)
        ).fetchone()
    ) == ("CANCELED", 1)
    assert [row[0] for row in db.connection.execute("SELECT status FROM assistant_reports")] == [
        "CANCELED"
    ]
    record = json.loads(
        db.connection.execute("SELECT record FROM outcomes WHERE id='outcome-1'").fetchone()[0]
    )
    assert OutcomeState(record["state"]) is OutcomeState.CANCELED

    # The recreated report triggers still report new work, under the new spelling.
    enqueue(db, "evening", "lucy", "Count vanilla")
    fresh = claim(db, "worker")
    cancel(db, fresh.id)
    assert tuple(
        db.connection.execute(
            "SELECT status FROM assistant_reports WHERE work_id=?", (fresh.id,)
        ).fetchone()
    ) == ("CANCELED",)
    db.close()


def test_a_legacy_outcome_state_still_loads():
    assert OutcomeState("CANCELLED") is OutcomeState.CANCELED
