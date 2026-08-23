"""Coordinator lease, readiness/liveness, drain and stop."""

from __future__ import annotations

import os
import secrets
import socket
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent.runtime import RuntimeRoot


class CoordinatorConflict(RuntimeError):
    pass


@dataclass
class CoordinatorLease:
    lease_id: str
    token: str
    pid: int
    host: str
    start_marker: str
    heartbeat_at: float
    path: Path

    def heartbeat(self) -> None:
        with exclusive_file_lock(self.path.with_suffix(".lock")):
            current = _read(self.path)
            if current.get("token") != self.token:
                raise CoordinatorConflict("coordinator fencing token lost")
            current["heartbeat_at"] = time.time()
            atomic_write_json(self.path, current)

    def release(self) -> None:
        with exclusive_file_lock(self.path.with_suffix(".lock")):
            current = _read(self.path)
            if current.get("token") != self.token:
                return
            self.path.unlink(missing_ok=True)


def acquire_coordinator_lease(
    runtime_root: RuntimeRoot, *, lease_seconds: float = 30.0
) -> CoordinatorLease:
    runtime_root.ensure_directory("service")
    path = runtime_root.service_dir / "coordinator.json"
    lock = runtime_root.locks_dir / "coordinator.lock"
    token = secrets.token_hex(16)
    lease_id = str(uuid4())
    start_marker = f"{os.getpid()}:{time.time_ns()}"
    with exclusive_file_lock(lock):
        if path.exists():
            current = _read(path)
            age = time.time() - float(current.get("heartbeat_at", 0))
            if age <= float(current.get("lease_seconds", lease_seconds)):
                raise CoordinatorConflict("another coordinator owns this runtime root")
        payload = {
            "lease_id": lease_id,
            "token": token,
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "start_marker": start_marker,
            "heartbeat_at": time.time(),
            "lease_seconds": lease_seconds,
            "recovered": path.exists(),
        }
        atomic_write_json(path, payload)
    return CoordinatorLease(
        lease_id, token, os.getpid(), socket.gethostname(), start_marker, time.time(), path
    )


def _read(path: Path) -> dict[str, Any]:
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CoordinatorConflict("corrupt coordinator lease")
    return data


@dataclass
class Readiness:
    ready: bool
    live: bool
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "live": self.live,
            "reasons": self.reasons,
            "generated_at": datetime.now(UTC).isoformat(),
        }


class ServiceRuntime:
    def __init__(self, runtime_root: RuntimeRoot) -> None:
        self.runtime_root = runtime_root
        self.lease: CoordinatorLease | None = None
        self._loop_ticks = 0
        self.draining = False

    def start(self) -> CoordinatorLease:
        self.lease = acquire_coordinator_lease(self.runtime_root)
        return self.lease

    def tick(self) -> None:
        if self.lease is None:
            raise CoordinatorConflict("no coordinator lease")
        self.lease.heartbeat()
        self._loop_ticks += 1

    def drain(self) -> None:
        self.draining = True

    def stop(self) -> None:
        if self.lease is not None:
            self.lease.release()
            self.lease = None

    def readiness(
        self, *, secrets_ok: bool = True, providers_ok: bool = True, channels_ok: bool = True
    ) -> Readiness:
        reasons = []
        try:
            probe = self.runtime_root.ensure_directory("service") / ".rename-probe"
            probe.write_text("ok", encoding="utf-8")
            dest = probe.with_suffix(".renamed")
            probe.replace(dest)
            dest.unlink()
        except OSError as exc:
            reasons.append(f"atomic-rename: {exc}")
        if self.lease is None:
            reasons.append("coordinator-lease-missing")
        if not secrets_ok:
            reasons.append("secrets-unresolved")
        if not providers_ok:
            reasons.append("providers-unprobed")
        if not channels_ok:
            reasons.append("channels-incomplete")
        quarantine = self.runtime_root.relay_dir / "quarantine"
        if quarantine.exists() and any(quarantine.iterdir()):
            reasons.append("unresolved-quarantine")
        live = self._loop_ticks > 0 and self.lease is not None
        return Readiness(ready=not reasons, live=live, reasons=reasons)
