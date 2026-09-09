"""Chapter 8: the Store becomes a catalog.

Chapters 0-7 each seeded exactly one product, SKU-TEA, via
`reference_organizations.store.seed`. That fixture is untouched -- it still
exists, because every chapter and test written before Unit 11 relies on its
exact single-SKU shape. This chapter uses the genuinely NEW entry point,
`seed_catalog`, which creates a real multi-product catalog: two distinct
SKUs, each with its own row in `products` and its own row in `inventory`,
each carrying its own independent stock level and reorder point. Imports the
production package throughout; nothing here re-implements catalog seeding.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reference_organizations.store import DEFAULT_CATALOG, seed_catalog


def the_store_becomes_a_catalog(root: Path) -> dict[str, Any]:
    from sovereign_agent.database import Database

    db = Database(root / ".sovereign" / "organization.db")
    products = seed_catalog(db)

    product_rows = db.connection.execute("SELECT sku, record FROM products ORDER BY sku").fetchall()
    inventory_rows = db.connection.execute(
        "SELECT sku, on_hand, reserved, reorder_point FROM inventory ORDER BY sku"
    ).fetchall()

    return {
        "catalog_size": {
            "distinct_skus_seeded": len(products),
            "skus": sorted(p.sku for p in products),
            "at_least_two": len(products) >= 2,
        },
        "products_table": [
            {"sku": row["sku"], "record": json.loads(row["record"])} for row in product_rows
        ],
        "inventory_table": [
            {
                "sku": row["sku"],
                "on_hand": row["on_hand"],
                "reserved": row["reserved"],
                "reorder_point": row["reorder_point"],
            }
            for row in inventory_rows
        ],
        "independent_reorder_points": {
            "distinct_reorder_points": sorted({row["reorder_point"] for row in inventory_rows}),
            "not_all_the_same": len({row["reorder_point"] for row in inventory_rows}) > 1,
        },
        "default_catalog_entry_count": len(DEFAULT_CATALOG),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(the_store_becomes_a_catalog(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
