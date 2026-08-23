"""Approval disposition evaluated before a mutating capability runs.

Durable pending records live in the session directory so a kill during
the wait, process restart, and a single later approve produce one invoke.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

from zeo_core.contracts import EffectKind, generate_invocation_id
from zeo_core.tools import BoundCapability

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent._internal.hashed import bind_hashed
from sovereign_agent.capabilities.catalog import FrozenExecutionCatalog, redacted_request_digest
from sovereign_agent.capabilities.context import ExecutionScope

_MUTATING = frozenset(
    {
        EffectKind.WRITE,
        EffectKind.DELETE,
        EffectKind.EXTERNAL_COMMUNICATION,
        EffectKind.FINANCIAL,
        EffectKind.SECURITY_SENSITIVE,
    }
)

PENDING_DIR = Path("capabilities") / "approvals" / "pending"
DECISIONS_DIR = Path("capabilities") / "approvals" / "decisions"


class ApprovalDisposition(StrEnum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    PREAPPROVED = "preapproved"
    DENIED = "denied"


class ApprovalConflict(RuntimeError):
    pass


class ApprovalPolicy:
    """Sovereign-owned policy. Never encoded in CapabilityResult."""

    def evaluate(
        self,
        capability: BoundCapability,
        scope: ExecutionScope,
        request: object | None = None,
    ) -> ApprovalDisposition:
        del request
        canonical = capability.definition.id.canonical()
        if canonical in scope.denied_capabilities:
            return ApprovalDisposition.DENIED
        kinds = capability.definition.effects.kinds
        if not (kinds & _MUTATING):
            return ApprovalDisposition.NOT_REQUIRED
        if canonical in scope.preapproved_capabilities:
            return ApprovalDisposition.PREAPPROVED
        if scope.require_approval_for_mutations:
            return ApprovalDisposition.REQUIRED
        return ApprovalDisposition.NOT_REQUIRED


def _pending_dir(session_dir: Path) -> Path:
    path = Path(session_dir) / PENDING_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _decisions_dir(session_dir: Path) -> Path:
    path = Path(session_dir) / DECISIONS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def persist_capability_approval(
    session_dir: Path,
    *,
    catalog: FrozenExecutionCatalog,
    canonical_id: str,
    definition_digest: str,
    arguments: dict[str, Any],
    reason: str,
    execution_id: str,
    ttl: timedelta = timedelta(hours=24),
    invocation_id: str | None = None,
) -> dict[str, Any]:
    """Persist a pending approval. Never stores raw secret values."""
    approval_id = invocation_id or generate_invocation_id()
    record = {
        "approval_id": approval_id,
        "invocation_id": approval_id,
        "canonical_id": canonical_id,
        "catalog_digest": catalog.digest,
        "definition_digest": definition_digest,
        "redacted_request_digest": redacted_request_digest(arguments),
        "reason": reason,
        "execution_id": execution_id,
        "expires_at": (datetime.now(UTC) + ttl).isoformat(),
        "created_at": datetime.now(UTC).isoformat(),
    }
    path = bind_hashed(_pending_dir(session_dir), approval_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    decision = bind_hashed(_decisions_dir(session_dir), approval_id)
    if decision.exists():
        return json.loads(decision.read_text(encoding="utf-8"))["request"]
    atomic_write_json(path, record)
    return record


def decide_capability_approval(
    session_dir: Path,
    approval_id: str,
    *,
    decision: str,
    actor: str,
    reason: str,
) -> dict[str, Any]:
    pending = bind_hashed(_pending_dir(session_dir), approval_id)
    decided = bind_hashed(_decisions_dir(session_dir), approval_id)
    if decided.exists():
        existing = json.loads(decided.read_text(encoding="utf-8"))
        if existing.get("decision") == decision:
            return existing
        raise ApprovalConflict("approval already decided differently")
    if not pending.exists():
        raise ApprovalConflict("unknown approval")
    request = json.loads(pending.read_text(encoding="utf-8"))
    expires = datetime.fromisoformat(request["expires_at"])
    kind = decision
    if expires <= datetime.now(UTC) and decision == "approved":
        kind = "expired"
    payload = {
        "approval_id": approval_id,
        "decision": kind,
        "actor": actor,
        "reason": reason,
        "decided_at": datetime.now(UTC).isoformat(),
        "request": request,
        "resumed": False,
    }
    atomic_write_json(decided, payload)
    if pending.exists():
        pending.unlink()
    return payload


def expire_due_approvals(session_dir: Path) -> list[dict[str, Any]]:
    expired: list[dict[str, Any]] = []
    now = datetime.now(UTC)
    for path in _pending_dir(session_dir).glob("*.json"):
        request = json.loads(path.read_text(encoding="utf-8"))
        if datetime.fromisoformat(request["expires_at"]) <= now:
            expired.append(
                decide_capability_approval(
                    session_dir,
                    request["approval_id"],
                    decision="expired",
                    actor="clock",
                    reason="approval expired",
                )
            )
    return expired


def load_approval_decision(session_dir: Path, approval_id: str) -> dict[str, Any] | None:
    path = bind_hashed(_decisions_dir(session_dir), approval_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def mark_approval_resumed(session_dir: Path, approval_id: str) -> dict[str, Any]:
    path = bind_hashed(_decisions_dir(session_dir), approval_id)
    if not path.exists():
        raise ApprovalConflict("no decision to resume")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("resumed"):
        return payload
    if payload.get("decision") != "approved":
        raise ApprovalConflict("only approved decisions resume execution")
    payload["resumed"] = True
    atomic_write_json(path, payload)
    return payload
