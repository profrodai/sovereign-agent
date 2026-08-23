"""Seat-instance supervision: presence, leases, drain, restart recovery."""

from __future__ import annotations

import os
import socket
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_bytes
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent._internal.hashed import bind_hashed, digest
from sovereign_agent.contracts._core import canonical_json_bytes, format_datetime
from sovereign_agent.contracts.ids import ProviderSessionId, SeatInstanceId
from sovereign_agent.registry import SeatInstance, SeatLifecycle, SeatRegistry
from sovereign_agent.runtime import RuntimeRoot


class PresenceState(StrEnum):
    STARTING = "starting"
    ONLINE = "online"
    BUSY = "busy"
    AWAITING_APPROVAL = "awaiting-approval"
    DRAINING = "draining"
    OFFLINE = "offline"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SupervisorConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class ContinuityBreak:
    instance_id: str
    previous_provider_session: str | None
    new_provider_session: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "provider-session-continuity-break",
            "instance_id": self.instance_id,
            "previous_provider_session": self.previous_provider_session,
            "new_provider_session": self.new_provider_session,
            "reason": self.reason,
        }


class SeatSupervisor:
    def __init__(
        self,
        runtime_root: RuntimeRoot,
        registry: SeatRegistry,
        *,
        heartbeat_timeout: timedelta = timedelta(seconds=30),
        unknown_grace: timedelta = timedelta(seconds=15),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.runtime_root = runtime_root
        self.registry = registry
        self.heartbeat_timeout = heartbeat_timeout
        self.unknown_grace = unknown_grace
        self._clock = clock or (lambda: datetime.now(UTC))
        self._leases = runtime_root.ensure_directory("service") / "instance-leases"
        self._leases.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._events = runtime_root.ensure_directory("service") / "continuity.jsonl"
        self._lock = runtime_root.locks_dir / "supervisor.lock"

    def observe(self, instance: SeatInstance) -> PresenceState:
        now = self._clock()
        age = now - instance.heartbeat_at
        recorded = str(instance.status.get("presence", PresenceState.ONLINE.value))
        try:
            presence = PresenceState(recorded)
        except ValueError:
            presence = PresenceState.UNKNOWN
        if presence in {PresenceState.DRAINING, PresenceState.OFFLINE, PresenceState.FAILED}:
            return presence
        if age > self.heartbeat_timeout + self.unknown_grace:
            return PresenceState.OFFLINE
        if age > self.heartbeat_timeout:
            return PresenceState.UNKNOWN
        return presence

    def acquire_instance(self, instance_id: SeatInstanceId | str, *, owner: str) -> dict[str, Any]:
        iid = (
            instance_id if isinstance(instance_id, SeatInstanceId) else SeatInstanceId(instance_id)
        )
        path = bind_hashed(self._leases, iid.value)
        token = digest(f"{owner}:{os.getpid()}:{socket.gethostname()}")
        with exclusive_file_lock(self._lock):
            if path.exists():
                current = _read_json(path)
                if not _stale(current, self._clock()) and current.get("owner") != owner:
                    raise SupervisorConflict(f"instance {iid.value} is already leased")
            payload = {
                "instance_id": iid.value,
                "owner": owner,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "token": token,
                "heartbeat_at": format_datetime(self._clock(), "heartbeat_at"),
                "lease_seconds": 60,
            }
            atomic_write_bytes(path, canonical_json_bytes(payload))
        return payload

    def heartbeat_instance(
        self,
        instance_id: SeatInstanceId | str,
        *,
        presence: PresenceState,
        active_execution: str | None = None,
    ) -> SeatInstance:
        iid = (
            instance_id if isinstance(instance_id, SeatInstanceId) else SeatInstanceId(instance_id)
        )
        current = self.registry.get(iid)
        status = dict(current.status)
        if presence is PresenceState.BUSY and status.get("active_execution") and active_execution:
            if status["active_execution"] != active_execution:
                raise SupervisorConflict("instance already has an active execution")
        status["presence"] = presence.value
        status["active_execution"] = active_execution
        lifecycle = {
            PresenceState.STARTING: SeatLifecycle.STARTING,
            PresenceState.ONLINE: SeatLifecycle.RUNNING,
            PresenceState.BUSY: SeatLifecycle.RUNNING,
            PresenceState.AWAITING_APPROVAL: SeatLifecycle.RUNNING,
            PresenceState.DRAINING: SeatLifecycle.STOPPING,
            PresenceState.OFFLINE: SeatLifecycle.STOPPED,
            PresenceState.FAILED: SeatLifecycle.FAILED,
            PresenceState.UNKNOWN: current.lifecycle,
        }[presence]
        return self.registry.heartbeat(iid, lifecycle=lifecycle, status=status)

    def drain(self, instance_id: SeatInstanceId | str) -> SeatInstance:
        return self.heartbeat_instance(instance_id, presence=PresenceState.DRAINING)

    def recover(
        self,
        instance_id: SeatInstanceId | str,
        *,
        provider_session: ProviderSessionId | str | None,
    ) -> ContinuityBreak | None:
        current = self.registry.get(instance_id)
        previous = (
            None if current.provider_session_id is None else current.provider_session_id.value
        )
        incoming = None if provider_session is None else str(provider_session)
        if previous and incoming and previous != incoming:
            event = ContinuityBreak(
                str(current.instance_id),
                previous,
                incoming,
                "provider session could not be restored",
            )
            from sovereign_agent._internal.atomic import atomic_append_jsonl

            atomic_append_jsonl(self._events, event.to_dict())
            self.heartbeat_instance(instance_id, presence=PresenceState.ONLINE)
            return event
        self.heartbeat_instance(instance_id, presence=PresenceState.ONLINE)
        return None

    def recover_nonterminal(self) -> list[SeatInstance]:
        recovered = []
        for instance in self.registry.list():
            presence = self.observe(instance)
            if presence not in {PresenceState.OFFLINE, PresenceState.FAILED}:
                recovered.append(self.heartbeat_instance(instance.instance_id, presence=presence))
        return recovered


def _read_json(path: Any) -> dict[str, Any]:
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SupervisorConflict("corrupt instance lease")
    return data


def _stale(payload: dict[str, Any], now: datetime) -> bool:
    from datetime import datetime as dt

    raw = payload.get("heartbeat_at")
    if not isinstance(raw, str):
        return True
    heartbeat = dt.fromisoformat(raw.replace("Z", "+00:00"))
    lease = float(payload.get("lease_seconds", 60))
    return (now - heartbeat).total_seconds() > lease
