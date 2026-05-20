"""ChannelRegistry: the set of adapters an orchestrator is running.

v0.3 Module 1 ships this as a small, standalone class — a name-keyed dict
with a register/get/list surface. v0.3 Module 3 introduces a generic
`Registry[T]` and a process-level `CHANNEL_REGISTRY` singleton; at that
point this class becomes a thin compatibility shim over the generic one.

It is kept deliberately specific *now* so Chapter 6 can introduce "a
registry" as a plain dict-wrapper for one concrete case, before Chapter 8
generalises the pattern across four cases. The student sees the specific
thing before the abstraction — which is the whole teaching philosophy of
this library (an abstraction earns its place by dissolving a failure the
student has already felt).
"""

from __future__ import annotations

from sovereign_agent.channels.adapter import ChannelAdapter
from sovereign_agent.errors import ValidationError


class ChannelRegistry:
    """An ordered, name-keyed collection of channel adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, ChannelAdapter] = {}

    def register(self, adapter: ChannelAdapter) -> None:
        """Add an adapter. Raises if an adapter with the same name exists."""
        if adapter.name in self._adapters:
            raise ValidationError(
                code="SA_VAL_BAD_TYPE",
                message=f"channel adapter {adapter.name!r} is already registered",
                context={"registered": sorted(self._adapters)},
            )
        self._adapters[adapter.name] = adapter

    def unregister(self, name: str) -> None:
        """Remove an adapter by name. Silent if it isn't registered."""
        self._adapters.pop(name, None)

    def get(self, name: str) -> ChannelAdapter:
        """Fetch an adapter by name. Raises if it isn't registered."""
        if name not in self._adapters:
            raise ValidationError(
                code="SA_VAL_BAD_TYPE",
                message=f"channel adapter {name!r} is not registered",
                context={"registered": sorted(self._adapters)},
            )
        return self._adapters[name]

    def for_channel_type(self, channel_type: str) -> ChannelAdapter | None:
        """Return the first adapter that handles `channel_type`, or None.

        The orchestrator uses this to find the adapter to deliver a
        response through, given only a session's channel binding.
        """
        for adapter in self._adapters.values():
            if adapter.channel_type == channel_type:
                return adapter
        return None

    def list(self) -> list[ChannelAdapter]:
        """All registered adapters, in registration order."""
        return list(self._adapters.values())

    def __contains__(self, name: str) -> bool:
        return name in self._adapters

    def __len__(self) -> int:
        return len(self._adapters)


__all__ = ["ChannelRegistry"]
