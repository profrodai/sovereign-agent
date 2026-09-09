"""Chapter 9: each product has its own threshold.

Chapter 8 proved the catalog itself is independent, row by row, before any
sale happened. This chapter proves the same independence holds once real
sales are involved: selling SKU-TEA down past its own reorder point leaves
SKU-COFFEE's stock and reorder state completely untouched, and selling a
SMALL amount of SKU-COFFEE (still above its own, higher reorder point)
correctly does NOT flag it, even though the same-shaped sale already
flagged SKU-TEA. Imports the production package throughout -- `record_sale`
and `below_reorder` are the same functions Chapters 0-7 already used for one
SKU, unmodified, now proven across two.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reference_organizations.store import below_reorder, record_sale, seed_catalog
from sovereign_agent.database import Database

TEA = "SKU-TEA"
COFFEE = "SKU-COFFEE"


def each_product_has_its_own_threshold(root: Path) -> dict[str, Any]:
    db = Database(root / ".sovereign" / "organization.db")
    seed_catalog(db)

    before = {
        row["sku"]: {"on_hand": row["on_hand"], "reorder_point": row["reorder_point"]}
        for row in db.connection.execute(
            "SELECT sku, on_hand, reorder_point FROM inventory ORDER BY sku"
        ).fetchall()
    }

    # Sell enough tea to cross ITS OWN reorder point (4 on hand, reorder at 3).
    tea_signal = record_sale(db, TEA, 2, 400)
    after_tea_sale = {
        row["sku"]: row["on_hand"]
        for row in db.connection.execute("SELECT sku, on_hand FROM inventory").fetchall()
    }
    below_after_tea = below_reorder(db)

    # Sell a small amount of coffee -- NOT enough to cross ITS OWN, higher
    # reorder point (10 on hand, reorder at 6): one unit leaves 9, still
    # above 6.
    coffee_signal = record_sale(db, COFFEE, 1, 650)
    below_after_small_coffee_sale = below_reorder(db)

    return {
        "opening_positions": before,
        "tea_sale": {
            "signal_id": tea_signal.id,
            "signal_severity": tea_signal.severity,
            "on_hand_after": after_tea_sale[TEA],
            "coffee_on_hand_unaffected": after_tea_sale[COFFEE] == before[COFFEE]["on_hand"],
        },
        "below_reorder_after_tea_sale": below_after_tea,
        "small_coffee_sale": {
            "signal_id": coffee_signal.id,
            "signal_severity": coffee_signal.severity,
            "on_hand_after": db.connection.execute(
                "SELECT on_hand FROM inventory WHERE sku = ?", (COFFEE,)
            ).fetchone()["on_hand"],
        },
        "below_reorder_after_small_coffee_sale": below_after_small_coffee_sale,
        "each_sku_evaluated_against_its_own_threshold": {
            "tea_flagged_at_its_own_lower_threshold": TEA in below_after_tea,
            "coffee_not_flagged_by_a_sale_still_above_its_own_higher_threshold": COFFEE
            not in below_after_small_coffee_sale,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(each_product_has_its_own_threshold(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
