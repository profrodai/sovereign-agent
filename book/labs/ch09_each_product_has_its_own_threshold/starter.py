"""Starter for Chapter 9's invariant-preserving sale lab."""

from __future__ import annotations

import sqlite3
from pathlib import Path

STUDENT_TODO = True

SCHEMA = """
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
CREATE TABLE cash_entries (sale_id TEXT PRIMARY KEY, amount_cents INTEGER NOT NULL);
CREATE TABLE events (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);
"""


class SaleError(RuntimeError):
    """A domain refusal that should leave every sale table unchanged."""


def record_sale(
    connection: sqlite3.Connection,
    sale_id: str,
    sku: str,
    quantity: int,
    *,
    fail_after_cash: bool = False,
) -> dict[str, int | str]:
    """Commit inventory, cash, and event as one fact."""
    # TODO(1): BEGIN IMMEDIATE before reading the product and inventory rows.
    # TODO(2): Refuse quantity > on_hand - reserved, then calculate the cash
    # amount from quantity * the catalog's price_cents.
    # TODO(3): Update inventory and insert cash plus event in the same
    # transaction. Use fail_after_cash to prove an exception rolls all back.
    raise NotImplementedError("implement an invariant-preserving sale")


def exercise(root: Path) -> dict[str, object]:
    """Prove price, reservation, rollback, and contention invariants."""
    # TODO(4): Observe a reservation refusal, one successful two-unit sale,
    # and the state before/after the injected failure.
    # TODO(5): Race two independent connections selling two of three units;
    # report statuses without exposing the nondeterministic winner identity.
    raise NotImplementedError("assemble the Chapter 9 sale experiments")
