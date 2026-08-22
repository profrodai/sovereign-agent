"""v0.3 Module 3 — Registry[T] generic behavior.

Twelve tests covering the surface: register, get, get_or_none, for_kind,
list, names, unregister, dunders, kind_filter enforcement, re-registration
after unregister, error shapes.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from sovereign_agent.errors import ValidationError
from sovereign_agent.registries import Registry


class FakeChannel:
    kind: ClassVar[str] = "channel"

    def __init__(self, name: str) -> None:
        self.name = name


class FakeTool:
    kind: ClassVar[str] = "tool"

    def __init__(self, name: str) -> None:
        self.name = name


def test_register_adds_plugin():
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("cli"))
    assert "cli" in reg
    assert len(reg) == 1


def test_register_duplicate_name_raises():
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("cli"))
    with pytest.raises(ValidationError) as exc:
        reg.register(FakeChannel("cli"))
    assert exc.value.code == "SA_VAL_BAD_TYPE"
    assert "already registered" in exc.value.message


def test_kind_filter_rejects_wrong_kind():
    reg: Registry[FakeChannel] = Registry(kind_filter="channel")
    with pytest.raises(ValidationError) as exc:
        reg.register(FakeTool("read_file"))  # type: ignore[arg-type]
    assert exc.value.code == "SA_VAL_BAD_TYPE"
    assert "expected kind 'channel'" in exc.value.message
    assert "got 'tool'" in exc.value.message


def test_kind_filter_none_accepts_any_plugin():
    reg = Registry(kind_filter=None)
    reg.register(FakeChannel("cli"))
    reg.register(FakeTool("read_file"))
    assert len(reg) == 2


def test_get_returns_plugin():
    reg: Registry[FakeChannel] = Registry()
    adapter = FakeChannel("cli")
    reg.register(adapter)
    assert reg.get("cli") is adapter


def test_get_missing_raises():
    reg: Registry[FakeChannel] = Registry()
    with pytest.raises(ValidationError) as exc:
        reg.get("nonexistent")
    assert exc.value.code == "SA_VAL_BAD_TYPE"
    assert "is not registered" in exc.value.message


def test_get_or_none_returns_none_for_missing():
    reg: Registry[FakeChannel] = Registry()
    assert reg.get_or_none("nonexistent") is None


def test_for_kind_returns_matching_plugins_in_order():
    reg = Registry(kind_filter=None)
    reg.register(FakeChannel("cli"))
    reg.register(FakeTool("read_file"))
    reg.register(FakeChannel("telegram"))
    channels = reg.for_kind("channel")
    assert [c.name for c in channels] == ["cli", "telegram"]
    tools = reg.for_kind("tool")
    assert [t.name for t in tools] == ["read_file"]


def test_unregister_removes():
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("cli"))
    reg.unregister("cli")
    assert "cli" not in reg
    assert len(reg) == 0


def test_unregister_missing_is_silent():
    reg: Registry[FakeChannel] = Registry()
    reg.unregister("never_registered")  # no exception


def test_list_returns_in_registration_order():
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("z"))
    reg.register(FakeChannel("a"))
    reg.register(FakeChannel("m"))
    assert [p.name for p in reg.list()] == ["z", "a", "m"]


def test_dunders_work():
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("cli"))
    reg.register(FakeChannel("telegram"))
    assert "cli" in reg
    assert "missing" not in reg
    assert 42 not in reg  # __contains__ tolerates non-str
    assert len(reg) == 2
    assert [p.name for p in reg] == ["cli", "telegram"]


def test_re_registration_after_unregister_works():
    """Unregister + re-register should not leave a ghost in the dict."""
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("cli"))
    reg.unregister("cli")
    reg.register(FakeChannel("cli"))  # must not raise
    assert "cli" in reg


def test_names_returns_keys_in_registration_order():
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("z"))
    reg.register(FakeChannel("a"))
    assert reg.names() == ["z", "a"]


def test_list_returns_a_copy_not_a_view():
    """Mutating the result of list() must not mutate the registry."""
    reg: Registry[FakeChannel] = Registry()
    reg.register(FakeChannel("cli"))
    snapshot = reg.list()
    snapshot.clear()
    assert len(reg) == 1  # registry unchanged
