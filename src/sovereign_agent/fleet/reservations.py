"""Atomic reservations and quota accounting."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent._internal.file_lock import exclusive_file_lock


class QuotaExceeded(ValueError):
    pass


@dataclass(frozen=True)
class ResourceVector:
    cpu: float = 0.0
    memory_bytes: int = 0
    disk_bytes: int = 0
    pids: int = 0
    wall_time_s: float = 0.0
    concurrency: int = 1
    tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu": self.cpu,
            "memory_bytes": self.memory_bytes,
            "disk_bytes": self.disk_bytes,
            "pids": self.pids,
            "wall_time_s": self.wall_time_s,
            "concurrency": self.concurrency,
            "tokens": self.tokens,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any] | None) -> ResourceVector:
        value = value or {}
        return cls(
            cpu=float(value.get("cpu") or 0),
            memory_bytes=int(value.get("memory_bytes") or 0),
            disk_bytes=int(value.get("disk_bytes") or 0),
            pids=int(value.get("pids") or 0),
            wall_time_s=float(value.get("wall_time_s") or 0),
            concurrency=int(value.get("concurrency") or 0),
            tokens=int(value.get("tokens") or 0),
        )

    def plus(self, other: ResourceVector) -> ResourceVector:
        return ResourceVector(
            cpu=self.cpu + other.cpu,
            memory_bytes=self.memory_bytes + other.memory_bytes,
            disk_bytes=self.disk_bytes + other.disk_bytes,
            pids=self.pids + other.pids,
            wall_time_s=self.wall_time_s + other.wall_time_s,
            concurrency=self.concurrency + other.concurrency,
            tokens=self.tokens + other.tokens,
        )

    def exceeds(self, limit: ResourceVector) -> str | None:
        for name in (
            "cpu",
            "memory_bytes",
            "disk_bytes",
            "pids",
            "wall_time_s",
            "concurrency",
            "tokens",
        ):
            if getattr(self, name) > getattr(limit, name) > 0:
                return name
        return None


@dataclass
class Reservation:
    reservation_id: str
    execution_id: str
    requested: ResourceVector
    reserved: ResourceVector
    peak: ResourceVector
    consumed: ResourceVector
    released: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "execution_id": self.execution_id,
            "requested": self.requested.to_dict(),
            "reserved": self.reserved.to_dict(),
            "peak": self.peak.to_dict(),
            "consumed": self.consumed.to_dict(),
            "released": self.released,
        }


class ReservationLedger:
    def __init__(self, root: Path, *, limit: ResourceVector | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._path = self.root / "reservations.json"
        self._lock = self.root / "reservations.lock"
        self.limit = limit or ResourceVector(
            cpu=32,
            memory_bytes=32 * 1024**3,
            disk_bytes=100 * 1024**3,
            pids=4096,
            wall_time_s=24 * 3600,
            concurrency=32,
            tokens=1_000_000,
        )
        self._items: dict[str, Reservation] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        for item in payload.get("reservations", []):
            reservation = Reservation(
                reservation_id=item["reservation_id"],
                execution_id=item["execution_id"],
                requested=ResourceVector.from_dict(item["requested"]),
                reserved=ResourceVector.from_dict(item["reserved"]),
                peak=ResourceVector.from_dict(item["peak"]),
                consumed=ResourceVector.from_dict(item["consumed"]),
                released=bool(item.get("released")),
            )
            self._items[reservation.reservation_id] = reservation

    def _persist(self) -> None:
        atomic_write_json(
            self._path, {"reservations": [item.to_dict() for item in self._items.values()]}
        )

    def _held(self) -> ResourceVector:
        held = ResourceVector()
        for item in self._items.values():
            if not item.released:
                held = held.plus(item.reserved)
        return held

    def reserve(
        self, reservation_id: str, execution_id: str, requested: ResourceVector
    ) -> Reservation:
        with exclusive_file_lock(self._lock):
            existing = self._items.get(reservation_id)
            if existing is not None:
                return existing
            projected = self._held().plus(requested)
            exceeded = projected.exceeds(self.limit)
            if exceeded:
                raise QuotaExceeded(f"quota exceeded for {exceeded}")
            reservation = Reservation(
                reservation_id=reservation_id,
                execution_id=execution_id,
                requested=requested,
                reserved=requested,
                peak=requested,
                consumed=ResourceVector(),
            )
            self._items[reservation_id] = reservation
            self._persist()
            return reservation

    def record_usage(self, reservation_id: str, consumed: ResourceVector) -> Reservation:
        with exclusive_file_lock(self._lock):
            item = self._items[reservation_id]
            peak = ResourceVector(
                cpu=max(item.peak.cpu, consumed.cpu),
                memory_bytes=max(item.peak.memory_bytes, consumed.memory_bytes),
                disk_bytes=max(item.peak.disk_bytes, consumed.disk_bytes),
                pids=max(item.peak.pids, consumed.pids),
                wall_time_s=max(item.peak.wall_time_s, consumed.wall_time_s),
                concurrency=max(item.peak.concurrency, consumed.concurrency),
                tokens=max(item.peak.tokens, consumed.tokens),
            )
            updated = replace(item, consumed=consumed, peak=peak)
            self._items[reservation_id] = updated
            self._persist()
            return updated

    def release(self, reservation_id: str) -> Reservation | None:
        with exclusive_file_lock(self._lock):
            item = self._items.get(reservation_id)
            if item is None:
                return None
            if item.released:
                return item
            updated = replace(item, released=True)
            self._items[reservation_id] = updated
            self._persist()
            return updated


ReservationLedger = ReservationLedger
QuotaExceeded = QuotaExceeded
Reservation = Reservation
