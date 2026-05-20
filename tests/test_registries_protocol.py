"""v0.3 Module 3 — Plugin protocol satisfaction tests.

Six tests confirming the structural contract works as documented:

  - A class with `name` instance attr and `kind` class attr satisfies Plugin
  - Missing `kind` fails
  - Missing `name` fails
  - `isinstance` works at runtime (the @runtime_checkable promise)
  - `kind` can be set on a class without inheritance
  - The Plugin protocol does NOT impose any methods — pure attribute contract
"""

from __future__ import annotations

from typing import ClassVar

from sovereign_agent.registries import Plugin


class GoodPlugin:
    """A class that satisfies Plugin: name + kind class attribute."""

    kind: ClassVar[str] = "goodkind"

    def __init__(self, name: str) -> None:
        self.name = name


class NoKind:
    """A class with name but no kind. Must NOT satisfy Plugin."""

    def __init__(self, name: str) -> None:
        self.name = name


class NoName:
    """A class with kind but no name. Must NOT satisfy Plugin."""

    kind: ClassVar[str] = "nokind"


def test_class_with_name_and_kind_satisfies_plugin():
    obj = GoodPlugin(name="alice")
    assert isinstance(obj, Plugin)


def test_missing_kind_does_not_satisfy():
    obj = NoKind(name="bob")
    assert not isinstance(obj, Plugin)


def test_missing_name_does_not_satisfy():
    obj = NoName()
    assert not isinstance(obj, Plugin)


def test_plugin_is_runtime_checkable():
    """The @runtime_checkable decorator is what makes isinstance() work
    against a Protocol. Verify the marker class attribute is present."""
    # _is_runtime_protocol is the CPython implementation detail; rather
    # than depend on it, the real test is that isinstance() actually
    # works on a plain object — which the other tests in this file
    # collectively prove. This test is the explicit assertion.
    obj = GoodPlugin(name="x")
    # No exception means runtime-checkable.
    assert isinstance(obj, Plugin)


def test_kind_can_be_assigned_without_inheritance():
    """The Plugin protocol does NOT require subclassing. Any class with
    the right shape satisfies it. This is critical for the didactic story:
    'satisfying the structural contract is enough'."""

    class Standalone:
        kind: ClassVar[str] = "stand"

        def __init__(self, name: str) -> None:
            self.name = name

    assert isinstance(Standalone(name="s"), Plugin)


def test_plugin_imposes_no_methods():
    """A pure attribute contract — Plugin does NOT require register(),
    setup(), or anything else. Verify by satisfying it with the most
    minimal possible class."""

    class Minimal:
        kind: ClassVar[str] = "minimal"
        name = "tiny"  # class attr is fine too; Protocol checks presence

    assert isinstance(Minimal(), Plugin)
