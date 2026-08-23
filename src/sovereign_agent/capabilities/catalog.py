"""Frozen per-execution capability catalog and reversible provider projection."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from zeo_core.adapters.llm_tools.openai import openai_function_name, project_openai_tool
from zeo_core.contracts import CapabilityId, CapabilityManifest
from zeo_core.tools import CapabilityRegistry

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent.contracts._core import ContractValidationError
from sovereign_agent.contracts.redaction import redact_json

CATALOG_RELATIVE = Path("capabilities") / "catalog.json"


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
    schema_digest: str
    definition_digest: str
    source_package_version: str


@dataclass(frozen=True)
class FrozenExecutionCatalog:
    entries: tuple[FrozenCapabilityEntry, ...]
    digest: str
    projection_index: dict[str, str]


class ProjectionCollision(ValueError):
    pass


class DuplicateCapabilityId(ValueError):
    pass


class CatalogMismatch(ValueError):
    """Resumed execution's live registry does not match the frozen catalog."""


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode()).hexdigest()


def definition_digest(bound: Any) -> str:
    manifest = CapabilityManifest.from_definition(bound.definition)
    dumped = manifest.model_dump(mode="json")
    return _digest(dumped)


def schema_digest(bound: Any) -> str:
    manifest = CapabilityManifest.from_definition(bound.definition)
    return _digest(manifest.request_schema)


def source_package_version(bound: Any) -> str:
    fn = getattr(bound, "_fn", None) or getattr(bound, "fn", None)
    module = getattr(fn, "__module__", "") or ""
    if module.startswith("sovereign_agent"):
        return f"sovereign-agent=={importlib.metadata.version('sovereign-agent')}"
    if module.startswith("zeo_core"):
        return f"zeocore=={importlib.metadata.version('zeocore')}"
    return f"zeocore=={importlib.metadata.version('zeocore')};sovereign-agent=={importlib.metadata.version('sovereign-agent')}"


def freeze_catalog(
    registry: CapabilityRegistry,
    *,
    granted: frozenset[str] | None = None,
    extra_names: frozenset[str] = frozenset(),
) -> FrozenExecutionCatalog:
    entries: list[FrozenCapabilityEntry] = []
    index: dict[str, str] = {}
    seen_ids: set[str] = set()
    for bound in registry.list_all():
        canonical = bound.definition.id.canonical()
        if canonical in seen_ids:
            raise DuplicateCapabilityId(f"duplicate capability identity: {canonical}")
        seen_ids.add(canonical)
        manifest = CapabilityManifest.from_definition(bound.definition)
        projected = project_openai_tool(manifest)
        if not projected.ok or projected.tool is None:
            reason = projected.incompatibility.reason if projected.incompatibility else "unknown"
            raise ProjectionCollision(f"cannot project {canonical}: {reason}")
        name = projected.tool.function["name"]
        if len(name) > 64:
            raise ProjectionCollision(f"projected name exceeds 64 characters: {name}")
        if name in index or name in extra_names:
            raise ProjectionCollision(f"duplicate projected name {name!r}")
        index[name] = canonical
        entries.append(
            FrozenCapabilityEntry(
                canonical_id=canonical,
                projection_name=name,
                version=bound.definition.id.version,
                effects_concurrency=bound.definition.effects.concurrency.value,
                grant=granted is None or canonical in granted,
                schema_digest=schema_digest(bound),
                definition_digest=definition_digest(bound),
                source_package_version=source_package_version(bound),
            )
        )
    payload = [_entry_payload(entry) for entry in entries]
    digest = _digest(payload)
    return FrozenExecutionCatalog(entries=tuple(entries), digest=digest, projection_index=index)


def _entry_payload(entry: FrozenCapabilityEntry) -> dict[str, Any]:
    return {
        "canonical_id": entry.canonical_id,
        "projection_name": entry.projection_name,
        "version": entry.version,
        "effects_concurrency": entry.effects_concurrency,
        "grant": entry.grant,
        "schema_digest": entry.schema_digest,
        "definition_digest": entry.definition_digest,
        "source_package_version": entry.source_package_version,
    }


def catalog_to_dict(catalog: FrozenExecutionCatalog) -> dict[str, Any]:
    return {
        "digest": catalog.digest,
        "entries": [_entry_payload(entry) for entry in catalog.entries],
    }


def catalog_from_dict(payload: dict[str, Any]) -> FrozenExecutionCatalog:
    entries = tuple(
        FrozenCapabilityEntry(
            canonical_id=str(item["canonical_id"]),
            projection_name=str(item["projection_name"]),
            version=str(item["version"]),
            effects_concurrency=str(item["effects_concurrency"]),
            grant=bool(item["grant"]),
            schema_digest=str(item["schema_digest"]),
            definition_digest=str(item["definition_digest"]),
            source_package_version=str(item["source_package_version"]),
        )
        for item in payload["entries"]
    )
    index = {entry.projection_name: entry.canonical_id for entry in entries}
    digest = str(payload["digest"])
    recomputed = _digest([_entry_payload(entry) for entry in entries])
    if digest != recomputed:
        raise CatalogMismatch("stored catalog digest does not match entries")
    return FrozenExecutionCatalog(entries=entries, digest=digest, projection_index=index)


def persist_catalog(catalog: FrozenExecutionCatalog, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, catalog_to_dict(catalog))


def load_catalog(path: Path) -> FrozenExecutionCatalog:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return catalog_from_dict(payload)


def catalog_path(session_dir: Path) -> Path:
    return Path(session_dir) / CATALOG_RELATIVE


def bind_session_catalog(
    session_dir: Path,
    live: FrozenExecutionCatalog,
) -> FrozenExecutionCatalog:
    """Load the frozen catalog for this execution, or persist `live` on first use.

    A digest mismatch is an explicit refusal. Resume never silently re-projects.
    """
    path = catalog_path(session_dir)
    if path.exists():
        frozen = load_catalog(path)
        if frozen.digest != live.digest:
            raise CatalogMismatch(
                f"frozen catalog {frozen.digest} does not match live registry {live.digest}"
            )
        return frozen
    persist_catalog(live, path)
    return live


def resolve_projected_name(catalog: FrozenExecutionCatalog, provider_name: str) -> str:
    canonical = catalog.projection_index.get(provider_name)
    if canonical is None:
        raise ContractValidationError(
            f"provider call {provider_name!r} is not in the frozen catalog"
        )
    return canonical


def entry_for_canonical(
    catalog: FrozenExecutionCatalog, canonical_id: str
) -> FrozenCapabilityEntry:
    for entry in catalog.entries:
        if entry.canonical_id == canonical_id:
            return entry
    raise ContractValidationError(f"canonical id {canonical_id!r} is not in the frozen catalog")


def openai_tools_from_registry(registry: CapabilityRegistry) -> list[dict]:
    tools: list[dict] = []
    seen: set[str] = set()
    freeze_catalog(registry)
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


def redacted_request_digest(arguments: dict[str, Any]) -> str:
    return _digest(redact_json(arguments))


openai_function_name = openai_function_name
