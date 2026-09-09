from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    result = target_module.exercise(root)
    trace_path = root / "trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    expected_digest = hashlib.sha256(
        json.dumps(trace["observed"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    kinds = [event["kind"] for event in trace["events"]]
    # The deliberately naive policy accepts the provider's self-report. The
    # governed policy below requires the independent records as well.
    assert result["naive_provider_claim_accepted"] is True
    assert result["governed_trace_accepted"] is True
    assert result["event_order"] == kinds
    assert result["evidence_digest"] == expected_digest
    assert kinds.index("evidence.recorded") < kinds.index("review.approved")
    assert kinds.index("review.approved") < kinds.index("outcome.accepted")
    actors = {
        trace["events"][0]["actor"],
        trace["events"][3]["actor"],
        trace["events"][4]["actor"],
    }
    assert len(actors) == 3
    return {
        "accepted_only_with_full_trace": True,
        "independent_actors": 3,
        "ordered_stages": len(kinds),
        "provider_report_is_not_proof": True,
    }
