"""Deterministic checks, digests, and evidence records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import Evidence

Check = Callable[[], tuple[int, str]]


def digest_payload(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, default=str, sort_keys=True).encode()).hexdigest()


def record_check(
    assignment_id: str, kind: str, command: list[str], exit_code: int, artifacts: Path | None = None
) -> Evidence:
    refs: list[str] = []
    if artifacts and artifacts.exists():
        refs.append(str(artifacts))
    evidence = Evidence(
        id=new_id("evd"),
        assignment_id=assignment_id,
        kind=kind,
        command=command,
        exit_code=exit_code,
        artifact_refs=refs,
        digest=digest_payload({"kind": kind, "exit_code": exit_code, "command": command}),
        created_at=utc_now(),
    )
    return evidence
