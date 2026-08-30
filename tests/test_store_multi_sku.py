"""Unit 11 proof matrix: the multi-SKU isolation matrix (governing ruling
Holding 2), a BINDING acceptance requirement, not a nice-to-have.

Proves, with real tests, all six surfaces the governing SOW names: sales
isolation, signal isolation, wake-decision isolation, Pulse-origin
isolation, assignment/replenishment isolation, and replay/restart/
concurrency preserving per-SKU idempotency. Concurrency proofs use real,
separate database connections against the same file -- never mocks standing
in for the SQLite boundary, extending `tests/test_pulse.py`'s own
`test_two_real_processes_evaluating_the_same_signal_create_one_canonical_
sow` precedent to the multi-SKU case rather than forking it.
"""

from __future__ import annotations

import threading
from pathlib import Path

from reference_organizations.store import (
    apply_restock,
    below_reorder,
    record_sale,
    seed_catalog,
)
from reference_organizations.store.pulse_gate import store_wake_gate
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization
from sovereign_agent.pulse import run_pulse_once

TEA = "SKU-TEA"
COFFEE = "SKU-COFFEE"


def _seeded_multi_sku_org(root: Path) -> tuple[Organization, dict[str, str]]:
    """A catalog org with one ACTIVE outcome per SKU -- the shape
    `store_wake_gate` requires (exactly one matching ACTIVE outcome per
    subject) to fire independently for each SKU."""
    org = Organization.init(root)
    seed_catalog(org.db)
    outcome_ids: dict[str, str] = {}
    for sku, title in ((TEA, "Keep the tea jar stocked"), (COFFEE, "Keep the coffee tin stocked")):
        outcome = org.create_outcome(
            title,
            f"On-hand {sku} is at or above the reorder point, the purchase is "
            "reconciled, and the replenishment is on the ledger.",
            [
                "inventory_at_or_above_reorder_point",
                "cash_reconciles",
                "replenishment_event_exists",
            ],
            "principal-human",
            sku,
        )
        org.activate(outcome.id, "master-course")
        outcome_ids[sku] = outcome.id
    return org, outcome_ids


# === Sales isolation ============================================================


def test_a_sale_of_one_sku_does_not_change_another_skus_inventory(tmp_path: Path) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    before = org.db.connection.execute(
        "SELECT on_hand FROM inventory WHERE sku = ?", (COFFEE,)
    ).fetchone()["on_hand"]
    record_sale(org.db, TEA, 2, 400)
    after = org.db.connection.execute(
        "SELECT on_hand FROM inventory WHERE sku = ?", (COFFEE,)
    ).fetchone()["on_hand"]
    assert before == after
    assert TEA in below_reorder(org.db)
    assert COFFEE not in below_reorder(org.db)


def test_a_sale_of_one_sku_creates_no_cash_entry_naming_another_sku(tmp_path: Path) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    record_sale(org.db, TEA, 2, 400)
    rows = org.db.connection.execute(
        "SELECT record FROM cash_entries WHERE record LIKE ?", (f"%{COFFEE}%",)
    ).fetchall()
    assert rows == []


# === Signal isolation ===========================================================


def test_signals_for_different_skus_never_share_a_dedupe_key(tmp_path: Path) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 4, 650)
    assert tea_signal.dedupe_key != coffee_signal.dedupe_key
    assert tea_signal.id != coffee_signal.id
    assert tea_signal.subject_ref == TEA
    assert coffee_signal.subject_ref == COFFEE


def test_a_signal_for_one_sku_is_never_conflated_with_another_skus_signal(
    tmp_path: Path,
) -> None:
    """Extends Unit 9's own per-occurrence dedupe_key fix: two DIFFERENT
    SKUs crossing their reorder points in the same run must produce two
    independently-readable signal rows, neither replacing the other."""
    org, _ = _seeded_multi_sku_org(tmp_path)
    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 5, 650)
    rows = org.db.connection.execute("SELECT id FROM signals").fetchall()
    ids = {row["id"] for row in rows}
    assert tea_signal.id in ids
    assert coffee_signal.id in ids
    assert len(ids) == 2


# === Wake-decision isolation ====================================================


