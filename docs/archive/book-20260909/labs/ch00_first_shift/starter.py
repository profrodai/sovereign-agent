from __future__ import annotations

import hashlib
import json
from pathlib import Path

STUDENT_TODO = True
REQUIRED_STAGES = (
    "assignment.created",
    "evidence.recorded",
    "review.approved",
    "outcome.accepted",
)


def digest_observation(observed: dict[str, object]) -> str:
    """Return a stable digest of exactly the fact that was checked."""
    # TODO(1): Canonicalize the observation before hashing it.
    encoded = json.dumps(observed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def actors_are_independent(actor_ids: list[str]) -> bool:
    """Decide whether assignment, review, and acceptance use distinct actors."""
    # TODO(2): Compare cardinality after deduplication; pairwise chains are insufficient.
    return len(set(actor_ids)) == len(actor_ids)


def exercise(root: Path) -> dict[str, object]:
    """Create and validate a durable authority/data trace."""
    # TODO(3): Persist an ordered trace under root and reject a provider-only claim.
    raise NotImplementedError("Build the assignment -> evidence -> review -> acceptance trace")
