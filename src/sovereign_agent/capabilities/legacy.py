"""Adapt deprecated @register_tool functions into ZeoCore-bound capabilities."""

from __future__ import annotations

import hashlib
import json
import warnings
from typing import Any

from zeo_core.contracts import CapabilityExample, ConcurrencyMode, EffectKind
from zeo_core.tools import BoundCapability
from zeo_core.tools.compat.sovereign_style import sovereign_style_capability

from sovereign_agent.tools.registry import ToolResult, _RegisteredTool

_RUNTIME_COMMAND_NAMES = frozenset(
    {"complete_task", "handoff_to_structured", "abort_execution", "session_status"}
)


class UnrepresentableLegacyTool(ValueError):
    """Legacy semantics that cannot be adapted truthfully into ZeoCore."""


def _capability_id_for(name: str, version: str) -> str:
    slug = name.replace("-", "_")
    return f"sovereign.legacy.{slug}@{version}"


def registered_tool_to_bound(tool: _RegisteredTool) -> BoundCapability:
    """Wrap a legacy registered tool as a BoundCapability. Migration only."""
    if tool.name in _RUNTIME_COMMAND_NAMES:
        raise UnrepresentableLegacyTool(
            f"{tool.name!r} is a runtime command and cannot be adapted as a ZeoCore capability"
        )
    if tool.verify_args is not None:
        raise UnrepresentableLegacyTool(
            f"{tool.name!r} uses verify_args, which has no truthful ZeoCore guard mapping"
        )
    schema = tool.parameters_schema or {}
    if schema.get("type") not in {None, "object"}:
        raise UnrepresentableLegacyTool(f"{tool.name!r} parameters are not a JSON object schema")
    effects = (EffectKind.READ,) if tool.parallel_safe else (EffectKind.WRITE,)
    concurrency = (
        ConcurrencyMode.PARALLEL_SAFE
        if tool.parallel_safe
        else ConcurrencyMode.SERIAL_PER_CAPABILITY
    )
    raw_examples = tool.examples or [{"input": {}, "output": {"note": "legacy"}}]
    examples = tuple(
        CapabilityExample(request=item.get("input") or {}, response=item.get("output"))
        for item in raw_examples
    )

    def _legacy(**kwargs: Any) -> Any:
        result = tool.fn(**kwargs)
        if isinstance(result, ToolResult):
            return result.output
        return result

    _legacy.__name__ = tool.name
    decorator = sovereign_style_capability(
        capability_id=_capability_id_for(tool.name, tool.version),
        description=tool.description,
        effects=effects,
        examples=examples,
        concurrency=concurrency,
        error_codes=tuple(c for c in tool.error_codes if c.startswith(("ZEO_", "ZC_", "QC_")))
        or ("ZEO_CAP_UNEXPECTED",),
    )
    return decorator(_legacy)


def warn_legacy_register(name: str) -> None:
    warnings.warn(
        f"register_tool({name!r}) is deprecated; author a ZeoCore @capability. "
        "The legacy surface remains compatibility-only through 2027-02-23 "
        "(v0.7 breaking-change window).",
        DeprecationWarning,
        stacklevel=3,
    )


def arguments_digest(arguments: dict[str, Any]) -> str:
    payload = json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()