def test_wake_gate_maps_each_signal_to_its_own_skus_outcome_only(tmp_path: Path) -> None:
    org, outcome_ids = _seeded_multi_sku_org(tmp_path)
    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 5, 650)

    tea_decision = store_wake_gate(org, tea_signal)
    coffee_decision = store_wake_gate(org, coffee_signal)

    assert tea_decision is not None
    assert coffee_decision is not None
    assert tea_decision.outcome_id == outcome_ids[TEA]
    assert coffee_decision.outcome_id == outcome_ids[COFFEE]
    assert tea_decision.outcome_id != coffee_decision.outcome_id


def test_wake_gate_never_fires_for_a_sku_still_above_reorder(tmp_path: Path) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    # Sell only one unit of coffee: on_hand goes from 10 to 9, still above
    # its reorder point of 6, so the signal is "info" severity and the gate
    # must decline it even though a signal was durably recorded.
    coffee_signal = record_sale(org.db, COFFEE, 1, 650)
    assert store_wake_gate(org, coffee_signal) is None


# === Pulse-origin isolation ======================================================


def test_pulse_origins_trace_each_decision_back_to_the_correct_skus_signal(
    tmp_path: Path,
) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 5, 650)

    report = run_pulse_once(org, store_wake_gate)
    tea_item = next(item for item in report.items if item.signal_id == tea_signal.id)
    coffee_item = next(item for item in report.items if item.signal_id == coffee_signal.id)
    assert tea_item.status == "created"
    assert coffee_item.status == "created"
    assert tea_item.sow_id != coffee_item.sow_id
    assert tea_item.assignment_id != coffee_item.assignment_id

    tea_origin = org.pulse_origin_for_sow(tea_item.sow_id)
    coffee_origin = org.pulse_origin_for_sow(coffee_item.sow_id)
    assert tea_origin is not None
    assert coffee_origin is not None

    tea_wd = org.db.connection.execute(
        "SELECT source_signal_id, subject FROM pulse_wake_decisions WHERE id = ?",
        (tea_origin.wake_decision_id,),
    ).fetchone()
    coffee_wd = org.db.connection.execute(
        "SELECT source_signal_id, subject FROM pulse_wake_decisions WHERE id = ?",
        (coffee_origin.wake_decision_id,),
    ).fetchone()
    assert tea_wd["source_signal_id"] == tea_signal.id
    assert tea_wd["subject"] == TEA
    assert coffee_wd["source_signal_id"] == coffee_signal.id
    assert coffee_wd["subject"] == COFFEE


# === Assignment and replenishment isolation ======================================


def test_multiple_qualifying_skus_each_get_their_own_canonical_chain(tmp_path: Path) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 5, 650)

    report = run_pulse_once(org, store_wake_gate)
    tea_item = next(item for item in report.items if item.signal_id == tea_signal.id)
    coffee_item = next(item for item in report.items if item.signal_id == coffee_signal.id)
    assert tea_item.assignment_state == AssignmentState.COMPLETED.value
    assert coffee_item.assignment_state == AssignmentState.COMPLETED.value

    sows = org.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    assignments = org.db.connection.execute("SELECT COUNT(*) AS c FROM assignments").fetchone()["c"]
    assert sows == 2
    assert assignments == 2


def test_replenishment_effect_for_one_sku_never_touches_another_skus_inventory(
    tmp_path: Path,
) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    coffee_before = org.db.connection.execute(
        "SELECT on_hand FROM inventory WHERE sku = ?", (COFFEE,)
    ).fetchone()["on_hand"]

    tea_signal = record_sale(org.db, TEA, 2, 400)
    report = run_pulse_once(org, store_wake_gate)
    tea_item = next(item for item in report.items if item.signal_id == tea_signal.id)
    assignment = org._assignment(tea_item.assignment_id)  # noqa: SLF001 -- test, same module family

    from reference_organizations.store import RestockProposal

    apply_restock(org.db, RestockProposal(TEA, 10), assignment.id, tea_signal.id)

    coffee_after = org.db.connection.execute(
        "SELECT on_hand FROM inventory WHERE sku = ?", (COFFEE,)
    ).fetchone()["on_hand"]
    assert coffee_before == coffee_after

    effects = org.db.connection.execute(
        "SELECT subject FROM effects WHERE assignment_id = ?", (assignment.id,)
    ).fetchall()
    assert {row["subject"] for row in effects} == {TEA}


