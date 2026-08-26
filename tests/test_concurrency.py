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

from .helpers import governed_assignment


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
    org, _outcome_id, _sow_id, assignment_id = governed_assignment(tmp_path)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    org.db.close()

    def work(db: Database, _index: int) -> str:
        result = apply_restock(db, RestockProposal("SKU-TEA", 6), assignment_id, signal.id)
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
    org, _outcome_id, _sow_id, _assignment_id = governed_assignment(tmp_path)
    org.db.close()  # on_hand = 4 from seed

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


def test_only_one_contender_wins_a_contested_lease(tmp_path: Path) -> None:
    """Two DISTINCT contenders: exactly one wins.

    Named for what it proves. The previous name -- "exactly one owner" --
    overclaimed: a second connection using the SAME actor id is granted the
    claim, because `claim_owner == actor_id` short circuits. That is
    actor-level idempotency, not process-level exclusivity, and the
    distinction is covered by the test below.
    """
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    org.db.close()

    def work(db: Database, index: int) -> str:
        # Distinct contenders: only the addressed actor may claim, so the second
        # is a different actor attempting the same message.
        claim(db, message.id, "sparring-course" if index == 0 else "operator-course")
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


def test_the_same_actor_from_two_processes_is_idempotent_not_exclusive(tmp_path: Path) -> None:
    """State the property honestly rather than overclaiming exclusivity.

    A second connection using the SAME actor id is granted the claim, because a
    claim already held by that actor short circuits. Two processes hosting one
    actor can therefore both proceed. That is actor-level idempotency; it is NOT
    process-level fencing, and 1.x does not provide fencing.

    The governing rule is recorded in
    docs/rulings/2026-08-26-one-process-per-actor.md: one process may host an
    actor, and lease fencing is deferred to Unit 8's supervisor. This test
    exists so nobody reads the mailbox as offering a guarantee it does not.
    """
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    org.db.close()

    first = Database(tmp_path / ".sovereign" / "organization.db")
    second = Database(tmp_path / ".sovereign" / "organization.db")
    try:
        claim(first, message.id, "sparring-course")
        again = claim(second, message.id, "sparring-course")
        assert again.claim_owner == "sparring-course"
    finally:
        first.close()
        second.close()


def test_two_connections_cannot_both_assign_one_sow(tmp_path: Path) -> None:
    """A duplicate assignment is a durable semantic consequence of a retry.

    `assign()` used to create a row from ANY state and only advance from READY
    or CHANGES_REQUESTED, so a second call left an assignment that could never
    run — and proof selection immediately treated it as the bound execution.
    """
    from sovereign_agent.models import Role

    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "t", "d", ["inventory_at_or_above_reorder_point"], "principal-human", "SKU-TEA"
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "s", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    org.db.close()

    def work(db: Database, _index: int) -> str:
        organization = Organization(tmp_path)
        organization.assign(sow.id, "operator-course", "master-course")
        return "assigned"

    results = _run_concurrently(tmp_path, work)

    db = Database(tmp_path / ".sovereign" / "organization.db")
    count = int(db.connection.execute("SELECT COUNT(*) AS c FROM assignments").fetchone()["c"])
    db.close()
    assert results.count("assigned") == 1, f"two workers both assigned: {results}"
    assert count == 1, f"{count} assignments exist for one SOW"
