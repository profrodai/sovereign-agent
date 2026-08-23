"""Contained fan-out for provider event observers and activity callbacks."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Sequence
from dataclasses import dataclass

from .events import ProviderEventType
from .protocol import EventCallback

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObserverFailure:
    callback: str
    event_sequence: int
    error: str


class EventFanout:
    """Deliver events without allowing instrumentation to break execution."""

    def __init__(
        self,
        observers: Sequence[EventCallback] = (),
        activity_callbacks: Sequence[EventCallback] = (),
    ) -> None:
        self._observers = tuple(observers)
        self._activity_callbacks = tuple(activity_callbacks)
        self._failures: list[ObserverFailure] = []

    @property
    def failures(self) -> tuple[ObserverFailure, ...]:
        return tuple(self._failures)

    async def emit(self, event: ProviderEventType) -> None:
        # Keep the groups separate: an observer failure must never prevent
        # activity callbacks from receiving the same event.
        for callback in (*self._observers, *self._activity_callbacks):
            try:
                result = callback(event)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:  # noqa: BLE001
                name = getattr(callback, "__qualname__", repr(callback))
                self._failures.append(
                    ObserverFailure(
                        callback=name,
                        event_sequence=event.sequence,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                log.exception(
                    "provider event callback %s failed at sequence %d",
                    name,
                    event.sequence,
                )


__all__ = ["EventFanout", "ObserverFailure"]
