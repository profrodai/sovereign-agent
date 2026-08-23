"""Unit 8 removal gate: legacy public tools remain until a breaking-release SOW."""

from __future__ import annotations

import sovereign_agent
from sovereign_agent.tools.registry import ToolRegistry, ToolResult, register_tool


def test_legacy_public_surface_still_importable() -> None:
    assert "register_tool" in sovereign_agent.__all__
    assert "ToolRegistry" in sovereign_agent.__all__
    assert "ToolResult" in sovereign_agent.__all__
    assert callable(register_tool)
    assert ToolRegistry is not None
    assert ToolResult is not None


def test_quickstart_still_exports_register_tool_during_compat_window() -> None:
    # Removal of register_tool from the public quickstart is a Unit 8 gate,
    # authorized only by a separately approved breaking release.
    import inspect

    from sovereign_agent import register_tool as exported

    assert inspect.isfunction(exported)
