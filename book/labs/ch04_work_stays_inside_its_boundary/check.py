"""Deterministic checker for the Chapter 4 companion lab."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    observed = target_module.exercise(root)
    assert observed["naive_accepts_traversal"] is True
    assert observed["repaired_refusals"] == ["absolute", "symlink", "traversal"]
    assert observed["nested_output"] == "output/report.json"
    assert observed["receipt_digest_matches"] is True
    assert observed["boundary_changed"] == ["policy.txt"]
    assert observed["boundary_scope"] == "organization_root_excluding_workspace_and_ledger"
    assert observed["ledger_change_visible"] is False
    return observed


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_ch04", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python check.py TARGET.py ROOT")
    print(json.dumps(check(_load(Path(sys.argv[1])), Path(sys.argv[2])), sort_keys=True, indent=2))
