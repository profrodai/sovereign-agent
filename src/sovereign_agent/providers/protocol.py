"""Structural contract for pluggable agent providers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import ClassVar, Protocol, runtime_checkable

from .events import ProviderEventType
from .models import InvocationRequest, InvocationResult, ProviderCapabilities

type EventCallback = Callable[[ProviderEventType], None | Awaitable[None]]


@runtime_checkable
class AgentProvider(Protocol):
    """A named provider that executes one normalized invocation."""

    name: str
    kind: ClassVar[str]
    capabilities: ProviderCapabilities

    async def invoke(
        self,
        request: InvocationRequest,
        *,
        observers: Sequence[EventCallback] = (),
        activity_callbacks: Sequence[EventCallback] = (),
    ) -> InvocationResult: ...


__all__ = ["AgentProvider", "EventCallback"]
