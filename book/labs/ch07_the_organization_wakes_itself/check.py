"""Executable checker for the Chapter 7 lab."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    observed = target_module.exercise(root)
    assert observed["mechanism"] == "manual_tick", "Pulse is a caller-driven tick, not a scheduler"
    stale = observed["stale_observation"]
    assert stale["was_low_before_restock"] is True
    assert stale["created_after_restock"] is False, "the gate must be revalidated under lock"
    assert stale["work_id"] is None
    assert stale["counts"] == {"decisions": 0, "work": 0}
    race = observed["race"]
    assert race["created_flags"] == [False, True], "exactly one connection must create"
    assert race["returned_work_ids"] == ["work-signal-low"], "the loser must return the winner"
    assert race["counts"] == {"decisions": 1, "work": 1, "origins": 1}
    assert observed["source_chain"] == {
        "signal_id": "signal-low",
        "source_kind": "sale.committed",
        "decision_id": "decision-signal-low",
        "work_id": "work-signal-low",
        "pulse_kind": "pulse.work_created",
    }
    return observed


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_ch07", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    module = _load(Path(sys.argv[1]))
    root = Path(sys.argv[2])
    print(json.dumps(check(module, root), indent=2, sort_keys=True))
