"""Admission after structural authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sovereign_agent.api.envelope import ProtocolEnvelope, ProtocolError

from .auth import Authenticator, ReplayDetected

__all__ = ["AdmissionDecision", "AdmissionService", "Authenticator", "ReplayDetected"]


@dataclass(frozen=True)
class AdmissionDecision:
    allowed: bool
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "reason": self.reason, "detail": self.detail}


class AdmissionService:
    """Runtime admission. Never treats HMAC success as ZEO authorization."""

    def __init__(self, authenticator: Authenticator) -> None:
        self.authenticator = authenticator

    def admit(self, envelope: ProtocolEnvelope, *, observer: bool = False) -> AdmissionDecision:
        try:
            self.authenticator.authenticate(envelope)
        except ProtocolError as exc:
            return AdmissionDecision(False, exc.reason, exc.detail)
        if observer and not envelope.kind.startswith("observe-"):
            return AdmissionDecision(False, "observer-forbidden", "read-only callers cannot mutate")
        return AdmissionDecision(True, "authenticated")
