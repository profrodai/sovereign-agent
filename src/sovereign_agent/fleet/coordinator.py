"""Coordinator: admit, place, reserve, fence, dispatch. Workers never finalize."""

from __future__ import annotations

import secrets
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sovereign_agent.fleet.metrics import FleetMetrics
from sovereign_agent.fleet.placement import PlacementDecision, PlacementEngine, PlacementRefusal
from sovereign_agent.fleet.protocol import (
    FencingToken,
    ProtocolError,
    ProtocolSession,
    WorkerIdentity,
    WorkerLease,
)
from sovereign_agent.fleet.reconciliation import (
    ExecutionObservation,
    Observation,
    ReconciliationEngine,
    RetrySafety,
)
from sovereign_agent.fleet.registry import WorkerRecord, WorkerRegistry
from sovereign_agent.fleet.reservations import ReservationLedger, ResourceVector


@dataclass
class Dispatch:
    lease: WorkerLease
    placement: PlacementDecision
    reservation_id: str
    catalog_digest: str


class FleetCoordinator:
    """Single control identity for a runtime. Workers only report evidence."""

    def __init__(self, root: Path, *, lease_ttl_s: float = 60.0) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry = WorkerRegistry(self.root / "workers")
        self.reservations = ReservationLedger(self.root / "reservations")
        self.placement = PlacementEngine()
        self.reconciliation = ReconciliationEngine()
        self.metrics = FleetMetrics()
        self.lease_ttl_s = lease_ttl_s
        self._sessions: dict[str, ProtocolSession] = {}
        self._leases: dict[str, WorkerLease] = {}
        self._finalized: set[str] = set()

    def register_worker(
        self, identity: WorkerIdentity, manifest: Mapping[str, Any]
    ) -> WorkerRecord:
        record = self.registry.register(identity, manifest)
        self._sessions[identity.worker_id] = ProtocolSession(identity, now_s=time.time())
        return record

    def admit_worker(self, worker_id: str) -> WorkerRecord:
        record = self.registry.admit(worker_id)
        self.metrics.workers_admitted = len(
            [item for item in self.registry.list() if item.admitted]
        )
        return record

    def expire_worker(self, worker_id: str) -> WorkerRecord:
        record = self.registry.expire(worker_id)
        session = self._sessions.get(worker_id)
        if session is not None:
            session.mark_expired()
        self.metrics.workers_expired += 1
        return record

    def drain_worker(self, worker_id: str) -> WorkerRecord:
        self.metrics.workers_draining += 1
        return self.registry.drain(worker_id)

    def dispatch(
        self,
        *,
        execution_id: str,
        catalog_digest: str,
        requirements: Mapping[str, Any],
        effects: Mapping[str, Any],
        constraints: Mapping[str, Any],
        resources: ResourceVector,
        invocation: Mapping[str, Any],
    ) -> Dispatch:
        del invocation
        workers = [item for item in self.registry.list() if item.admitted and not item.expired]
        try:
            decision = self.placement.place(
                requirements=requirements,
                effects=effects,
                constraints=constraints,
                workers=workers,
            )
        except PlacementRefusal:
            self.metrics.refusals += 1
            raise
        reservation_id = f"rsv-{execution_id}"
        self.reservations.reserve(reservation_id, execution_id, resources)
        worker = self.registry.require(decision.worker_id)
        lease = WorkerLease(
            lease_id=f"lease-{secrets.token_hex(8)}",
            execution_id=execution_id,
            worker_id=worker.identity.worker_id,
            fencing=worker.identity.fencing,
            expires_at_s=time.time() + self.lease_ttl_s,
        )
        self._leases[execution_id] = lease
        self.metrics.reservations_held += 1
        return Dispatch(
            lease=lease,
            placement=decision,
            reservation_id=reservation_id,
            catalog_digest=catalog_digest,
        )

    def accept_worker_message(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        worker_id = str(payload["worker_id"])
        session = self._sessions.get(worker_id)
        if session is None:
            raise ProtocolError("worker is not registered")
        lease = None
        if "lease" in payload:
            lease = WorkerLease.from_dict(payload["lease"])
            current = self._leases.get(lease.execution_id)
            session.require_canonical(payload, current)
        ack = session.observe(payload)
        kind = payload.get("kind")
        if kind == "completion":
            execution_id = lease.execution_id if lease else ""
            if execution_id in self._finalized:
                self.metrics.duplicate_finalizations_blocked += 1
                self.reconciliation.observe(
                    ExecutionObservation(
                        execution_id=execution_id,
                        desired="completed",
                        observed=Observation.COMPLETED,
                        retry_safety=RetrySafety.UNSAFE,
                        fencing_generation=lease.fencing.generation if lease else 0,
                        completion_payload=payload,
                    )
                )
                return {"ack": ack.to_dict(), "quarantined": True}
            if session.expired:
                raise ProtocolError("expired worker cannot finalize")
            self._finalized.add(execution_id)
            session.note_completion(execution_id)
        fencing_raw = payload.get("fencing")
        if fencing_raw is None and lease is not None:
            fencing_raw = lease.fencing.to_dict()
        if fencing_raw is not None:
            self.registry.heartbeat(
                worker_id, FencingToken.from_dict(fencing_raw), int(payload["seq"])
            )
        return {"ack": ack.to_dict(), "quarantined": False}

    def locate(self, execution_id: str) -> dict[str, Any]:
        lease = self._leases.get(execution_id)
        return {
            "execution_id": execution_id,
            "lease": None if lease is None else lease.to_dict(),
            "finalized": execution_id in self._finalized,
            "canonical": self.reconciliation.canonical(execution_id),
        }

    def status(self) -> dict[str, Any]:
        workers = self.registry.list()
        self.metrics.workers_admitted = len([item for item in workers if item.admitted])
        self.metrics.workers_expired = len([item for item in workers if item.expired])
        self.metrics.workers_draining = len([item for item in workers if item.draining])
        return {
            "workers": [item.to_dict() for item in workers],
            "metrics": self.metrics.snapshot(),
            "finalized": sorted(self._finalized),
        }


FleetCoordinator = FleetCoordinator
Dispatch = Dispatch
