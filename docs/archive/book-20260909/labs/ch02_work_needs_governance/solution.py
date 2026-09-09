from __future__ import annotations

import hashlib
import json
from pathlib import Path

STUDENT_TODO = False


def _digest(state: dict[str, int]) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _verify(case: dict[str, object]) -> str:
    if not case["condition_true"]:
        return "condition_false"
    if case["evidence_digest"] != _digest(case["current_state"]):
        return "stale_evidence"
    if case["evidence_sow"] != case["sow"] or case["evidence_execution"] != case["execution"]:
        return "borrowed_evidence"
    if case["required_effect"] not in case["effects_by_execution"].get(case["execution"], []):
        return "noncausal_execution"
    return "accepted"


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    state = {"on_hand": 8, "reorder_point": 5}
    valid: dict[str, object] = {
        "condition_true": True,
        "current_state": state,
        "evidence_digest": _digest(state),
        "sow": "sow-a",
        "execution": "asg-a",
        "evidence_sow": "sow-a",
        "evidence_execution": "asg-a",
        "required_effect": "replenishment",
        "effects_by_execution": {"asg-a": ["replenishment"]},
    }
    cases = {
        "valid": valid,
        "stale": {**valid, "current_state": {"on_hand": 9, "reorder_point": 5}},
        "borrowed": {**valid, "evidence_sow": "sow-b", "evidence_execution": "asg-b"},
        "noncausal": {**valid, "effects_by_execution": {"asg-older": ["replenishment"]}},
    }
    verdicts = {name: _verify(case) for name, case in cases.items()}
    (root / "proof-cases.json").write_text(
        json.dumps(cases, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "naive_condition_only_accepts": sorted(cases),
        "layered_verdicts": verdicts,
        "rejected_mutations": sum(verdict != "accepted" for verdict in verdicts.values()),
    }
