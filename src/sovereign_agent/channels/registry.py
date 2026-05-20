"""ChannelRegistry: the set of adapters an orchestrator is running.

As of v0.3 Module 3, this is a thin compatibility shim over the generic
`Registry[T]` defined in `sovereign_agent.registries`. The M1 docstring
promised this dissolve; M3 delivers it.

Why a shim still exists:

  - Backwards compatibility. The Orchestrator's `__init__` constructs
    `ChannelRegistry()` directly. Removing the class would be a breaking
    change for any v0.3.0 user.
  - One channel-specific method. `for_channel_type()` narrows further
    than the generic `for_kind("channel")` does, because every adapter
    has kind="channel" but channel_type varies (cli, telegram, slack).
    Different layers want different granularities — the orchestrator
    iterates by kind; the router resolves by channel_type.

For new code, prefer:

  - The module-level singleton: `from sovereign_agent.channels import
    CHANNEL_REGISTRY`. This is what the operator introspects.
  - A scoped registry: `Registry[ChannelAdapter](kind_filter="channel")`,
    for cases where you want isolation from the global.

The teaching arc behind this shim: Chapter 6 introduced "a registry" as a
plain dict-wrapper for one concrete case (channels). Chapter 8 generalises
the pattern across four cases by naming the contract (Plugin) and turning
the dict-wrapper into a generic (Registry[T]). The shim is what production
code looks like during the transition — real refactors are incremental;
the first instance of an abstraction earns its place by replacing the
simplest case first.
"""

from __future__ import annotations

from sovereign_agent.channels.adapter import ChannelAdapter
from sovereign_agent.registries import Registry


class ChannelRegistry(Registry[ChannelAdapter]):
    """An ordered, name-keyed collection of channel adapters.

    Backwards-compatible with the M1 signature: `ChannelRegistry()` takes
    no arguments, enforces kind="channel" via the parent class's
    kind_filter, and inherits register / get / list / __contains__ /
    __len__ / __iter__ from `Registry[T]`. The only addition over the
    generic is `for_channel_type()`.
    """

    def __init__(self) -> None:
        super().__init__(kind_filter="channel")

    def for_channel_type(self, channel_type: str) -> ChannelAdapter | None:
        """Return the first adapter that handles `channel_type`, or None.

        The orchestrator uses this to find the adapter to deliver a
        response through, given only a session's channel binding.
        """
        for adapter in self.list():
            if adapter.channel_type == channel_type:
                return adapter
        return None


__all__ = ["ChannelRegistry"]
