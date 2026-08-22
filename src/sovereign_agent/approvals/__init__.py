"""Durable approval records, policies, and resumable waits."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_bytes
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent._internal.hashed import bind_hashed
from sovereign_agent.contracts._core import canonical_json_bytes, format_datetime, parse_datetime
from sovereign_agent.runtime import RuntimeRoot


class ApprovalDecisionKind(StrEnum):
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class PolicyEffect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_HUMAN = "require-human"


class ApprovalConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class PolicyRule:
    effect: PolicyEffect
    capabilities: tuple[str, ...] = ()
    risk_classes: tuple[str, ...] = ()
    action_kinds: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    execution_id: str
    seat_instance: str
    action_kind: str
    action_summary: str
    risk_class: str
    requested_at: datetime
    expires_at: datetime
    requested_capabilities: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    destination: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "execution_id": self.execution_id,
            "seat_instance": self.seat_instance,
            "action_kind": self.action_kind,
            "action_summary": self.action_summary,
            "risk_class": self.risk_class,
            "requested_at": format_datetime(self.requested_at, "requested_at"),
            "expires_at": format_datetime(self.expires_at, "expires_at"),
            "requested_capabilities": list(self.requested_capabilities),
            "evidence_refs": list(self.evidence_refs),
            "destination": self.destination,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApprovalRequest:
        return cls(
            approval_id=str(data["approval_id"]),
            execution_id=str(data["execution_id"]),
            seat_instance=str(data["seat_instance"]),
            action_kind=str(data["action_kind"]),
            action_summary=str(data["action_summary"]),
            risk_class=str(data["risk_class"]),
            requested_at=parse_datetime(data["requested_at"], "requested_at"),
            expires_at=parse_datetime(data["expires_at"], "expires_at"),
            requested_capabilities=tuple(data.get("requested_capabilities") or ()),
            evidence_refs=tuple(data.get("evidence_refs") or ()),
            destination=data.get("destination"),
        )


class ApprovalService:
    def __init__(self, runtime_root: RuntimeRoot, *, rules: tuple[PolicyRule, ...] = ()) -> None:
        self.runtime_root = runtime_root
        self.rules = rules
        self._dir = runtime_root.ensure_directory("approvals")
        self._pending = self._dir / "pending"
        self._decisions = self._dir / "decisions"
        self._pending.mkdir(mode=0o700, exist_ok=True)
        self._decisions.mkdir(mode=0o700, exist_ok=True)
        self._lock = runtime_root.locks_dir / "approvals.lock"
        self._resumed: set[str] = set()

    def evaluate(
        self, request: ApprovalRequest, *, engage_mode: str = "interactive"
    ) -> PolicyEffect:
        del engage_mode  # autonomous does not imply external send
        for rule in self.rules:
            if self._matches(rule, request):
                return rule.effect
        if request.risk_class in {"external-write", "destructive"} or request.action_kind in {
            "email.send",
            "channel.send",
            "tool-call",
        }:
            if (
                "email.send" in request.requested_capabilities
                or request.risk_class == "external-write"
            ):
                return PolicyEffect.REQUIRE_HUMAN
            if request.risk_class == "destructive":
                return PolicyEffect.REQUIRE_HUMAN
        return PolicyEffect.REQUIRE_HUMAN

    def submit(
        self, request: ApprovalRequest, *, engage_mode: str = "interactive"
    ) -> dict[str, Any]:
        effect = self.evaluate(request, engage_mode=engage_mode)
        if effect is PolicyEffect.ALLOW:
            return self.decide(
                request.approval_id,
                ApprovalDecisionKind.APPROVED,
                actor="policy",
                reason="policy-allow",
                request=request,
            )
        if effect is PolicyEffect.DENY:
            return self.decide(
                request.approval_id,
                ApprovalDecisionKind.DENIED,
                actor="policy",
                reason="policy-deny",
                request=request,
            )
        path = bind_hashed(self._pending, request.approval_id)
        with exclusive_file_lock(self._lock):
            atomic_write_bytes(path, canonical_json_bytes(request.to_dict()))
        return {"status": PolicyEffect.REQUIRE_HUMAN.value, "approval_id": request.approval_id}

    def decide(
        self,
        approval_id: str,
        kind: ApprovalDecisionKind,
        *,
        actor: str,
        reason: str,
        scope: str = "once",
        request: ApprovalRequest | None = None,
    ) -> dict[str, Any]:
        with exclusive_file_lock(self._lock):
            pending_path = bind_hashed(self._pending, approval_id)
            decision_path = bind_hashed(self._decisions, approval_id)
            if decision_path.exists():
                raise ApprovalConflict("approval already decided")
            if request is None and pending_path.exists():
                request = ApprovalRequest.from_dict(
                    json.loads(pending_path.read_text(encoding="utf-8"))
                )
            if request is None:
                raise ApprovalConflict("unknown approval")
            payload = {
                "approval_id": approval_id,
                "execution_id": request.execution_id,
                "decision": kind.value,
                "actor": actor,
                "reason": reason,
                "scope": scope,
                "decided_at": format_datetime(datetime.now(UTC), "decided_at"),
                "request": request.to_dict(),
                "resumed": False,
            }
            atomic_write_bytes(decision_path, canonical_json_bytes(payload))
            if pending_path.exists():
                pending_path.unlink()
            return payload

    def expire_due(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        observed = now or datetime.now(UTC)
        expired = []
        for path in self._pending.glob("*.json"):
            request = ApprovalRequest.from_dict(json.loads(path.read_text(encoding="utf-8")))
            if request.expires_at <= observed:
                expired.append(
                    self.decide(
                        request.approval_id,
                        ApprovalDecisionKind.EXPIRED,
                        actor="clock",
                        reason="approval expired",
                        request=request,
                    )
                )
        return expired

    def pending(self) -> list[dict[str, Any]]:
        return [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(self._pending.glob("*.json"))
        ]

    def resume_execution(self, approval_id: str) -> str:
        path = bind_hashed(self._decisions, approval_id)
        if not path.exists():
            raise ApprovalConflict("no decision to resume")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("resumed"):
            raise ApprovalConflict("approval already resumed exactly once")
        if payload.get("decision") != ApprovalDecisionKind.APPROVED.value:
            raise ApprovalConflict("only approved decisions resume execution")
        payload["resumed"] = True
        atomic_write_bytes(path, canonical_json_bytes(payload))
        return str(payload["execution_id"])

    def _matches(self, rule: PolicyRule, request: ApprovalRequest) -> bool:
        if rule.action_kinds and request.action_kind not in rule.action_kinds:
            return False
        if rule.risk_classes and request.risk_class not in rule.risk_classes:
            return False
        if rule.capabilities and not set(rule.capabilities) & set(request.requested_capabilities):
            return False
        return True
