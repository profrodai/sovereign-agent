"""Sovereign-owned lock acquisition for ZeoCore concurrency declarations."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from pydantic import BaseModel
from zeo_core.contracts import ConcurrencyMode
from zeo_core.tools import BoundCapability, resource_coordination_key


class ConcurrencyGate:
    def __init__(self) -> None:
        self._exclusive = asyncio.Lock()
        self._per_capability: dict[str, asyncio.Lock] = {}
        self._per_resource: dict[str, asyncio.Lock] = {}

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

    @asynccontextmanager
    async def hold(
        self,
        capability: BoundCapability,
        request: BaseModel,
    ) -> AsyncIterator[str | None]:
        mode = capability.definition.effects.concurrency
        canonical = capability.definition.id.canonical()
        evidence: str | None = None
        if mode is ConcurrencyMode.EXCLUSIVE:
            await self._exclusive.acquire()
            evidence = f"exclusive:{canonical}"
            try:
                yield evidence
            finally:
                self._exclusive.release()
            return
        if mode is ConcurrencyMode.SERIAL_PER_CAPABILITY:
            lock = self._cap_lock(canonical)
            await lock.acquire()
            evidence = f"serial_capability:{canonical}"
            try:
                yield evidence
            finally:
                lock.release()
            return
        if mode is ConcurrencyMode.SERIAL_PER_RESOURCE:
            key = resource_coordination_key(capability, request) or canonical
            lock = self._resource_lock(key)
            await lock.acquire()
            evidence = f"serial_resource:{key}"
            try:
                yield evidence
            finally:
                lock.release()
            return
        yield evidence
