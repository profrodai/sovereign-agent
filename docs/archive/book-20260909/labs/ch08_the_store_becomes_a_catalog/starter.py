"""Starter for Chapter 8's populated catalog migration lab."""

from __future__ import annotations

import sqlite3
from pathlib import Path

STUDENT_TODO = True

LEGACY_SCHEMA = """
CREATE TABLE catalog_v1 (
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    on_hand INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL
);
"""

VALID_ROWS: tuple[tuple[str, str, int, int, int], ...] = (
    ("SKU-TEA", "Assam tea", 400, 4, 3),
    ("SKU-COFFEE", "Kenyan coffee", 650, 10, 6),
)


def migrate(connection: sqlite3.Connection) -> None:
    """Normalize catalog_v1 without losing its populated rows."""
    # TODO(1): Begin one IMMEDIATE transaction and create products/inventory.
    # Put positive-price, nonnegative-stock, reservation, and foreign-key
    # invariants in the schema rather than relying only on Python checks.
    # TODO(2): Copy with plain INSERT so duplicate identity fails closed. Do
    # not use executescript: it can commit before the migration is complete.
    # TODO(3): Drop catalog_v1 and stamp the migration only after both copies
    # succeed; roll back every DDL and DML statement on any exception.
    raise NotImplementedError("implement the populated catalog migration")


def exercise(root: Path) -> dict[str, object]:
    """Migrate valid legacy rows and prove duplicate input rolls back."""
    # TODO(4): Run a valid populated upgrade and probe all three constraints.
    # TODO(5): Run a duplicate-SKU upgrade in another database, then prove the
    # legacy table and all three original rows survived the rollback.
    raise NotImplementedError("assemble the Chapter 8 migration experiments")
