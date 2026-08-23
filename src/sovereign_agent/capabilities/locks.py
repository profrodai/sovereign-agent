"""Sovereign-owned lock acquisition for ZeoCore concurrency declarations."""

from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import shutil
import socket
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel
from zeo_core.contracts import ConcurrencyMode
from zeo_core.tools import BoundCapability, resource_coordination_key

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent._internal.file_lock import exclusive_file_lock


class LockContention(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(f"contention acquiring lock {key}")
        self.key = key
        self.evidence = f"contention:{key}"


class LockTimeout(Exception):
    def __init__(self, phase: str, key: str) -> None:
        super().__init__(f"{phase} timed out for lock {key}")
        self.phase = phase
        self.key = key
        self.evidence = f"timeout:{phase}:{key}"


@dataclass(frozen=True)
class LockOwnership:
    seat: str | None = None
    session: str | None = None
    repository: str | None = None
    channel: str | None = None


def coordination_lock_key(
    capability: BoundCapability,
    request: BaseModel,
    ownership: LockOwnership,
) -> str:
    mode = capability.definition.effects.concurrency
    canonical = capability.definition.id.canonical()
    if mode is ConcurrencyMode.SERIAL_PER_RESOURCE:
        zeo_key = resource_coordination_key(capability, request) or canonical
    else:
        zeo_key = canonical
    material = "|".join(
        [
            mode.value,
            zeo_key,
            ownership.seat or "",
            ownership.session or "",
            ownership.repository or "",
            ownership.channel or "",
        ]
    )
    return hashlib.sha256(material.encode()).hexdigest()[:32]


class _DurableLease:
    def __init__(self, path: Path, token: str) -> None:
        self.path = path
        self.token = token
        self._released = False

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        metadata_path = self.path / "owner.json"
        try:
            payload = metadata_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return
        if self.token not in payload:
            return
        tombstone = self.path.with_name(f".released-{self.token}")
        try:
            self.path.rename(tombstone)
        except FileNotFoundError:
            return
        shutil.rmtree(tombstone, ignore_errors=True)


class ConcurrencyGate:
    def __init__(
        self,
        locks_root: Path | None = None,
        *,
        ownership: LockOwnership | None = None,
        acquire_timeout: float = 5.0,
        lease_seconds: float = 30.0,
    ) -> None:
        self._exclusive = asyncio.Lock()
        self._per_capability: dict[str, asyncio.Lock] = {}
        self._per_resource: dict[str, asyncio.Lock] = {}
        self._locks_root = Path(locks_root) if locks_root is not None else None
        self._ownership = ownership or LockOwnership()
        self._acquire_timeout = acquire_timeout
        self._lease_seconds = lease_seconds

    def _cap_lock(self, canonical: str) -> asyncio.Lock:
        lock = self._per_capability.get(canonical)
        if lock is None:
            lock = asyncio.Lock()
            self._per_capability[canonical] = lock
        return lock

    def _resource_lock(self, key: str) -> asyncio.Lock:
        lock = self._per_resource.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._per_resource[key] = lock
        return lock

    def _acquire_durable(self, key: str) -> _DurableLease:
        assert self._locks_root is not None
        self._locks_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        lock_path = self._locks_root / key
        guard = self._locks_root / ".gate.lock"
        deadline = time.monotonic() + self._acquire_timeout
        owner_name = f"{socket.gethostname()}:{os.getpid()}"
        while True:
            token = secrets.token_hex(16)
            acquired = False
            with exclusive_file_lock(guard):
                try:
                    lock_path.mkdir(mode=0o700)
                    acquired = True
                except FileExistsError:
                    self._recover_if_stale(lock_path)
                if acquired:
                    atomic_write_json(
                        lock_path / "owner.json",
                        {
                            "token": token,
                            "owner": owner_name,
                            "heartbeat_ns": time.time_ns(),
                            "lease_seconds": self._lease_seconds,
                        },
                    )
                    return _DurableLease(lock_path, token)
            if time.monotonic() >= deadline:
                raise LockContention(key)
            time.sleep(0.02)

    def _recover_if_stale(self, lock_path: Path) -> None:
        meta = lock_path / "owner.json"
        try:
            import json

            payload = json.loads(meta.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            shutil.rmtree(lock_path, ignore_errors=True)
            return
        lease = float(payload.get("lease_seconds") or self._lease_seconds)
        heartbeat = int(payload.get("heartbeat_ns") or 0)
        if heartbeat and (time.time_ns() - heartbeat) / 1e9 > lease:
            shutil.rmtree(lock_path, ignore_errors=True)

    @asynccontextmanager
    async def hold(
        self,
        capability: BoundCapability,
        request: BaseModel,
        *,
        ownership: LockOwnership | None = None,
    ) -> AsyncIterator[str | None]:
        owned = ownership or self._ownership
        mode = capability.definition.effects.concurrency
        canonical = capability.definition.id.canonical()
        if mode is ConcurrencyMode.PARALLEL_SAFE:
            yield f"parallel:{canonical}"
            return
        key = coordination_lock_key(capability, request, owned)
        lease: _DurableLease | None = None
        memory: asyncio.Lock | None = None
        if mode is ConcurrencyMode.EXCLUSIVE:
            memory = self._exclusive
            evidence = f"exclusive:{canonical}:{key}"
        elif mode is ConcurrencyMode.SERIAL_PER_CAPABILITY:
            memory = self._cap_lock(canonical)
            evidence = f"serial_capability:{canonical}:{key}"
        else:
            memory = self._resource_lock(key)
            evidence = f"serial_resource:{key}"
        try:
            await asyncio.wait_for(memory.acquire(), timeout=self._acquire_timeout)
        except TimeoutError as exc:
            raise LockContention(key) from exc
        except asyncio.CancelledError:
            raise
        try:
            if self._locks_root is not None:
                try:
                    lease = await asyncio.wait_for(
                        asyncio.to_thread(self._acquire_durable, key),
                        timeout=self._acquire_timeout + 1,
                    )
                except TimeoutError as exc:
                    raise LockContention(key) from exc
            yield evidence
        finally:
            if lease is not None:
                lease.release()
            memory.release()
