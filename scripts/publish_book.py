#!/usr/bin/env python3
"""Regenerate the published copies of book/ under docs/book/.

book/ is the source of truth. docs/book/ is a projection for the site, exactly
as governance Markdown is a projection of the ledger: generated, never
hand-edited, and verified by scripts/verify_curriculum.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from verify_curriculum import BOOK, PUBLISHED, render_published  # noqa: E402


def main() -> int:
    out = REPO_ROOT / "docs" / "book"
    out.mkdir(parents=True, exist_ok=True)
    for source_rel, published_rel in PUBLISHED.items():
        text = (BOOK / source_rel).read_text(encoding="utf-8")
        (out / published_rel).write_text(render_published(text), encoding="utf-8")
    print(f"published {len(PUBLISHED)} chapter page(s) into docs/book/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
