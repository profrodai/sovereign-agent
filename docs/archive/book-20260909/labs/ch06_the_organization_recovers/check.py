"""Deterministic checker for the Chapter 6 companion lab."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    observed = target_module.exercise(root)
    assert observed["naive_output_guess"] == "COMPLETED"
    assert observed["injected_recovery_won"] is False
    assert observed["rollback_state"] == "RUNNING"
    assert observed["rollback_fence"] == "attempt-7"
    assert observed["rollback_receipts"] == 0
    assert observed["supervisor_winners"] == 1
    assert observed["terminal_state"] == "FAILED"
    assert observed["fence_released"] is True
    assert observed["receipt_status"] == "failed"
    assert observed["failure_category"] == "worker_lost"
    assert observed["receipt_count"] == 1
    return observed


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_ch06", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python check.py TARGET.py ROOT")
    print(json.dumps(check(_load(Path(sys.argv[1])), Path(sys.argv[2])), sort_keys=True, indent=2))
