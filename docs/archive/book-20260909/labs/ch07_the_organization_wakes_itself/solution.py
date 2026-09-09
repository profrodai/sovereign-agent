"""Reference solution for Chapter 7's manual Pulse transaction lab."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

STUDENT_TODO = False


SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE inventory (
    sku TEXT PRIMARY KEY,
    on_hand INTEGER NOT NULL,
    reserved INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL
);
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE signals (
    id TEXT PRIMARY KEY,
    source_event_id TEXT NOT NULL REFERENCES events(id),
    sku TEXT NOT NULL
);
CREATE TABLE wake_decisions (
    id TEXT PRIMARY KEY,
    source_signal_id TEXT NOT NULL UNIQUE REFERENCES signals(id),
    source_event_id TEXT NOT NULL REFERENCES events(id)
);
CREATE TABLE work (
    id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL UNIQUE REFERENCES wake_decisions(id),
    sku TEXT NOT NULL
);
CREATE TABLE origins (
    work_id TEXT PRIMARY KEY REFERENCES work(id),
    decision_id TEXT NOT NULL REFERENCES wake_decisions(id),
    pulse_event_id TEXT NOT NULL UNIQUE REFERENCES events(id)
);
"""


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _fresh_database(path: Path) -> None:
    if path.exists():
        path.unlink()
    connection = _connect(path)
    connection.executescript(SCHEMA)
    connection.execute("INSERT INTO inventory VALUES ('SKU-TEA', 2, 0, 3)")
    connection.execute(
        "INSERT INTO events VALUES ('event-sale', 'sale.committed', ?)",
        (json.dumps({"signal_id": "signal-low", "sku": "SKU-TEA"}, sort_keys=True),),
    )
    connection.execute("INSERT INTO signals VALUES ('signal-low', 'event-sale', 'SKU-TEA')")
    connection.close()


def _manual_tick(connection: sqlite3.Connection, signal_id: str) -> tuple[str | None, bool]:
    """Create or return one canonical work item for a signal.

    The gate is deliberately re-read only after BEGIN IMMEDIATE holds the
    write lock. A caller may have observed an old low-stock state, but that
    observation grants no authority to create work.
    """
    connection.execute("BEGIN IMMEDIATE")
    try:
        existing = connection.execute(
            "SELECT w.id FROM wake_decisions d JOIN work w ON w.decision_id = d.id "
            "WHERE d.source_signal_id = ?",
            (signal_id,),
        ).fetchone()
        if existing is not None:
            connection.commit()
            return str(existing["id"]), False

        row = connection.execute(
            "SELECT s.sku, s.source_event_id, i.on_hand, i.reserved, i.reorder_point "
            "FROM signals s JOIN inventory i ON i.sku = s.sku WHERE s.id = ?",
            (signal_id,),
        ).fetchone()
        if row is None or int(row["on_hand"]) - int(row["reserved"]) > int(row["reorder_point"]):
            connection.commit()
            return None, False

        decision_id = f"decision-{signal_id}"
        work_id = f"work-{signal_id}"
        pulse_event_id = f"event-pulse-{signal_id}"
        connection.execute(
            "INSERT INTO wake_decisions VALUES (?, ?, ?)",
            (decision_id, signal_id, row["source_event_id"]),
        )
        connection.execute("INSERT INTO work VALUES (?, ?, ?)", (work_id, decision_id, row["sku"]))
        connection.execute(
            "INSERT INTO events VALUES (?, 'pulse.work_created', ?)",
            (pulse_event_id, json.dumps({"work_id": work_id}, sort_keys=True)),
        )
        connection.execute(
            "INSERT INTO origins VALUES (?, ?, ?)",
            (work_id, decision_id, pulse_event_id),
        )
        connection.commit()
        return work_id, True
    except BaseException:
        connection.rollback()
        raise


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "pulse.sqlite3"
    _fresh_database(path)

    # A stale outside observation said "low". The shelf is then replenished;
    # the transaction-time read must refuse creation.
    observer = _connect(path)
    was_low = bool(
        observer.execute(
            "SELECT on_hand - reserved <= reorder_point AS low FROM inventory WHERE sku='SKU-TEA'"
        ).fetchone()["low"]
    )
    observer.execute("UPDATE inventory SET on_hand = 9 WHERE sku='SKU-TEA'")
    stale_work, stale_created = _manual_tick(observer, "signal-low")
    stale_counts = {
        "decisions": observer.execute("SELECT COUNT(*) FROM wake_decisions").fetchone()[0],
        "work": observer.execute("SELECT COUNT(*) FROM work").fetchone()[0],
    }
    observer.execute("UPDATE inventory SET on_hand = 2 WHERE sku='SKU-TEA'")
    observer.close()

    barrier = threading.Barrier(2)
    results: list[tuple[str | None, bool]] = []
    result_lock = threading.Lock()

    def contend() -> None:
        connection = _connect(path)
        barrier.wait()
        result = _manual_tick(connection, "signal-low")
        with result_lock:
            results.append(result)
        connection.close()

    contenders = [threading.Thread(target=contend), threading.Thread(target=contend)]
    for contender in contenders:
        contender.start()
    for contender in contenders:
        contender.join()

    inspector = _connect(path)
    chain = inspector.execute(
        "SELECT s.id AS signal_id, e.kind AS source_kind, d.id AS decision_id, "
        "w.id AS work_id, pe.kind AS pulse_kind "
        "FROM signals s JOIN events e ON e.id=s.source_event_id "
        "JOIN wake_decisions d ON d.source_signal_id=s.id "
        "JOIN work w ON w.decision_id=d.id "
        "JOIN origins o ON o.work_id=w.id "
        "JOIN events pe ON pe.id=o.pulse_event_id"
    ).fetchone()
    counts = {
        "decisions": inspector.execute("SELECT COUNT(*) FROM wake_decisions").fetchone()[0],
        "work": inspector.execute("SELECT COUNT(*) FROM work").fetchone()[0],
        "origins": inspector.execute("SELECT COUNT(*) FROM origins").fetchone()[0],
    }
    inspector.close()

    return {
        "mechanism": "manual_tick",
        "stale_observation": {
            "was_low_before_restock": was_low,
            "created_after_restock": stale_created,
            "work_id": stale_work,
            "counts": stale_counts,
        },
        "race": {
            "created_flags": sorted(created for _work_id, created in results),
            "returned_work_ids": sorted({work_id for work_id, _created in results}),
            "counts": counts,
        },
        "source_chain": dict(chain) if chain is not None else {},
    }
