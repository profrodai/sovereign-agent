#!/usr/bin/env python3
"""Set a SKU's on-hand stock to zero, behind the organization's back.

The quickstart uses this to show that `ACCEPTED` records a decision that was
made, while the world can move afterwards. It exists as a script because the
inline one-liner it replaced used Bash quoting on a page that also gives Windows
instructions — a command that cannot be pasted on the platform it is shown to.

    python scripts/empty_the_shelf.py <organization-root> [SKU]
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print(__doc__)
        return 2
    root = Path(argv[1]).resolve()
    sku = argv[2] if len(argv) == 3 else "SKU-TEA"
    database = root / ".sovereign" / "organization.db"
    if not database.is_file():
        print(f"no organization at {root}")
        return 2
    connection = sqlite3.connect(database)
    try:
        changed = connection.execute(
            "UPDATE inventory SET on_hand = 0 WHERE sku = ?", (sku,)
        ).rowcount
        connection.commit()
    finally:
        connection.close()
    if not changed:
        print(f"no inventory row for {sku}")
        return 1
    print(f"{sku} on_hand set to 0 — now run: sovereign-agent inspect --root {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
