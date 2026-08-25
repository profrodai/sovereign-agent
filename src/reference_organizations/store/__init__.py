"""Sovereign Store walking skeleton — extra budget, Pydantic/stdlib only."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.events import append_event
from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import Signal


@dataclass
class Product:
    sku: str
    name: str
    unit_cost_cents: int
    price_cents: int


@dataclass
class InventoryPosition:
    sku: str
    on_hand: int
    reserved: int
    reorder_point: int


def seed(db: Database) -> None:
    product = Product(sku="SKU-TEA", name="Assam tea", unit_cost_cents=120, price_cents=400)
    with db.transaction():
        db.connection.execute(
            "INSERT OR REPLACE INTO products(sku, record) VALUES (?, ?)",
            (product.sku, json.dumps(product.__dict__)),
        )
        db.connection.execute(
            "INSERT OR REPLACE INTO inventory("
            "sku, on_hand, reserved, reorder_point, record) VALUES (?, ?, ?, ?, ?)",
            (product.sku, 4, 0, 3, json.dumps({"sku": product.sku})),
        )
        db.connection.execute(
            "INSERT OR REPLACE INTO cash_entries(id, amount_cents, record) VALUES (?, ?, ?)",
            ("cash-opening", 10_000, json.dumps({"reason": "opening"})),
        )
        append_event(db, "store.seeded", {"sku": product.sku})


def record_sale(db: Database, sku: str, quantity: int, unit_price_cents: int) -> Signal:
    """Mutate inventory and cash in the same transaction as the recording event."""
    row = db.connection.execute(
        "SELECT on_hand, reorder_point FROM inventory WHERE sku = ?", (sku,)
    ).fetchone()
    if row is None:
        raise Refusal(
            "Unknown SKU.", "Actors cannot invent inventory.", "inventory list", "Seed the catalog."
        )
    on_hand = int(row["on_hand"]) - quantity
    if on_hand < 0:
        raise Refusal(
            "Sale would go negative.",
            "The ledger refuses unrecorded stock.",
            "status",
            "Restock first.",
        )
    cash_id = new_id("cash")
    signal = Signal(
        id=new_id("sig"),
        kind="inventory.changed",
        source="sale",
        subject_ref=sku,
        severity="warning" if on_hand <= int(row["reorder_point"]) else "info",
        observed_at=utc_now(),
        payload_digest=sku,
        dedupe_key=f"inventory:{sku}:{on_hand}",
    )
    with db.transaction():
        db.connection.execute("UPDATE inventory SET on_hand = ? WHERE sku = ?", (on_hand, sku))
        db.connection.execute(
            "INSERT INTO cash_entries(id, amount_cents, record) VALUES (?, ?, ?)",
            (cash_id, quantity * unit_price_cents, json.dumps({"sku": sku, "qty": quantity})),
        )
        db.connection.execute(
            "INSERT OR REPLACE INTO signals(id, dedupe_key, record) VALUES (?, ?, ?)",
            (signal.id, signal.dedupe_key, signal.model_dump_json()),
        )
        append_event(
            db,
            "sale.committed",
            {
                "sku": sku,
                "qty": quantity,
                "on_hand": on_hand,
                "cash_id": cash_id,
                "signal_id": signal.id,
            },
        )
    return signal


def below_reorder(db: Database) -> list[str]:
    rows = db.connection.execute(
        "SELECT sku FROM inventory WHERE on_hand <= reorder_point"
    ).fetchall()
    return [row["sku"] for row in rows]


def cash_balance_cents(db: Database) -> int:
    row = db.connection.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM cash_entries"
    ).fetchone()
    return int(row["total"])
