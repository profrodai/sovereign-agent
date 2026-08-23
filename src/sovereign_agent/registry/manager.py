"""Process-safe persistent seat-instance registry."""

from __future__ import annotations

import builtins
import hashlib
import json
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_bytes, fsync_directory
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent.contracts._core import canonical_json_bytes
from sovereign_agent.contracts.ids import (
    ProviderSessionId,
    SeatId,
    SeatInstanceId,
    SovereignSessionId,
)
from sovereign_agent.runtime import RuntimeRoot

from .errors import (
    RegistrationConflict,
    RegistryCorruptionError,
    RegistryValidationError,
    SeatInstanceNotFound,
)
from .models import RuntimeAddress, SeatInstance, SeatLifecycle

Clock = Callable[[], datetime]


class SeatRegistry:
    """Durable registry rooted in ``RuntimeRoot.seats_dir``."""

    def __init__(self, runtime_root: RuntimeRoot, *, clock: Clock | None = None) -> None:
        self.runtime_root = runtime_root.initialize()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._records = self.runtime_root.seats_dir / "instances"
        self._locks = self.runtime_root.locks_dir / "registry"
        self._safe_directory(self._records)
        self._safe_directory(self._locks)

    def register(
        self,
        *,
        instance_id: SeatInstanceId | str,
        seat_id: SeatId | str,
        provider: str,
        backend: str,
        capabilities: tuple[str, ...] | list[str] = (),
        address: RuntimeAddress | str | None = None,
        lifecycle: SeatLifecycle = SeatLifecycle.REGISTERED,
        status: Mapping[str, Any] | None = None,
        sovereign_session_id: SovereignSessionId | str | None = None,
        provider_session_id: ProviderSessionId | str | None = None,
        capability_manifest_ref: str | None = None,
    ) -> SeatInstance:
        iid = (
            instance_id if isinstance(instance_id, SeatInstanceId) else SeatInstanceId(instance_id)
        )
        sid = seat_id if isinstance(seat_id, SeatId) else SeatId(seat_id)
        runtime_address = (
            RuntimeAddress.for_instance(iid)
            if address is None
            else address
            if isinstance(address, RuntimeAddress)
            else RuntimeAddress(address)
        )
        now = self._now()
        candidate = SeatInstance(
            instance_id=iid,
            seat_id=sid,
            provider=provider,
            backend=backend,
            capabilities=tuple(capabilities),
            address=runtime_address,
            registered_at=now,
            updated_at=now,
            heartbeat_at=now,
            lifecycle=lifecycle,
            status=status or {},  # type: ignore[arg-type]
            sovereign_session_id=sovereign_session_id,  # type: ignore[arg-type]
            provider_session_id=provider_session_id,  # type: ignore[arg-type]
            capability_manifest_ref=capability_manifest_ref,
        )
        with self._guard(iid):
            path = self._record_path(iid)
            if path.exists():
                current = self._read(path)
                if self._identity(current) != self._identity(candidate):
                    raise RegistrationConflict(
                        f"instance {iid.value!r} is registered with different identity"
                    )
                return current
            self._ensure_regular_or_missing(path)
            atomic_write_bytes(path, canonical_json_bytes(candidate.to_dict()))
            fsync_directory(path.parent)
        return candidate

    def get(self, instance_id: SeatInstanceId | str) -> SeatInstance:
        iid = (
            instance_id if isinstance(instance_id, SeatInstanceId) else SeatInstanceId(instance_id)
        )
        path = self._record_path(iid)
        if not path.exists():
            raise SeatInstanceNotFound(iid.value)
        record = self._read(path)
        if record.instance_id != iid:
            raise RegistryCorruptionError("registry filename and instance identity disagree")
        return record

    def resolve(self, address: RuntimeAddress | str) -> SeatInstance:
        parsed = address if isinstance(address, RuntimeAddress) else RuntimeAddress(address)
        record = self.get(parsed.instance_id)
        if record.address != parsed:
            raise SeatInstanceNotFound(parsed.value)
        return record

    def heartbeat(
        self,
        instance_id: SeatInstanceId | str,
        *,
        lifecycle: SeatLifecycle | None = None,
        status: Mapping[str, Any] | None = None,
    ) -> SeatInstance:
        iid = (
            instance_id if isinstance(instance_id, SeatInstanceId) else SeatInstanceId(instance_id)
        )
        with self._guard(iid):
            current = self.get(iid)
            now = self._now()
            updated = SeatInstance(
                instance_id=current.instance_id,
                seat_id=current.seat_id,
                provider=current.provider,
                backend=current.backend,
                capabilities=current.capabilities,
                address=current.address,
                registered_at=current.registered_at,
                updated_at=now,
                heartbeat_at=now,
                lifecycle=lifecycle or current.lifecycle,
                status=current.status if status is None else status,  # type: ignore[arg-type]
                sovereign_session_id=current.sovereign_session_id,
                provider_session_id=current.provider_session_id,
                capability_manifest_ref=current.capability_manifest_ref,
            )
            atomic_write_bytes(self._record_path(iid), canonical_json_bytes(updated.to_dict()))
            fsync_directory(self._records)
            return updated

    def list(self) -> builtins.list[SeatInstance]:
        records: builtins.list[SeatInstance] = []
        for path in sorted(self._records.glob("*.json")):
            self._ensure_regular_or_missing(path)
            records.append(self._read(path))
        return sorted(records, key=lambda item: item.registered_at)

    def stale(
        self,
        threshold: timedelta | float,
        *,
        now: datetime | None = None,
    ) -> builtins.list[SeatInstance]:
        observed = self._now() if now is None else now
        return [item for item in self.list() if item.is_stale(observed, threshold)]

    def is_live(
        self,
        instance_id: SeatInstanceId | str,
        threshold: timedelta | float,
        *,
        now: datetime | None = None,
    ) -> bool:
        observed = self._now() if now is None else now
        return not self.get(instance_id).is_stale(observed, threshold)

    @staticmethod
    def _identity(item: SeatInstance) -> tuple[object, ...]:
        return (
            item.instance_id,
            item.seat_id,
            item.provider,
            item.backend,
            item.capabilities,
            item.address,
            item.sovereign_session_id,
            item.provider_session_id,
            item.capability_manifest_ref,
        )

    def _record_path(self, instance_id: SeatInstanceId) -> Path:
        digest = hashlib.sha256(instance_id.value.encode()).hexdigest()
        path = self.runtime_root.path(Path("seats") / "instances" / f"{digest}.json")
        if path.parent != self._records.resolve():
            raise RegistryValidationError("registry record escaped records directory")
        return path

    def _read(self, path: Path) -> SeatInstance:
        self._ensure_regular_or_missing(path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise TypeError("record is not an object")
            return SeatInstance.from_dict(raw)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise RegistryCorruptionError(f"invalid registry record: {path}") from exc

    def _safe_directory(self, path: Path) -> None:
        if path.is_symlink():
            raise RegistryValidationError(f"registry directory must not be a symlink: {path}")
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not path.is_dir():
            raise RegistryValidationError(f"registry path is not a directory: {path}")
        path.resolve().relative_to(self.runtime_root.root.resolve())

    @staticmethod
    def _ensure_regular_or_missing(path: Path) -> None:
        if path.is_symlink():
            raise RegistryValidationError(f"registry record must not be a symlink: {path}")
        if path.exists() and not path.is_file():
            raise RegistryValidationError(f"registry record must be a regular file: {path}")

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise RegistryValidationError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)

    def _guard(self, instance_id: SeatInstanceId) -> AbstractContextManager[None]:
        digest = hashlib.sha256(instance_id.value.encode()).hexdigest()
        path = self._locks / f"{digest}.lock"
        self._ensure_regular_or_missing(path)
        return exclusive_file_lock(path)


__all__ = ["SeatRegistry"]
