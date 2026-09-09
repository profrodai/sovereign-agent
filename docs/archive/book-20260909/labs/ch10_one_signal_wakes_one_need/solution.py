"""A small executable model of exact causal binding.

This does not imitate the production database.  It isolates the acceptance
invariant so each edge can be attacked independently.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STUDENT_TODO = False


def validate_proof(graph: dict[str, Any]) -> str:
    """Return ACCEPTED or the first deterministic refusal category."""
    expected = graph["expected"]
    if not graph["world"]["condition_true"]:
        return "world_condition_false"

    # Signals and observations corroborate the world condition.  They cannot
    # identify which execution caused the change.
    if not graph["corroboration"]:
        return "missing_corroboration"

    execution = graph["execution"]
    if execution["sow_id"] != expected["sow_id"]:
        return "sibling_proof"
    if execution["outcome_id"] != expected["outcome_id"]:
        return "wrong_outcome"
    if execution["status"] != "completed":
        return "execution_incomplete"

    effect = graph.get("effect")
    if effect is None:
        return "missing_causal_effect"
    if effect["execution_id"] != execution["id"]:
        return "wrong_execution"
    if effect["outcome_id"] != expected["outcome_id"]:
        return "wrong_outcome"
    if effect["subject"] != expected["subject"]:
        return "wrong_subject"
    if effect["kind"] != expected["effect_kind"]:
        return "wrong_effect_kind"
    return "ACCEPTED"


def _base_graph() -> dict[str, Any]:
    return {
        "world": {"condition_true": True, "on_hand": 14, "reorder_at": 10},
        "corroboration": [
            {"kind": "inventory.low", "subject": "SKU-TEA", "on_hand": 8},
            {"kind": "inventory.observed", "subject": "SKU-TEA", "on_hand": 14},
        ],
        "expected": {
            "outcome_id": "outcome-tea",
            "sow_id": "sow-restock-tea",
            "subject": "SKU-TEA",
            "effect_kind": "inventory.restocked",
        },
        "execution": {
            "id": "exec-restock-tea",
            "sow_id": "sow-restock-tea",
            "outcome_id": "outcome-tea",
            "status": "completed",
        },
        "effect": {
            "execution_id": "exec-restock-tea",
            "outcome_id": "outcome-tea",
            "subject": "SKU-TEA",
            "kind": "inventory.restocked",
        },
    }


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    repaired = _base_graph()
    attacks: dict[str, dict[str, Any]] = {}

    attacks["world_only"] = json.loads(json.dumps(repaired))
    attacks["world_only"]["effect"] = None

    attacks["sibling_proof"] = json.loads(json.dumps(repaired))
    attacks["sibling_proof"]["execution"]["sow_id"] = "sow-audit-sibling"

    attacks["wrong_execution"] = json.loads(json.dumps(repaired))
    attacks["wrong_execution"]["effect"]["execution_id"] = "exec-older-replenishment"

    attacks["wrong_subject"] = json.loads(json.dumps(repaired))
    attacks["wrong_subject"]["effect"]["subject"] = "SKU-CONE"

    result: dict[str, object] = {
        "principle": "corroboration_is_not_causal_binding",
        "attacks": {name: validate_proof(graph) for name, graph in attacks.items()},
        "repaired": validate_proof(repaired),
        "proof_edges": [
            "outcome->sow",
            "sow->execution",
            "execution->effect",
            "effect->subject",
        ],
    }
    (root / "proof-graph.json").write_text(
        json.dumps(repaired, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
