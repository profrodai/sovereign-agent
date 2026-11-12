"""Count the entire installed teaching distribution, with a visible core subtotal.

Supersedes verify_source_budget.py for the always-on curriculum. Allowance:
docs/rulings/2026-09-07-always-on-source-budget.md, with the measured research
amendments in docs/rulings/2026-10-24-research-profile-source-budget.md and
docs/rulings/2026-10-25-research-continuation-source-budget.md and
docs/rulings/2026-10-31-private-paper-assessment-source-budget.md.
Legacy script remains history.
"""

from __future__ import annotations

import sys
from pathlib import Path

from verify_source_budget import MAX_ROOT_EXPORTS, root_exports

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "src" / "sovereign_agent"
MAX_CORE_MODULES = 55
MAX_CORE_LINES = 12_261
MAX_INSTALLED_MODULES = 80
MAX_INSTALLED_LINES = 15_500


def measure(root: Path) -> tuple[int, int]:
    files = list(root.rglob("*.py"))
    return len(files), sum(
        bool(line.strip()) for path in files for line in path.read_text().splitlines()
    )


def main() -> int:
    modules, lines = measure(CORE)
    installed_modules, installed_lines = measure(ROOT / "src")
    exports = len(root_exports())
    print(
        f"modules={modules}/{MAX_CORE_MODULES} nonblank_lines={lines}/{MAX_CORE_LINES} "
        f"root_exports={exports}/{MAX_ROOT_EXPORTS}"
    )
    print(
        f"installed_modules={installed_modules}/{MAX_INSTALLED_MODULES} "
        f"installed_nonblank_lines={installed_lines}/{MAX_INSTALLED_LINES}"
    )
    failures = [
        label
        for label, count, limit in (
            ("core modules", modules, MAX_CORE_MODULES),
            ("core lines", lines, MAX_CORE_LINES),
            ("installed modules", installed_modules, MAX_INSTALLED_MODULES),
            ("installed lines", installed_lines, MAX_INSTALLED_LINES),
            ("root exports", exports, MAX_ROOT_EXPORTS),
        )
        if count > limit
    ]
    for failure in failures:
        print(f"FAIL: {failure} exceeds authorized budget")
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
