from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import NamedTuple

STUDENT_TODO = True


class ProofBinding(NamedTuple):
    sow_id: str
    execution_id: str
    required_effect: str


def digest_state(state: dict[str, int]) -> str:
    """Digest the complete state observed by a check."""
    # TODO(1): Use canonical JSON so insertion order cannot change the digest.
    payload = json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_case(case: dict[str, object], binding: ProofBinding) -> str:
    """Return accepted or the first actionable rejection reason."""
    # TODO(2): Reject stale state and evidence borrowed from another binding.
    # TODO(3): Require this execution—not an older sibling—to carry the declared effect.
    raise NotImplementedError("Implement the layered proof joins")


def exercise(root: Path) -> dict[str, object]:
    """Reject stale, borrowed, and noncausal evidence independently."""
    raise NotImplementedError("Implement the layered acceptance verifier and mutation battery")
