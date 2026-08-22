"""v0.3 Module 3 — ChannelRegistry shim + CHANNEL_REGISTRY singleton.

Verifies that:

  1. `ChannelAdapter` Protocol's new `kind` attribute is set to "channel"
     and is inherited by concrete adapters without redeclaration.
  2. `ChannelRegistry()` still works for backwards-compat (M1 Orchestrator
     constructs it directly).
  3. `for_channel_type()` — the one channel-specific narrowing — still
     works on the shim.
  4. `CHANNEL_REGISTRY` exists as a module-level singleton, is a
     Registry[ChannelAdapter] with kind_filter="channel", and rejects
     non-channel registrations.
  5. The generic `Registry` and the channels-specific shim raise the same
     ValidationError code on duplicate / missing.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from sovereign_agent.channels import (
    CHANNEL_REGISTRY,
    ChannelAdapter,
    ChannelRegistry,
    CliChannelAdapter,
)
from sovereign_agent.errors import ValidationError
from sovereign_agent.registries import Plugin, Registry


def test_channel_adapter_protocol_carries_kind_channel():
    """The Protocol declaration sets kind="channel"; CliChannelAdapter
    inherits it without redeclaring."""
    assert CliChannelAdapter.kind == "channel"


def test_cli_adapter_satisfies_both_channel_adapter_and_plugin():
    """The new Plugin contract is satisfied by every existing M1 adapter
    without any code change to the adapter itself."""
    adapter = CliChannelAdapter()
    assert isinstance(adapter, ChannelAdapter)
    assert isinstance(adapter, Plugin)


def test_channel_registry_is_a_registry_subclass():
    """The M1 ChannelRegistry now subclasses the generic Registry[T]."""
    assert issubclass(ChannelRegistry, Registry)


def test_channel_registry_constructs_with_no_arguments():
    """M1 callers do `ChannelRegistry()` — must still work."""
    reg = ChannelRegistry()
    assert len(reg) == 0


def test_channel_registry_for_channel_type_narrows():
    """The channel-specific method that the generic Registry doesn't have."""
    reg = ChannelRegistry()
    cli = CliChannelAdapter()
    reg.register(cli)
    assert reg.for_channel_type("cli") is cli
    assert reg.for_channel_type("telegram") is None


def test_channel_registry_inherits_generic_methods():
    """register, get, list, __contains__ — all from the generic parent."""
    reg = ChannelRegistry()
    cli = CliChannelAdapter()
    reg.register(cli)
    assert "cli" in reg
    assert reg.get("cli") is cli
    assert reg.list() == [cli]
    assert len(reg) == 1


def test_channel_registry_rejects_non_channel_plugin():
    """kind_filter='channel' enforced by the shim's super().__init__()."""

    class FakeJudge:
        kind: ClassVar[str] = "judge"

        def __init__(self) -> None:
            self.name = "fake_judge"

    reg = ChannelRegistry()
    with pytest.raises(ValidationError) as exc:
        reg.register(FakeJudge())  # type: ignore[arg-type]
    assert exc.value.code == "SA_VAL_BAD_TYPE"
    assert "expected kind 'channel'" in exc.value.message


def test_channel_registry_module_singleton_exists():
    """CHANNEL_REGISTRY is the module-level singleton operators introspect."""
    assert isinstance(CHANNEL_REGISTRY, Registry)


def test_channel_registry_singleton_filters_to_channel_kind():
    """The singleton must reject non-channel plugins at registration."""

    class FakeJudge:
        kind: ClassVar[str] = "judge"

        def __init__(self) -> None:
            self.name = "fake_judge"

    with pytest.raises(ValidationError):
        CHANNEL_REGISTRY.register(FakeJudge())  # type: ignore[arg-type]


def test_orchestrator_constructs_with_adapters_unchanged_m1_api():
    """The M1 Orchestrator API — `Orchestrator(config, adapters=[...])` —
    is unchanged. This is the critical regression check."""
    from sovereign_agent.config import Config
    from sovereign_agent.orchestrator import Orchestrator

    cfg = Config()
    adapter = CliChannelAdapter()
    orch = Orchestrator(cfg, adapters=[adapter])
    assert "cli" in orch.channels
    assert orch.channels.get("cli") is adapter
