"""`seed_catalog`'s OWN validation contract -- distinct from
`tests/test_store_multi_sku.py`'s isolation matrix, which uses `seed_catalog`
only as setup and never tests its refusal behavior directly.

Proves two things Chapter 8 of the book relies on and that were previously
untested in isolation:

1. The cardinality and duplicate-SKU checks run BEFORE `db.transaction()`
   opens, so a refused call leaves the database completely untouched -- not
   partially seeded, not seeded-then-rolled-back, just never written.
2. Removing the pre-transaction duplicate check (the mutation the book's own
   "Break it" exercise reproduces) is not merely a worse error message: it
   changes `INSERT OR REPLACE`'s ordinary last-write-wins semantics into a
   silent data-loss bug where the function's own return value overclaims how
   many distinct products it seeded.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reference_organizations.store import CatalogEntry, Product, seed_catalog
from sovereign_agent.database import Database
from sovereign_agent.events import append_event


def _entries(*, duplicate: bool) -> tuple[CatalogEntry, ...]:
    tea = CatalogEntry(
        product=Product(sku="SKU-TEA", name="Assam tea", unit_cost_cents=120, price_cents=400),
        on_hand=4,
        reorder_point=3,
    )
    coffee = CatalogEntry(
        product=Product(
            sku="SKU-COFFEE", name="Kenyan coffee", unit_cost_cents=210, price_cents=650
        ),
        on_hand=10,
        reorder_point=6,
    )
    if not duplicate:
        return (tea, coffee)
    impostor_tea = CatalogEntry(
        product=Product(sku="SKU-TEA", name="Impostor tea", unit_cost_cents=999, price_cents=999),
        on_hand=99,
        reorder_point=99,
    )
    return (tea, impostor_tea, coffee)


def test_seed_catalog_refuses_a_single_entry_catalog(tmp_path: Path) -> None:
    db = Database(tmp_path / "catalog.db")
    with pytest.raises(ValueError, match="at least two distinct SKUs"):
        seed_catalog(db, _entries(duplicate=False)[:1])
    assert db.connection.execute("SELECT COUNT(*) c FROM products").fetchone()["c"] == 0


def test_seed_catalog_refuses_duplicate_skus_and_writes_nothing(tmp_path: Path) -> None:
    db = Database(tmp_path / "catalog.db")
    with pytest.raises(ValueError, match="duplicate SKUs in catalog"):
        seed_catalog(db, _entries(duplicate=True))
    # The refusal happens BEFORE db.transaction() opens -- zero rows in
    # either table, not a rolled-back partial write.
    assert db.connection.execute("SELECT COUNT(*) c FROM products").fetchone()["c"] == 0
    assert db.connection.execute("SELECT COUNT(*) c FROM inventory").fetchone()["c"] == 0


def test_a_valid_catalog_seeds_exactly_as_many_product_rows_as_entries(tmp_path: Path) -> None:
    db = Database(tmp_path / "catalog.db")
    entries = _entries(duplicate=False)
    products = seed_catalog(db, entries)
    assert len(products) == len(entries)
    row_count = db.connection.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    assert row_count == len(entries)


def _seed_catalog_without_duplicate_check(
    db: Database, entries: tuple[CatalogEntry, ...]
) -> tuple[Product, ...]:
    """The exact mutation the book's 'Break it' exercise reproduces: only the
    cardinality check survives; the `len(set(skus)) != len(skus)` guard is
    removed. Everything else -- the transaction, the INSERT OR REPLACE
    statements, the return value -- is copied verbatim from the production
    `seed_catalog` so the only variable is the missing check."""
    if len(entries) < 2:
        raise ValueError("a catalog needs at least two distinct SKUs")
    with db.transaction():
        for entry in entries:
            db.connection.execute(
                "INSERT OR REPLACE INTO products(sku, record) VALUES (?, ?)",
                (entry.product.sku, json.dumps(entry.product.__dict__)),
            )
            db.connection.execute(
                "INSERT OR REPLACE INTO inventory("
                "sku, on_hand, reserved, reorder_point, record) VALUES (?, ?, ?, ?, ?)",
                (
                    entry.product.sku,
                    entry.on_hand,
                    0,
                    entry.reorder_point,
                    json.dumps({"sku": entry.product.sku}),
                ),
            )
            append_event(db, "store.seeded", {"sku": entry.product.sku})
        db.connection.execute(
            "INSERT OR REPLACE INTO cash_entries(id, amount_cents, record) VALUES (?, ?, ?)",
            ("cash-opening", 10_000, json.dumps({"reason": "opening"})),
        )
    return tuple(entry.product for entry in entries)


def test_removing_the_duplicate_check_makes_the_return_value_overclaim_rows_written(
    tmp_path: Path,
) -> None:
    """The false green the book's exercise exposes: the mutated function does
    NOT raise on a duplicate SKU. It returns a 3-product tuple while the
    database ends up with only 2 product rows -- the second SKU-TEA entry
    silently overwrote the first via ordinary `INSERT OR REPLACE` semantics,
    and nothing in the function's own return value reveals the loss."""
    db = Database(tmp_path / "catalog.db")
    entries = _entries(duplicate=True)
    assert len(entries) == 3

    result = _seed_catalog_without_duplicate_check(db, entries)
    assert len(result) == 3  # the overclaim: return value says 3

    actual_rows = db.connection.execute("SELECT sku, record FROM products").fetchall()
    assert len(actual_rows) == 2  # ground truth: only 2 distinct SKUs exist

    tea_record = json.loads(
        db.connection.execute("SELECT record FROM products WHERE sku = 'SKU-TEA'").fetchone()[
            "record"
        ]
    )
    assert tea_record["name"] == "Impostor tea"  # the real seed data was clobbered
