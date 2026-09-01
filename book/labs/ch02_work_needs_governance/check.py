from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    result = target_module.exercise(root)
    expected_verdicts = {
        "valid": "accepted",
        "stale": "stale_evidence",
        "borrowed": "borrowed_evidence",
        "noncausal": "noncausal_execution",
    }
    assert result["layered_verdicts"] == expected_verdicts
    assert result["naive_condition_only_accepts"] == ["borrowed", "noncausal", "stale", "valid"]
    assert result["rejected_mutations"] == 3
    cases = json.loads((root / "proof-cases.json").read_text(encoding="utf-8"))
    assert cases["borrowed"]["evidence_sow"] != cases["borrowed"]["sow"]
    assert cases["noncausal"]["condition_true"] is True
    assert cases["stale"]["current_state"] != cases["valid"]["current_state"]
    return {
        "valid_proof_accepted": True,
        "stale_proof_rejected": True,
        "borrowed_proof_rejected": True,
        "noncausal_proof_rejected": True,
    }
