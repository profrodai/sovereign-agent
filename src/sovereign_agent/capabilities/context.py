"""Scoped ToolContext construction. Opaque correlation ids only."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zeo_core.tools import (
    BoundCapability,
    NeverCancelled,
    RecordingArtifactSink,
    SystemClock,
    ToolContext,
)

from sovereign_agent.contracts import RuntimeCapabilityManifest
from sovereign_agent.session.directory import Session


@dataclass
class ExecutionScope:
    """Runtime-owned execution handle passed to the capability adapter."""

    id: str
    work_dir: Path
    output_dir: Path
    runtime_manifest: RuntimeCapabilityManifest
    allowed_capabilities: frozenset[str] = field(default_factory=frozenset)
    granted_capabilities: frozenset[str] = field(default_factory=frozenset)
    preapproved_capabilities: frozenset[str] = field(default_factory=frozenset)
    denied_capabilities: frozenset[str] = field(default_factory=frozenset)
    require_approval_for_mutations: bool = False
    services: dict[str, Any] = field(default_factory=dict)
    logger: Any = None
    fs: Any = None
    session: Session | None = None
    catalog_digest: str | None = None
    seat: str | None = None
    repository: str | None = None
    channel: str | None = None
    invoke_timeout: float = 30.0
    complete_timeout: float = 5.0
    teardown_timeout: float = 5.0


class CapabilityContextFactory:
    def build(
        self,
        execution: ExecutionScope,
        capability: BoundCapability,
        cancellation: Any | None = None,
    ) -> ToolContext:
        services: dict[str, Any] = {
            "clock": SystemClock(),
            "cancellation": cancellation or NeverCancelled(),
            "artifacts": RecordingArtifactSink(),
        }
        services.update(execution.services)
        return ToolContext(
            run_id=str(execution.id),
            tool_name=capability.definition.id.name,
            tool_version=capability.definition.id.version,
            logger=execution.logger or logging.getLogger("sovereign_agent.capabilities"),
            fs=execution.fs if execution.fs is not None else object(),
            work_dir=str(execution.work_dir),
            output_dir=str(execution.output_dir),
            services=services,
            metadata={
                "execution_id": str(execution.id),
                "capability_id": capability.definition.id.canonical(),
            },
        )
