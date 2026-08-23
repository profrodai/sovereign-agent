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


def _capability_id_for(name: str, version: str) -> str:
    slug = name.replace("-", "_")
    return f"sovereign.legacy.{slug}@{version}"


def registered_tool_to_bound(tool: _RegisteredTool) -> BoundCapability:
    """Wrap a legacy registered tool as a BoundCapability. Migration only."""
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
        "The legacy surface remains through v0.5.",
        DeprecationWarning,
        stacklevel=3,
    )


def arguments_digest(arguments: dict[str, Any]) -> str:
    payload = json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()
