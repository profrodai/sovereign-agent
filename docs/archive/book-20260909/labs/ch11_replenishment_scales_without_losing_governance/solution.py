"""SQLite exercise: authorization, idempotency, and atomicity are distinct."""

from __future__ import annotations

import sqlite3
from pathlib import Path

STUDENT_TODO = False


class Restock:
    def __init__(
        self,
        effect_key: str,
        assignment_id: str,
        signal_id: str,
        sku: str,
        quantity: int,
        unit_cost_cents: int,
    ) -> None:
        self.effect_key = effect_key
        self.assignment_id = assignment_id
        self.signal_id = signal_id
        self.sku = sku
        self.quantity = quantity
        self.unit_cost_cents = unit_cost_cents


def initialize(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode = WAL;
            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                on_hand INTEGER NOT NULL CHECK (on_hand >= 0)
            );
            CREATE TABLE IF NOT EXISTS cash (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                cents INTEGER NOT NULL CHECK (cents >= 0)
            );
            CREATE TABLE IF NOT EXISTS authorizations (
                assignment_id TEXT PRIMARY KEY,
                signal_id TEXT NOT NULL,
                subject TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS effects (
                effect_key TEXT PRIMARY KEY,
                assignment_id TEXT NOT NULL,
                signal_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost_cents INTEGER NOT NULL
            );
            INSERT OR IGNORE INTO inventory(sku, on_hand) VALUES ('SKU-TEA', 4);
            INSERT OR IGNORE INTO cash(singleton, cents) VALUES (1, 10000);
            INSERT OR IGNORE INTO authorizations(assignment_id, signal_id, subject)
                VALUES ('assignment-tea', 'signal-tea-low', 'SKU-TEA');
            """
        )
        connection.commit()
    finally:
        connection.close()


def apply_restock(db_path: Path, request: Restock, *, fault: str | None = None) -> str:
    """Return applied/replay; refuse unauthorized or colliding requests."""
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("BEGIN IMMEDIATE")
        authorization = connection.execute(
            "SELECT signal_id, subject FROM authorizations WHERE assignment_id = ?",
            (request.assignment_id,),
        ).fetchone()
        if authorization is None or (authorization["signal_id"], authorization["subject"]) != (
            request.signal_id,
            request.sku,
        ):
            raise ValueError("unauthorized")

        existing = connection.execute(
            "SELECT assignment_id, signal_id, subject, quantity, unit_cost_cents "
            "FROM effects WHERE effect_key = ?",
            (request.effect_key,),
        ).fetchone()
        identity = (
            request.assignment_id,
            request.signal_id,
            request.sku,
            request.quantity,
            request.unit_cost_cents,
        )
        if existing is not None:
            durable = tuple(existing)
            if durable != identity:
                raise ValueError("effect_identity_conflict")
            connection.commit()
            return "replay"

        if request.quantity <= 0 or request.unit_cost_cents < 0:
            raise ValueError("invalid_restock")
        cost = request.quantity * request.unit_cost_cents
        cash = connection.execute("SELECT cents FROM cash WHERE singleton = 1").fetchone()["cents"]
        if cash < cost:
            raise ValueError("insufficient_cash")

        updated = connection.execute(
            "UPDATE inventory SET on_hand = on_hand + ? WHERE sku = ?",
            (request.quantity, request.sku),
        )
        if updated.rowcount != 1:
            raise ValueError("unknown_sku")
        if fault == "after_inventory":
            raise RuntimeError("injected_after_inventory")
        connection.execute("UPDATE cash SET cents = cents - ? WHERE singleton = 1", (cost,))
        connection.execute(
            "INSERT INTO effects VALUES (?, ?, ?, ?, ?, ?)",
            (request.effect_key, *identity),
        )
        connection.commit()
        return "applied"
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def snapshot(db_path: Path) -> dict[str, int]:
    connection = sqlite3.connect(db_path)
    try:
        on_hand = connection.execute(
            "SELECT on_hand FROM inventory WHERE sku = 'SKU-TEA'"
        ).fetchone()[0]
        cash = connection.execute("SELECT cents FROM cash WHERE singleton = 1").fetchone()[0]
        effects = connection.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
        return {"tea_on_hand": on_hand, "cash_cents": cash, "effect_count": effects}
    finally:
        connection.close()


def exercise(root: Path) -> dict[str, object]:
    db_path = root / "restock.sqlite3"
    initialize(db_path)
    canonical = Restock(
        "restock:signal-tea-low",
        "assignment-tea",
        "signal-tea-low",
        "SKU-TEA",
        6,
        300,
    )
    apply_restock(db_path, canonical)
    replay = apply_restock(db_path, canonical)

    unauthorized = "not_tested"
    try:
        apply_restock(
            db_path,
            Restock("restock:intruder", "assignment-intruder", "signal-tea-low", "SKU-TEA", 2, 300),
        )
    except ValueError as exc:
        unauthorized = str(exc)

    before_fault = snapshot(db_path)
    rollback = "not_tested"
    try:
        apply_restock(
            db_path,
            Restock("restock:fault", "assignment-tea", "signal-tea-low", "SKU-TEA", 2, 300),
            fault="after_inventory",
        )
    except RuntimeError as exc:
        rollback = str(exc)

    return {
        "state": snapshot(db_path),
        "replay": replay,
        "unauthorized": unauthorized,
        "fault": rollback,
        "rollback_preserved_state": before_fault == snapshot(db_path),
        "lesson": "idempotency_does_not_grant_authority",
    }
