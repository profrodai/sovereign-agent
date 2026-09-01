"""Reference solution for Chapter 9's invariant-preserving sale lab."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

STUDENT_TODO = False


SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE products (
    sku TEXT PRIMARY KEY,
    price_cents INTEGER NOT NULL CHECK (price_cents > 0)
);
CREATE TABLE inventory (
    sku TEXT PRIMARY KEY REFERENCES products(sku),
    on_hand INTEGER NOT NULL CHECK (on_hand >= 0),
    reserved INTEGER NOT NULL CHECK (reserved >= 0 AND reserved <= on_hand),
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0)
);
CREATE TABLE cash_entries (
    sale_id TEXT PRIMARY KEY,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0)
);
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


class SaleError(RuntimeError):
    pass


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _fresh_database(path: Path, *, on_hand: int, reserved: int) -> None:
    if path.exists():
        path.unlink()
    connection = _connect(path)
    connection.executescript(SCHEMA)
    connection.execute("INSERT INTO products VALUES ('SKU-GELATO', 425)")
    connection.execute(
        "INSERT INTO inventory VALUES ('SKU-GELATO', ?, ?, 2)",
        (on_hand, reserved),
    )
    connection.close()


def _record_sale(
    connection: sqlite3.Connection,
    sale_id: str,
    sku: str,
    quantity: int,
    *,
    fail_after_cash: bool = False,
) -> dict[str, int | str]:
    if quantity <= 0:
        raise SaleError("quantity must be positive")
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute(
            "SELECT i.on_hand, i.reserved, p.price_cents "
            "FROM inventory i JOIN products p USING (sku) WHERE i.sku = ?",
            (sku,),
        ).fetchone()
        if row is None:
            raise SaleError("unknown SKU")
        available = int(row["on_hand"]) - int(row["reserved"])
        if quantity > available:
            raise SaleError(f"requested {quantity}, available {available}")
        amount = quantity * int(row["price_cents"])
        new_on_hand = int(row["on_hand"]) - quantity
        connection.execute("UPDATE inventory SET on_hand=? WHERE sku=?", (new_on_hand, sku))
        connection.execute("INSERT INTO cash_entries VALUES (?, ?)", (sale_id, amount))
        if fail_after_cash:
            raise RuntimeError("injected failure after cash")
        connection.execute(
            "INSERT INTO events VALUES (?, 'sale.committed', ?)",
            (
                f"event-{sale_id}",
                json.dumps(
                    {"amount_cents": amount, "qty": quantity, "sale_id": sale_id, "sku": sku},
                    sort_keys=True,
                ),
            ),
        )
        connection.commit()
        return {"sale_id": sale_id, "quantity": quantity, "amount_cents": amount}
    except BaseException:
        connection.rollback()
        raise


def _snapshot(connection: sqlite3.Connection) -> dict[str, int]:
    inventory = connection.execute(
        "SELECT on_hand, reserved FROM inventory WHERE sku='SKU-GELATO'"
    ).fetchone()
    return {
        "on_hand": int(inventory["on_hand"]),
        "reserved": int(inventory["reserved"]),
        "available": int(inventory["on_hand"]) - int(inventory["reserved"]),
        "cash_total": int(
            connection.execute(
                "SELECT COALESCE(SUM(amount_cents), 0) FROM cash_entries"
            ).fetchone()[0]
        ),
        "cash_rows": int(connection.execute("SELECT COUNT(*) FROM cash_entries").fetchone()[0]),
        "event_rows": int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]),
    }


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "sale.sqlite3"
    _fresh_database(path, on_hand=5, reserved=2)
    connection = _connect(path)

    reservation_refusal = "not_refused"
    try:
        _record_sale(connection, "reserved-sale", "SKU-GELATO", 4)
    except SaleError as error:
        reservation_refusal = str(error)
    after_reservation_refusal = _snapshot(connection)

    committed = _record_sale(connection, "sale-one", "SKU-GELATO", 2)
    event_payload = json.loads(
        connection.execute("SELECT payload FROM events WHERE id='event-sale-one'").fetchone()[0]
    )
    after_commit = _snapshot(connection)

    injected_failure = "not_raised"
    before_failure = _snapshot(connection)
    try:
        _record_sale(
            connection,
            "sale-fault",
            "SKU-GELATO",
            1,
            fail_after_cash=True,
        )
    except RuntimeError as error:
        injected_failure = str(error)
    after_failure = _snapshot(connection)
    connection.close()

    race_path = root / "sale-race.sqlite3"
    _fresh_database(race_path, on_hand=3, reserved=0)
    barrier = threading.Barrier(2)
    statuses: list[str] = []
    statuses_lock = threading.Lock()

    def contend(sale_id: str) -> None:
        contender = _connect(race_path)
        barrier.wait()
        try:
            _record_sale(contender, sale_id, "SKU-GELATO", 2)
            status = "committed"
        except SaleError:
            status = "refused"
        with statuses_lock:
            statuses.append(status)
        contender.close()

    threads = [
        threading.Thread(target=contend, args=("race-a",)),
        threading.Thread(target=contend, args=("race-b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    race_inspector = _connect(race_path)
    race_snapshot = _snapshot(race_inspector)
    race_inspector.close()

    return {
        "reservation": {
            "result": reservation_refusal,
            "state": after_reservation_refusal,
        },
        "committed_sale": {
            "receipt": committed,
            "event_payload": event_payload,
            "state": after_commit,
        },
        "fault_injection": {
            "result": injected_failure,
            "state_unchanged": before_failure == after_failure,
            "state": after_failure,
        },
        "contention": {
            "statuses": sorted(statuses),
            "state": race_snapshot,
        },
    }
