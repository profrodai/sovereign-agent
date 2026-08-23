"""Durable worker registry with verified manifests and fencing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent.contracts.capabilities import EvidenceLevel, RuntimeCapabilityManifest
from sovereign_agent.fleet.protocol import FencingToken, ProtocolError, WorkerIdentity


@dataclass
class WorkerRecord:
    identity: WorkerIdentity
    manifest: dict[str, Any]
    last_ok_seq: int = -1
    admitted: bool = False
    draining: bool = False
    expired: bool = False
    last_heartbeat_s: float = 0.0
    rejection_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "manifest": self.manifest,
            "last_ok_seq": self.last_ok_seq,
            "admitted": self.admitted,
            "draining": self.draining,
            "expired": self.expired,
            "last_heartbeat_s": self.last_heartbeat_s,
            "rejection_reasons": list(self.rejection_reasons),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> WorkerRecord:
        return cls(
            identity=WorkerIdentity.from_dict(value["identity"]),
            manifest=dict(value.get("manifest") or {}),
            last_ok_seq=int(value.get("last_ok_seq", -1)),
            admitted=bool(value.get("admitted", False)),
            draining=bool(value.get("draining", False)),
            expired=bool(value.get("expired", False)),
            last_heartbeat_s=float(value.get("last_heartbeat_s", 0.0)),
            rejection_reasons=list(value.get("rejection_reasons") or []),
        )


class WorkerRegistry:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._path = self.root / "workers.json"
        self._lock = self.root / "workers.lock"
        self._records: dict[str, WorkerRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        import json

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        for item in payload.get("workers", []):
            record = WorkerRecord.from_dict(item)
            self._records[record.identity.worker_id] = record

    def _persist(self) -> None:
        atomic_write_json(
            self._path,
            {"workers": [record.to_dict() for record in self._records.values()]},
        )

    def register(self, identity: WorkerIdentity, manifest: Mapping[str, Any]) -> WorkerRecord:
        with exclusive_file_lock(self._lock):
            existing = self._records.get(identity.worker_id)
            if existing is not None and existing.identity.fencing.dominates(identity.fencing):
                raise ProtocolError("registration rejected: stale fencing token")
            if existing is not None and existing.identity.process_instance != identity.process_instance:
                identity = WorkerIdentity(
                    worker_id=identity.worker_id,
                    process_instance=identity.process_instance,
                    host=identity.host,
                    backend=identity.backend,
                    package_version=identity.package_version,
                    protocol_version=identity.protocol_version,
                    fencing=existing.identity.fencing.next_token(),
                )
            record = WorkerRecord(
                identity=identity,
                manifest=dict(manifest),
                last_heartbeat_s=time.time(),
            )
            self._records[identity.worker_id] = record
            self._persist()
            return record

    def admit(self, worker_id: str) -> WorkerRecord:
        with exclusive_file_lock(self._lock):
            record = self.require(worker_id)
            record.admitted = True
            record.expired = False
            self._persist()
            return record

    def expire(self, worker_id: str) -> WorkerRecord:
        with exclusive_file_lock(self._lock):
            record = self.require(worker_id)
            record.expired = True
            record.admitted = False
            self._persist()
            return record

    def drain(self, worker_id: str) -> WorkerRecord:
        with exclusive_file_lock(self._lock):
            record = self.require(worker_id)
            record.draining = True
            self._persist()
            return record

    def heartbeat(self, worker_id: str, fencing: FencingToken, seq: int) -> WorkerRecord:
        with exclusive_file_lock(self._lock):
            record = self.require(worker_id)
            if record.identity.fencing.generation != fencing.generation:
                raise ProtocolError("heartbeat rejected: fencing mismatch")
            record.last_heartbeat_s = time.time()
            record.last_ok_seq = seq
            self._persist()
            return record

    def require(self, worker_id: str) -> WorkerRecord:
        try:
            return self._records[worker_id]
        except KeyError as exc:
            raise ProtocolError(f"unknown worker {worker_id}") from exc

    def list(self) -> list[WorkerRecord]:
        return list(self._records.values())

    def capability_manifest(self, worker_id: str) -> RuntimeCapabilityManifest:
        record = self.require(worker_id)
        raw = record.manifest.get("capabilities") or record.manifest
        if isinstance(raw, RuntimeCapabilityManifest):
            return raw
        return RuntimeCapabilityManifest.from_dict({"capabilities": raw} if "capabilities" not in raw else raw)


def enforced(manifest: RuntimeCapabilityManifest, name: str) -> bool:
    assertion = manifest.get(name)
    if assertion is None:
        return False
    return bool(assertion.is_available()) and assertion.has_evidence(EvidenceLevel.ENFORCED)


WorkerRegistry = WorkerRegistry
WorkerRecord = WorkerRecord
