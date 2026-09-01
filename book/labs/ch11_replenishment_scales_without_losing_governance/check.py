"""Behavioral checker for Chapter 11, including a real two-connection race."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    if getattr(target_module, "STUDENT_TODO", True):
        raise AssertionError("complete the starter and set STUDENT_TODO = False")
    first = target_module.exercise(root)
    second = target_module.exercise(root)
    assert first == second, "reopening and replaying must preserve the same observation"
    assert first["state"] == {"tea_on_hand": 10, "cash_cents": 8200, "effect_count": 1}
    assert first["replay"] == "replay"
    assert first["unauthorized"] == "unauthorized"
    assert first["rollback_preserved_state"] is True

    race_db = root / "race.sqlite3"
    target_module.initialize(race_db)
    request = target_module.Restock(
        "restock:race", "assignment-tea", "signal-tea-low", "SKU-TEA", 6, 300
    )
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    failures: list[str] = []

    def contender() -> None:
        try:
            barrier.wait(timeout=5)
            outcomes.append(target_module.apply_restock(race_db, request))
        except BaseException as exc:  # checker must report thread failures
            failures.append(repr(exc))

    threads = [threading.Thread(target=contender) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    assert not failures, failures
    assert not any(thread.is_alive() for thread in threads)
    assert sorted(outcomes) == ["applied", "replay"]
    assert target_module.snapshot(race_db) == {
        "tea_on_hand": 10,
        "cash_cents": 8200,
        "effect_count": 1,
    }

    conflict = target_module.Restock(
        "restock:race", "assignment-tea", "signal-tea-low", "SKU-TEA", 7, 300
    )
    try:
        target_module.apply_restock(race_db, conflict)
    except ValueError as exc:
        assert str(exc) == "effect_identity_conflict"
    else:
        raise AssertionError("same key with different payload was misclassified as replay")
    return first


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_lab", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    observation = check(_load(Path(sys.argv[1])), Path(sys.argv[2]))
    print(json.dumps(observation, indent=2, sort_keys=True))
