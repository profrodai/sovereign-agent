"""The Plugin contract (v0.3, Module 3).

Two handles every pluggable thing in sovereign-agent exposes:

  - `name` — what an operator types in a config file. Two instances of the
    same plugin kind can have different names.
  - `kind` — what the orchestrator buckets registries by, applied as a
    class variable. Every channel adapter has kind="channel"; every tool
    has kind="tool". Used by `Registry.for_kind()` and by the generic
    `kind_filter` registration check.

Distinct from `Discoverable` (sovereign_agent.discovery). Plugin is the
*registry* contract — who's named, who's loaded, how the operator enables
or disables capability. Discoverable is the *schema-export* contract — how
an LLM learns what an extension can do at runtime. A thing can be:

  - Both (tools — they register AND they're shown to the LLM)
  - Plugin only (channel adapters — operators name them but the LLM
    doesn't pick a channel)
  - Discoverable only (rare; usually a schema-exporter with no need to be
    named by an operator)
  - Neither (private helpers)

The README's eighth decision says *"prompts are advisory; the registry is
physics."* Plugin is what makes that physics generalise: a channel
registry, a tool registry, and any future judge or memory registry all
speak the same vocabulary, so per-kind policy (sandboxing, rate limits,
audit logging) can be applied without coupling to specific plugin classes.
"""

from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class Plugin(Protocol):
    """The structural contract every plugin satisfies.

    Implementations need not inherit from anything. Satisfying the two
    attributes below is enough — `isinstance(obj, Plugin)` succeeds for
    any object with a `name: str` instance attribute and a `kind: str`
    class attribute.

    Why a ClassVar for `kind`: every Telegram channel adapter has the
    same kind ("channel"); the kind is a property of the *class*, not of
    each instance. `name` varies per instance (one bot named "support",
    another named "ops") so it's an instance attribute. Putting kind on
    the class also means a subclass declaring `kind = "channel"` once
    propagates to every instance — no constructor boilerplate.
    """

    name: str
    kind: ClassVar[str]


__all__ = ["Plugin"]
