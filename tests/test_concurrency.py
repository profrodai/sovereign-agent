"""Two connections, one truth.

Every test in the rest of this suite uses a single connection. That is a
structural blind spot: a read-then-write race is invisible to sequential tests,
and six of the seven blocking findings on PR #24 lived in it. These tests open
real second connections and force contention with a barrier.
"""

from __future__ import annotations

import threading
from pathlib import Path

from reference_organizations.store import RestockProposal, apply_restock, record_sale, seed
from sovereign_agent.database import Database
from sovereign_agent.organization import Organization
from sovereign_agent.relay import claim, send


def _run_concurrently(root: Path, work, count: int = 2) -> list[str]:
    """Run `work(db, index)` on `count` independent connections, released together."""
    barrier = threading.Barrier(count)
    results: list[str] = []
    lock = threading.Lock()

    def runner(index: int) -> None:
        db = Database(root / ".sovereign" / "organization.db")
        db.connection.execute("PRAGMA busy_timeout = 5000")
        barrier.wait()
        try:
            outcome = work(db, index)
        except Exception as error:  # noqa: BLE001 - the refusal is the result
            outcome = f"{type(error).__name__}"
        with lock:
            results.append(outcome)
        db.close()

    threads = [threading.Thread(target=runner, args=(index,)) for index in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def test_concurrent_retries_order_stock_exactly_once(tmp_path: Path) -> None:
    """A retry must not double-order.

    Before the fix, both workers passed a preflight scan of the event log and
    both committed: on_hand=14, two purchase entries, two replenishment events.
    """
    org = Organization.init(tmp_path)
    seed(org.db)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    org.db.close()

    def work(db: Database, _index: int) -> str:
        result = apply_restock(db, RestockProposal("SKU-TEA", 6), "asg_same", signal.id)
        return "replay" if result.get("idempotent_replay") else "committed"

    results = _run_concurrently(tmp_path, work)

    db = Database(tmp_path / ".sovereign" / "organization.db")
    on_hand = int(
        db.connection.execute("SELECT on_hand FROM inventory WHERE sku = 'SKU-TEA'").fetchone()[
            "on_hand"
        ]
    )
    events = int(
        db.connection.execute(
            "SELECT COUNT(*) AS c FROM events WHERE kind = 'replenishment.committed'"
        ).fetchone()["c"]
    )
    purchases = int(
        db.connection.execute(
            "SELECT COUNT(*) AS c FROM cash_entries WHERE amount_cents < 0"
        ).fetchone()["c"]
    )
    db.close()

    assert results.count("committed") == 1, f"expected exactly one commit, got {results}"
    assert on_hand == 8, f"stock ordered more than once: on_hand={on_hand}"
    assert events == 1
    assert purchases == 1


def test_concurrent_sales_cannot_oversell(tmp_path: Path) -> None:
    """Two sales of the whole shelf must not both succeed."""
    org = Organization.init(tmp_path)
    seed(org.db)  # on_hand = 4
    org.db.close()

    def work(db: Database, _index: int) -> str:
        record_sale(db, "SKU-TEA", 3, 400)
        return "sold"

    results = _run_concurrently(tmp_path, work)

    db = Database(tmp_path / ".sovereign" / "organization.db")
    on_hand = int(
        db.connection.execute("SELECT on_hand FROM inventory WHERE sku = 'SKU-TEA'").fetchone()[
            "on_hand"
        ]
    )
    sales = int(
        db.connection.execute(
            "SELECT COUNT(*) AS c FROM events WHERE kind = 'sale.committed'"
        ).fetchone()["c"]
    )
    db.close()

    assert on_hand >= 0, "inventory went negative under concurrent sales"
    assert sales == results.count("sold")
    assert on_hand == 4 - 3 * results.count("sold")


def test_a_message_lease_has_exactly_one_owner(tmp_path: Path) -> None:
    """Two connections must not both believe they hold the same claim."""
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    org.db.close()

    def work(db: Database, _index: int) -> str:
        claim(db, message.id, "sparring-course")
        return "claimed"

    results = _run_concurrently(tmp_path, work)

    db = Database(tmp_path / ".sovereign" / "organization.db")
    claimed_events = int(
        db.connection.execute(
            "SELECT COUNT(*) AS c FROM events WHERE kind = 'message.claimed'"
        ).fetchone()["c"]
    )
    db.close()

    assert results.count("claimed") == 1, f"two workers claimed one lease: {results}"
    assert claimed_events == 1
