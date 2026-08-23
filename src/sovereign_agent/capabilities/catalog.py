"""Frozen per-execution capability catalog and reversible provider projection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from zeo_core.adapters.llm_tools.openai import openai_function_name, project_openai_tool
from zeo_core.contracts import CapabilityId, CapabilityManifest
from zeo_core.tools import CapabilityRegistry

from sovereign_agent.contracts._core import ContractValidationError


@dataclass(frozen=True)
class ProjectedCapability:
    provider_name: str
    canonical_id: CapabilityId


@dataclass(frozen=True)
class FrozenCapabilityEntry:
    canonical_id: str
    projection_name: str
    version: str
    effects_concurrency: str
    grant: bool


@dataclass(frozen=True)
class FrozenExecutionCatalog:
    entries: tuple[FrozenCapabilityEntry, ...]
    digest: str
    projection_index: dict[str, str]


class ProjectionCollision(ValueError):
    pass


def freeze_catalog(
    registry: CapabilityRegistry,
    *,
    granted: frozenset[str] | None = None,
    extra_names: frozenset[str] = frozenset(),
) -> FrozenExecutionCatalog:
    entries: list[FrozenCapabilityEntry] = []
    index: dict[str, str] = {}
    for bound in registry.list_all():
        manifest = CapabilityManifest.from_definition(bound.definition)
        projected = project_openai_tool(manifest)
        if not projected.ok or projected.tool is None:
            reason = projected.incompatibility.reason if projected.incompatibility else "unknown"
            raise ProjectionCollision(f"cannot project {bound.definition.id.canonical()}: {reason}")
        name = projected.tool.function["name"]
        if len(name) > 64:
            raise ProjectionCollision(f"projected name exceeds 64 characters: {name}")
        if name in index or name in extra_names:
            raise ProjectionCollision(f"duplicate projected name {name!r}")
        canonical = bound.definition.id.canonical()
        index[name] = canonical
        entries.append(
            FrozenCapabilityEntry(
                canonical_id=canonical,
                projection_name=name,
                version=bound.definition.id.version,
                effects_concurrency=bound.definition.effects.concurrency.value,
                grant=granted is None or canonical in granted,
            )
        )
    payload = [
        {
            "canonical_id": e.canonical_id,
            "projection_name": e.projection_name,
            "version": e.version,
            "effects_concurrency": e.effects_concurrency,
            "grant": e.grant,
        }
        for e in entries
    ]
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return FrozenExecutionCatalog(entries=tuple(entries), digest=digest, projection_index=index)


def resolve_projected_name(catalog: FrozenExecutionCatalog, provider_name: str) -> str:
    canonical = catalog.projection_index.get(provider_name)
    if canonical is None:
        raise ContractValidationError(
            f"provider call {provider_name!r} is not in the frozen catalog"
        )
    return canonical


def openai_tools_from_registry(registry: CapabilityRegistry) -> list[dict]:
    tools: list[dict] = []
    seen: set[str] = set()
    for bound in registry.list_all():
        manifest = CapabilityManifest.from_definition(bound.definition)
        result = project_openai_tool(manifest)
        if not result.ok or result.tool is None:
            raise ProjectionCollision(f"cannot project {bound.definition.id.canonical()}")
        name = result.tool.function["name"]
        if name in seen:
            raise ProjectionCollision(f"duplicate projected name {name!r}")
        seen.add(name)
        tools.append(result.tool.model_dump())
    return tools


# Re-export helper used by tests
openai_function_name = openai_function_name
