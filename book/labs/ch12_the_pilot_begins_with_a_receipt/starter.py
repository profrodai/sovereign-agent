"""Starter for Chapter 12's pilot and proof-pack lab."""

from pathlib import Path
from typing import Any

STUDENT_TODO = True


class PilotStart:
    """The four fields whose exact equality defines a safe replay."""

    def __init__(
        self,
        pilot_id: str,
        store_org_id: str,
        pilot_profile_id: str,
        evidence_namespace: str,
    ) -> None:
        self.pilot_id = pilot_id
        self.store_org_id = store_org_id
        self.pilot_profile_id = pilot_profile_id
        self.evidence_namespace = evidence_namespace


def start_pilot(db_path: Path, request: PilotStart, *, fault: str | None = None) -> str:
    """Start, replay, or refuse while preserving one atomic pilot state."""
    # TODO(1): Compare full identity and transact row, singleton slot, and event together.
    raise NotImplementedError


def verify_manifest(manifest: dict[str, Any], evidence_root: Path) -> list[str]:
    """Return deterministic path, digest, status, and honesty failures."""
    # TODO(2): Resolve evidence paths, recompute hashes, and reject NOT_RUN success prose.
    raise NotImplementedError


def exercise(root: Path) -> dict[str, object]:
    """Start exactly one pilot and verify honest, confined evidence."""
    # TODO(3): Prove replay/no-orphan behavior and run all proof-pack mutations.
    raise NotImplementedError(
        "Make replay exact, pilot start atomic, and proof-pack validation fail closed."
    )