# === Replay, restart, and concurrency preserve per-SKU idempotency ==============


def test_replaying_pulse_for_multiple_skus_creates_no_duplicate_work(tmp_path: Path) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    record_sale(org.db, TEA, 2, 400)
    record_sale(org.db, COFFEE, 5, 650)
    run_pulse_once(org, store_wake_gate)
    second = run_pulse_once(org, store_wake_gate)
    assert second.items == ()
    sows = org.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    assert sows == 2


def test_reopening_the_database_preserves_both_skus_canonical_work(tmp_path: Path) -> None:
    org, _ = _seeded_multi_sku_org(tmp_path)
    record_sale(org.db, TEA, 2, 400)
    record_sale(org.db, COFFEE, 5, 650)
    run_pulse_once(org, store_wake_gate)
    org.db.close()

    reopened = Organization(tmp_path)
    second = run_pulse_once(reopened, store_wake_gate)
    assert second.items == ()
    sows = reopened.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    decisions = reopened.db.connection.execute(
        "SELECT COUNT(*) AS c FROM pulse_wake_decisions"
    ).fetchone()["c"]
    assert sows == 2
    assert decisions == 2


def test_two_real_connections_racing_two_different_skus_create_two_canonical_sows(
    tmp_path: Path,
) -> None:
    """A REAL two-connection proof extending
    `tests/test_pulse.py::test_two_real_processes_evaluating_the_same_
    signal_create_one_canonical_sow`: two genuinely separate `Organization`
    instances race `create_pulse_work` for DIFFERENT SKUs' signals at the
    same moment via a real `threading.Barrier`. Each SKU must get its own
    canonical SOW; neither may contaminate or block the other, and neither
    may produce a duplicate for its own SKU."""
    org, outcome_ids = _seeded_multi_sku_org(tmp_path)
    tea_signal = record_sale(org.db, TEA, 2, 400)
    coffee_signal = record_sale(org.db, COFFEE, 5, 650)
    tea_event_id = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed' "
        "AND json_extract(payload, '$.signal_id') = ?",
        (tea_signal.id,),
    ).fetchone()["id"]
    coffee_event_id = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed' "
        "AND json_extract(payload, '$.signal_id') = ?",
        (coffee_signal.id,),
    ).fetchone()["id"]
    org.db.close()

    barrier = threading.Barrier(2)
    results: list[tuple[str, str, str, bool]] = []
    lock = threading.Lock()

    def contend(sku: str, signal_id: str, event_id: str) -> None:
        contender = Organization(tmp_path)
        contender.db.connection.execute("PRAGMA busy_timeout = 5000")
        barrier.wait()
        sow, assignment, created = contender.create_pulse_work(
            source_signal_id=signal_id,
            source_event_id=event_id,
            subject=sku,
            outcome_id=outcome_ids[sku],
            scope=f"pulse replenishment for {sku}",
            role=Role.OPERATOR,
            planner_id="master-course",
            worker_id="operator-course",
            required_effect_kind="replenishment",
        )
        with lock:
            results.append((sku, sow.id, assignment.id, created))
        contender.db.close()

    threads = [
        threading.Thread(target=contend, args=(TEA, tea_signal.id, tea_event_id)),
        threading.Thread(target=contend, args=(COFFEE, coffee_signal.id, coffee_event_id)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 2
    by_sku = {row[0]: row for row in results}
    assert by_sku[TEA][3] is True, "the TEA racer must win its own SKU's canonical creation"
    assert by_sku[COFFEE][3] is True, "the COFFEE racer must win its own SKU's canonical creation"
    assert by_sku[TEA][1] != by_sku[COFFEE][1], "different SKUs must never share a SOW"

    inspector = Organization(tmp_path)
    sow_count = inspector.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    decision_count = inspector.db.connection.execute(
        "SELECT COUNT(*) AS c FROM pulse_wake_decisions"
    ).fetchone()["c"]
    assert sow_count == 2
    assert decision_count == 2
