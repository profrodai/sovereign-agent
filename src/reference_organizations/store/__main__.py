"""``python -m reference_organizations.store`` inspection commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reference_organizations.store import below_reorder, cash_balance_cents
from sovereign_agent.organization import Organization


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reference_organizations.store")
    parser.add_argument("--root", type=Path, default=Path("."))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("inventory")
    args = parser.parse_args(argv)
    org = Organization(args.root)
    if args.command == "status":
        print(f"cash_cents={cash_balance_cents(org.db)}")
        print(f"below_reorder={below_reorder(org.db)}")
        return 0
    rows = org.db.connection.execute("SELECT sku, on_hand, reorder_point FROM inventory").fetchall()
    for row in rows:
        print(f"{row['sku']} on_hand={row['on_hand']} reorder={row['reorder_point']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
