"""Behavioral checker for the Chapter 10 lab."""

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
    assert first == second, "the exercise must be idempotent"
    assert first["repaired"] == "ACCEPTED"
    assert first["attacks"] == {
        "world_only": "missing_causal_effect",
        "sibling_proof": "sibling_proof",
        "wrong_execution": "wrong_execution",
        "wrong_subject": "wrong_subject",
    }
    saved = json.loads((root / "proof-graph.json").read_text(encoding="utf-8"))
    assert target_module.validate_proof(saved) == "ACCEPTED"
    assert saved["corroboration"][0]["on_hand"] < saved["world"]["reorder_at"]
    assert saved["world"]["on_hand"] >= saved["world"]["reorder_at"], (
        "a successful restock proof must end in a healthy current observation"
    )

    mutant = json.loads(json.dumps(saved))
    mutant["effect"]["outcome_id"] = "outcome-cones"
    assert target_module.validate_proof(mutant) == "wrong_outcome"
    mutant = json.loads(json.dumps(saved))
    mutant["effect"]["kind"] = "inventory.observed"
    assert target_module.validate_proof(mutant) == "wrong_effect_kind"
    return first


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_lab", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    observation = check(_load(Path(sys.argv[1])), Path(sys.argv[2]))
    print(json.dumps(observation, indent=2, sort_keys=True))
