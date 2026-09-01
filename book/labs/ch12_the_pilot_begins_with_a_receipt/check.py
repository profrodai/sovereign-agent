"""Behavioral checker for the Chapter 12 pilot and evidence lab."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    if getattr(target_module, "STUDENT_TODO", True):
        raise AssertionError("complete the starter and set STUDENT_TODO = False")
    first = target_module.exercise(root)
    second = target_module.exercise(root)
    assert first == second, "pilot replay across invocations must be stable"
    assert first["pilot"] == {
        "pilots": ["pilot-lucy-01"],
        "active": "pilot-lucy-01",
        "started_events": 1,
    }
    assert first["replay"] == "replay"
    assert first["no_orphan_after_fault"] is True
    proof = first["proof_pack"]
    assert proof["valid_failures"] == []
    assert proof["attacks"] == {
        "path_escape": ["path_escape"],
        "digest_mismatch": ["digest_mismatch"],
        "not_run_lie": ["not_run_success_claim"],
    }
    assert proof["internally_consistent"] is True
    assert proof["authenticated"] is False

    isolated = root / "fault-only.sqlite3"
    target_module.initialize(isolated)
    request = target_module.PilotStart("pilot-fault", "store", "profile", "ns")
    try:
        target_module.start_pilot(isolated, request, fault="after_pilot")
    except RuntimeError as exc:
        assert str(exc) == "injected_after_pilot"
    else:
        raise AssertionError("fault injection did not interrupt pilot start")
    assert target_module.pilot_snapshot(isolated) == {
        "pilots": [],
        "active": None,
        "started_events": 0,
    }

    conflict = target_module.PilotStart(
        "pilot-lucy-01", "store-lucy", "profile-changed", "evidence/lucy-01"
    )
    try:
        target_module.start_pilot(root / "pilot.sqlite3", conflict)
    except ValueError as exc:
        assert str(exc) == "pilot_identity_conflict"
    else:
        raise AssertionError("same pilot id with changed identity was accepted as replay")

    before_other = target_module.pilot_snapshot(root / "pilot.sqlite3")
    other = target_module.PilotStart(
        "pilot-lucy-02", "store-lucy", "profile-safe", "evidence/lucy-02"
    )
    try:
        target_module.start_pilot(root / "pilot.sqlite3", other)
    except ValueError as exc:
        assert str(exc) == "pilot_already_active"
    else:
        raise AssertionError("a different pilot occupied an already active singleton slot")
    assert target_module.pilot_snapshot(root / "pilot.sqlite3") == before_other, (
        "refusing a different active pilot must roll back its inserted row"
    )
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
