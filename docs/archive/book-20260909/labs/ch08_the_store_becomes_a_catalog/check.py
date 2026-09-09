"""Executable checker for the Chapter 8 lab."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    observed = target_module.exercise(root)
    success = observed["successful_migration"]
    assert success["rows_before"] == success["rows_after"] == 2
    assert success["tables"] == ["inventory", "products", "schema_migrations"]
    assert [row["sku"] for row in success["products"]] == ["SKU-COFFEE", "SKU-TEA"]
    assert success["products"][0]["reorder_point"] == 6
    assert success["products"][1]["reorder_point"] == 3
    assert success["constraints"] == {
        "negative_stock": "refused",
        "reserved_above_stock": "refused",
        "orphan_inventory": "refused",
    }
    assert success["tea_after_refusals"] == {"on_hand": 4, "reserved": 0}
    duplicate = observed["duplicate_migration"]
    assert duplicate == {
        "result": "duplicate_sku_refused",
        "legacy_rows_preserved": 3,
        "tables_after_rollback": ["catalog_v1"],
    }, "a failed copy must leave the legacy schema and all rows intact"
    return observed


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_ch08", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    module = _load(Path(sys.argv[1]))
    print(json.dumps(check(module, Path(sys.argv[2])), indent=2, sort_keys=True))
