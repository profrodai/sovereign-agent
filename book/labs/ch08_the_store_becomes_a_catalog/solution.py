"""Reference solution for Chapter 8's populated catalog migration lab."""

from __future__ import annotations

import sqlite3
from pathlib import Path

STUDENT_TODO = False


LEGACY_SCHEMA = """
CREATE TABLE catalog_v1 (
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    on_hand INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL
);
"""

MIGRATION = """
CREATE TABLE products (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents > 0)
);
CREATE TABLE inventory (
    sku TEXT PRIMARY KEY REFERENCES products(sku),
    on_hand INTEGER NOT NULL CHECK (on_hand >= 0),
    reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved >= 0 AND reserved <= on_hand),
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0)
);
INSERT INTO products(sku, name, price_cents)
    SELECT sku, name, price_cents FROM catalog_v1;
INSERT INTO inventory(sku, on_hand, reserved, reorder_point)
    SELECT sku, on_hand, 0, reorder_point FROM catalog_v1;
DROP TABLE catalog_v1;
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
INSERT INTO schema_migrations VALUES (2, '2026-09-01T00:00:00Z');
"""


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed_legacy(path: Path, *, duplicate: bool) -> None:
    if path.exists():
        path.unlink()
    connection = _connect(path)
    connection.executescript(LEGACY_SCHEMA)
    connection.executemany(
        "INSERT INTO catalog_v1 VALUES (?, ?, ?, ?, ?)",
        [
            ("SKU-TEA", "Assam tea", 400, 4, 3),
            ("SKU-COFFEE", "Kenyan coffee", 650, 10, 6),
        ],
    )
    if duplicate:
        connection.execute(
            "INSERT INTO catalog_v1 VALUES ('SKU-TEA', 'Conflicting tea', 999, 99, 9)"
        )
    connection.close()


def _migrate(connection: sqlite3.Connection) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        # executescript would commit an open transaction implicitly. Execute
        # the known statements one by one so rollback covers the whole copy.
        statements = [statement.strip() for statement in MIGRATION.split(";") if statement.strip()]
        for statement in statements:
            connection.execute(statement)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def _tables(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [str(row["name"]) for row in rows]


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    valid_path = root / "catalog-valid.sqlite3"
    invalid_path = root / "catalog-duplicate.sqlite3"

    _seed_legacy(valid_path, duplicate=False)
    valid = _connect(valid_path)
    before = valid.execute("SELECT COUNT(*) FROM catalog_v1").fetchone()[0]
    _migrate(valid)
    products = [
        dict(row)
        for row in valid.execute(
            "SELECT p.sku, p.name, p.price_cents, i.on_hand, i.reserved, i.reorder_point "
            "FROM products p JOIN inventory i USING (sku) ORDER BY p.sku"
        ).fetchall()
    ]

    constraint_results: dict[str, str] = {}
    for name, statement in {
        "negative_stock": "UPDATE inventory SET on_hand=-1 WHERE sku='SKU-TEA'",
        "reserved_above_stock": "UPDATE inventory SET reserved=5 WHERE sku='SKU-TEA'",
        "orphan_inventory": "INSERT INTO inventory VALUES ('SKU-MISSING', 1, 0, 0)",
    }.items():
        try:
            valid.execute(statement)
        except sqlite3.IntegrityError:
            constraint_results[name] = "refused"
        else:
            constraint_results[name] = "accepted"
    valid_after = valid.execute(
        "SELECT on_hand, reserved FROM inventory WHERE sku='SKU-TEA'"
    ).fetchone()
    valid_tables = _tables(valid)
    valid.close()

    _seed_legacy(invalid_path, duplicate=True)
    invalid = _connect(invalid_path)
    failure = "none"
    try:
        _migrate(invalid)
    except sqlite3.IntegrityError:
        failure = "duplicate_sku_refused"
    duplicate_rows = invalid.execute("SELECT COUNT(*) FROM catalog_v1").fetchone()[0]
    invalid_tables = _tables(invalid)
    invalid.close()

    return {
        "successful_migration": {
            "rows_before": before,
            "rows_after": len(products),
            "tables": valid_tables,
            "products": products,
            "constraints": constraint_results,
            "tea_after_refusals": dict(valid_after),
        },
        "duplicate_migration": {
            "result": failure,
            "legacy_rows_preserved": duplicate_rows,
            "tables_after_rollback": invalid_tables,
        },
    }
