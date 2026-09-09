from __future__ import annotations

import hashlib
import json
from pathlib import Path

STUDENT_TODO = False


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def exercise(root: Path) -> dict[str, object]:
    """Show why a provider report is a proposal, not an acceptance decision."""
    root.mkdir(parents=True, exist_ok=True)
    observed = {"sku": "SKU-TEA", "on_hand": 8, "reorder_point": 5}
    evidence_digest = hashlib.sha256(_canonical(observed)).hexdigest()
    events = [
        {"kind": "assignment.created", "actor": "operator-course"},
        {"kind": "provider.reported", "status": "completed"},
        {"kind": "evidence.recorded", "success": True, "digest": evidence_digest},
        {"kind": "review.approved", "actor": "sparring-course"},
        {"kind": "outcome.accepted", "actor": "principal-human"},
    ]
    (root / "trace.json").write_text(
        json.dumps({"observed": observed, "events": events}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    kinds = [str(event["kind"]) for event in events]
    provider_only = "provider.reported" in kinds
    required = {
        "assignment.created",
        "evidence.recorded",
        "review.approved",
        "outcome.accepted",
    }
    governed_actors = {
        events[0]["actor"],
        events[3]["actor"],
        events[4]["actor"],
    }
    independent_actors = len(governed_actors) == 3
    return {
        "naive_provider_claim_accepted": provider_only,
        "governed_trace_accepted": required.issubset(kinds) and independent_actors,
        "event_order": kinds,
        "evidence_digest": evidence_digest,
        "trace_file": "trace.json",
    }
