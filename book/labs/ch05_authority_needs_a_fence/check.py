"""Deterministic checker for the Chapter 5 companion lab."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    observed = target_module.exercise(root)
    assert observed["naive_winners"] == 2
    assert observed["cas_winners_before_expiry"] == 1
    assert observed["unexpired_retry_same_token"] is True
    assert observed["expired_takeover_won"] is True
    assert observed["token_increased"] is True
    assert observed["stale_completion_accepted"] is False
    assert observed["current_completion_accepted"] is True
    assert observed["final_state"] == "DONE"
    return observed


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_ch05", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python check.py TARGET.py ROOT")
    print(json.dumps(check(_load(Path(sys.argv[1])), Path(sys.argv[2])), sort_keys=True, indent=2))
