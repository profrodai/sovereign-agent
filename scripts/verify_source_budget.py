"""Enforce the educational package's module, line, and export budgets."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "sovereign_agent"
MAX_MODULES = 40
MAX_NONBLANK_LINES = 6_000
MAX_ROOT_EXPORTS = 30


def root_exports() -> list[str]:
    tree = ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return value
    raise ValueError("sovereign_agent.__all__ must be a literal list of strings")


def main() -> int:
    modules = sorted(PACKAGE.rglob("*.py"))
    nonblank_lines = sum(
        1
        for path in modules
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    exports = root_exports()
    failures: list[str] = []
    if len(modules) > MAX_MODULES:
        failures.append(f"{len(modules)} modules exceeds {MAX_MODULES}")
    if nonblank_lines > MAX_NONBLANK_LINES:
        failures.append(f"{nonblank_lines} nonblank lines exceeds {MAX_NONBLANK_LINES}")
    if len(exports) > MAX_ROOT_EXPORTS:
        failures.append(f"{len(exports)} root exports exceeds {MAX_ROOT_EXPORTS}")

    print(
        f"modules={len(modules)}/{MAX_MODULES} "
        f"nonblank_lines={nonblank_lines}/{MAX_NONBLANK_LINES} "
        f"root_exports={len(exports)}/{MAX_ROOT_EXPORTS}"
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
