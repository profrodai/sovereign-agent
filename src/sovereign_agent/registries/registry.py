"""Registry[T]: a name-keyed collection of plugins (v0.3, Module 3).

This is the production-grade dissolve of the duplication the M1
ChannelRegistry's docstring promised would land in Module 3. The same
register/get/list surface, parameterised by a Plugin type. The
ChannelRegistry that v0.3 Module 1 introduced now subclasses this and
adds only the channel-specific `for_channel_type()` narrowing.

The teaching arc is: Chapter 6 introduces "a registry" as a plain
dict-wrapper for one concrete case (channels). Chapter 8 generalises by
naming the contract (Plugin) and turning the dict-wrapper into a generic
(Registry[T]). The reader has felt the duplication of similar-looking
registries; the abstraction earns its place by dissolving it.

## Why module-level singletons live elsewhere

Each subpackage that defines a plugin kind owns its singleton:

    sovereign_agent.channels.CHANNEL_REGISTRY: Registry[ChannelAdapter]

The Registry class itself does not define a global instance. This is
deliberate — making the singletons live at module level means

    python -c "from sovereign_agent.channels import CHANNEL_REGISTRY; \\
               print(CHANNEL_REGISTRY.names())"

is the operator's primary introspection, and tests can monkeypatch the
module attribute without reaching into class state.

## What this does NOT do

- **No entry-point discovery.** v0.3 keeps plugin registration in-process.
  Loading plugins from pip-installed packages via importlib.metadata is a
  v0.4 concern.
- **No subscription / observation API.** The orchestrator polls the
  registry at startup (and `add_adapter()` mutates it at runtime). There
  is no "registry changed" event.
- **No removal-while-iterating.** `list()` and `for_kind()` return copies;
  mutating during iteration of the original collection would be a bug.
"""

from __future__ import annotations

from collections.abc import Iterator

from sovereign_agent.errors import ValidationError
from sovereign_agent.registries.protocol import Plugin


class Registry[T: Plugin]:
    """Ordered, name-keyed collection of plugins.

    Uses PEP 695 type parameter syntax (`class C[T: Bound]:`) — Python
    3.12+. The bound `T: Plugin` is enforced by the type checker; at
    runtime, `kind_filter` enforces the plugin kind dynamically.

    Parameters
    ----------
    kind_filter:
        If set, `register()` rejects any plugin whose `kind` doesn't match.
        This makes the singleton registries safe: registering a tool into
        CHANNEL_REGISTRY is a clear error at registration time, not a
        confusing failure later.
    """

    def __init__(self, *, kind_filter: str | None = None) -> None:
        self._items: dict[str, T] = {}
        self._kind_filter = kind_filter

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def register(self, plugin: T) -> None:
        """Add a plugin. Raises ValidationError on duplicate name or wrong kind."""
        if self._kind_filter is not None and plugin.kind != self._kind_filter:
            raise ValidationError(
                code="SA_VAL_BAD_TYPE",
                message=(
                    f"registry rejects plugin {plugin.name!r}: "
                    f"expected kind {self._kind_filter!r}, got {plugin.kind!r}"
                ),
                context={"plugin_name": plugin.name, "expected_kind": self._kind_filter},
            )
        if plugin.name in self._items:
            raise ValidationError(
                code="SA_VAL_BAD_TYPE",
                message=f"plugin {plugin.name!r} is already registered",
                context={"registered": sorted(self._items)},
            )
        self._items[plugin.name] = plugin

    def unregister(self, name: str) -> None:
        """Remove a plugin by name. Silent if not registered."""
        self._items.pop(name, None)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------
    def get(self, name: str) -> T:
        """Fetch a plugin by name. Raises ValidationError if absent."""
        if name not in self._items:
            raise ValidationError(
                code="SA_VAL_BAD_TYPE",
                message=f"plugin {name!r} is not registered",
                context={"registered": sorted(self._items)},
            )
        return self._items[name]

    def get_or_none(self, name: str) -> T | None:
        """Fetch by name, or None if absent. The non-raising counterpart of get()."""
        return self._items.get(name)

    def for_kind(self, kind: str) -> list[T]:
        """All plugins whose `kind` matches, in registration order."""
        return [p for p in self._items.values() if p.kind == kind]

    def list(self) -> list[T]:
        """All plugins, in registration order."""
        return list(self._items.values())

    def names(self) -> list[str]:
        """All registered plugin names, in registration order."""
        return list(self._items.keys())

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------
    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._items

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        # Iterating yields plugins, not names — most natural for `for adapter
        # in CHANNEL_REGISTRY:`. Use .names() if you want the keys.
        return iter(self._items.values())


__all__ = ["Registry"]
