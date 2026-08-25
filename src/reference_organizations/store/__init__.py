"""Sovereign Store walking skeleton — extra budget, Pydantic/stdlib only."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.events import append_event
from sovereign_agent.evidence import digest_payload
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


@dataclass(frozen=True)
class RestockProposal:
    """What an intelligence provider is allowed to ASK for.

    A provider fills this in. It carries no authority: every field is re-checked
    by `apply_restock` against the ledger before anything is written. Note what
    is absent — there is no price, no cost, and no cash amount. Cost comes from
    the product record, so a provider cannot talk the organization into paying
    more by writing a bigger number.
    """

    sku: str
    quantity: int


MAX_RESTOCK_UNITS = 50


def _state_digest(db: Database, sku: str) -> str:
    """Digest the exact facts a check reads: inventory row plus cash total.

    An event counter cannot see a silent `UPDATE inventory`. This digest changes
    if and only if one of the values a check depends on changes.
    """
    row = db.connection.execute(
        "SELECT on_hand, reserved, reorder_point FROM inventory WHERE sku = ?", (sku,)
    ).fetchone()
    facts = {
        "sku": sku,
        "on_hand": None if row is None else int(row["on_hand"]),
        "reserved": None if row is None else int(row["reserved"]),
        "reorder_point": None if row is None else int(row["reorder_point"]),
        "cash_cents": cash_balance_cents(db),
    }
    return digest_payload(facts)


def validate_restock(db: Database, proposal: RestockProposal) -> tuple[int, int]:
    """Refuse an unsound proposal. Returns (unit_cost_cents, total_cost_cents).

    This is the trusted boundary. It runs in Python, reads authoritative rows,
    and never consults the provider for a value it can look up itself.
    """
    if proposal.quantity <= 0:
        raise Refusal(
            f"Proposed restock quantity {proposal.quantity} is not positive.",
            "An effect must move the world in the direction it claims.",
            "sovereign-agent status",
            "Propose a quantity of at least 1.",
        )
    if proposal.quantity > MAX_RESTOCK_UNITS:
        raise Refusal(
            f"Proposed restock of {proposal.quantity} exceeds the bound of {MAX_RESTOCK_UNITS}.",
            "Bounded authority: a provider may propose, but not without limit.",
            "sovereign-agent status",
            f"Propose at most {MAX_RESTOCK_UNITS} units.",
        )
    product = db.connection.execute(
        "SELECT record FROM products WHERE sku = ?", (proposal.sku,)
    ).fetchone()
    if product is None:
        raise Refusal(
            f"Unknown SKU {proposal.sku}.",
            "Actors cannot invent a product by naming one.",
            "sqlite3 .sovereign/organization.db 'select sku from products'",
            "Propose a SKU that exists in the catalog.",
        )
    if (
        db.connection.execute("SELECT 1 FROM inventory WHERE sku = ?", (proposal.sku,)).fetchone()
        is None
    ):
        raise Refusal(
            f"No inventory row for {proposal.sku}.",
            "Restock adjusts a position that must already exist.",
            "sovereign-agent status",
            "Seed the catalog first.",
        )
    unit_cost = int(json.loads(product["record"])["unit_cost_cents"])
    total = unit_cost * proposal.quantity
    balance = cash_balance_cents(db)
    if total > balance:
        raise Refusal(
            f"Restock costs {total} but only {balance} cash is available.",
            "The organization refuses to spend money it does not have.",
            "sovereign-agent status",
            "Propose a smaller quantity.",
        )
    return unit_cost, total


def apply_restock(
    db: Database, proposal: RestockProposal, assignment_id: str, signal_id: str | None = None
) -> dict[str, object]:
    """Validate, then commit inventory, cash, and the event in ONE transaction.

    Idempotent per assignment: replaying the same assignment is a no-op, so a
    retried execution cannot double-order stock.
    """
    # Idempotency is keyed on (assignment, sku). Keying on the assignment alone
    # would let a replay for one product silently report success for another.
    existing = db.connection.execute(
        "SELECT payload FROM events WHERE kind = 'replenishment.committed'"
    ).fetchall()
    for row in existing:
        payload = json.loads(row["payload"])
        if (payload.get("assignment_id"), payload.get("sku")) == (
            assignment_id,
            proposal.sku,
        ):
            return {**payload, "idempotent_replay": True}

    unit_cost, total = validate_restock(db, proposal)
    cash_id = new_id("cash")
    with db.transaction():
        db.connection.execute(
            "UPDATE inventory SET on_hand = on_hand + ? WHERE sku = ?",
            (proposal.quantity, proposal.sku),
        )
        # Purchases are NEGATIVE: cash leaves the organization to buy stock.
        db.connection.execute(
            "INSERT INTO cash_entries(id, amount_cents, record) VALUES (?, ?, ?)",
            (
                cash_id,
                -total,
                json.dumps(
                    {
                        "reason": "purchase",
                        "sku": proposal.sku,
                        "qty": proposal.quantity,
                        "unit_cost_cents": unit_cost,
                        "assignment_id": assignment_id,
                    }
                ),
            ),
        )
        if signal_id is not None:
            db.connection.execute(
                "UPDATE signals SET record = json_set(record, '$.severity', 'resolved') "
                "WHERE id = ?",
                (signal_id,),
            )
        row = db.connection.execute(
            "SELECT on_hand FROM inventory WHERE sku = ?", (proposal.sku,)
        ).fetchone()
        payload = {
            "sku": proposal.sku,
            "qty": proposal.quantity,
            "unit_cost_cents": unit_cost,
            "total_cost_cents": total,
            "on_hand": int(row["on_hand"]),
            "cash_id": cash_id,
            "assignment_id": assignment_id,
            "signal_id": signal_id,
        }
        append_event(db, "replenishment.committed", payload)
    return payload
