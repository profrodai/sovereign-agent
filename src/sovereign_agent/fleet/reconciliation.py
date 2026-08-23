"""Reconcile desired vs observed worker state. No last-write-wins finalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class Observation(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    LOST = "lost"


class RetrySafety(StrEnum):
    SAFE = "safe"
    UNSAFE = "unsafe"
    DECLARED_UNKNOWN = "unknown"


class UnknownState(ValueError):
    """Disconnect or crash left the execution in an explicit unknown state."""


@dataclass
class ExecutionObservation:
    execution_id: str
    desired: str
    observed: Observation
    retry_safety: RetrySafety
    fencing_generation: int
    completion_payload: Mapping[str, Any] | None = None


@dataclass
class ReconciliationResult:
    execution_id: str
    canonical_status: str
    quarantined: bool
    diagnostics: list[str] = field(default_factory=list)
    reassigned: bool = False


class ReconciliationEngine:
    def __init__(self) -> None:
        self._canonical: dict[str, dict[str, Any]] = {}
        self._quarantine: dict[str, list[dict[str, Any]]] = {}

    def observe(self, observation: ExecutionObservation) -> ReconciliationResult:
        current = self._canonical.get(observation.execution_id)
        if observation.observed is Observation.UNKNOWN:
            return ReconciliationResult(
                execution_id=observation.execution_id,
                canonical_status="unknown",
                quarantined=False,
                diagnostics=["disconnect observed as unknown; reconcile before retry"],
            )
        if current is None:
            if observation.observed in {Observation.COMPLETED, Observation.FAILED}:
                self._canonical[observation.execution_id] = {
                    "status": observation.observed.value,
                    "fencing_generation": observation.fencing_generation,
                    "payload": dict(observation.completion_payload or {}),
                }
                return ReconciliationResult(
                    execution_id=observation.execution_id,
                    canonical_status=observation.observed.value,
                    quarantined=False,
                )
            return ReconciliationResult(
                execution_id=observation.execution_id,
                canonical_status=observation.observed.value,
                quarantined=False,
            )
        if observation.observed in {Observation.COMPLETED, Observation.FAILED}:
            if current["status"] in {"completed", "failed"}:
                self._quarantine.setdefault(observation.execution_id, []).append(
                    dict(observation.completion_payload or {})
                )
                return ReconciliationResult(
                    execution_id=observation.execution_id,
                    canonical_status=current["status"],
                    quarantined=True,
                    diagnostics=["late or duplicate completion quarantined; canonical receipt unchanged"],
                )
            if observation.fencing_generation < int(current["fencing_generation"]):
                raise PermissionError("stale worker cannot finalize")
            current["status"] = observation.observed.value
            current["payload"] = dict(observation.completion_payload or {})
            return ReconciliationResult(
                execution_id=observation.execution_id,
                canonical_status=current["status"],
                quarantined=False,
            )
        return ReconciliationResult(
            execution_id=observation.execution_id,
            canonical_status=current["status"],
            quarantined=False,
        )

    def reassign(
        self,
        observation: ExecutionObservation,
        *,
        fenced: bool,
        side_effects_proven_safe: bool,
    ) -> ReconciliationResult:
        if observation.retry_safety is not RetrySafety.SAFE:
            raise UnknownState("retry safety must be declared; it is never inferred")
        if observation.retry_safety is RetrySafety.DECLARED_UNKNOWN:
            raise UnknownState("retry safety unknown")
        if not fenced:
            raise PermissionError("reassign requires fencing")
        if not side_effects_proven_safe:
            raise PermissionError("reassign requires side-effect safety proof")
        if observation.observed is Observation.UNKNOWN:
            raise UnknownState("cannot reassign while observation is unknown")
        self._canonical[observation.execution_id] = {
            "status": "reassigned",
            "fencing_generation": observation.fencing_generation,
            "payload": {},
        }
        return ReconciliationResult(
            execution_id=observation.execution_id,
            canonical_status="reassigned",
            quarantined=False,
            reassigned=True,
        )

    def canonical(self, execution_id: str) -> dict[str, Any] | None:
        return self._canonical.get(execution_id)

    def diagnostics(self, execution_id: str) -> list[dict[str, Any]]:
        return list(self._quarantine.get(execution_id, []))


ReconciliationEngine = ReconciliationEngine
UnknownState = UnknownState
