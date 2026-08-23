"""Merge ZeoCore capabilities and Sovereign runtime commands for one provider surface."""

from __future__ import annotations

from dataclasses import dataclass

from zeo_core.tools import CapabilityRegistry

from sovereign_agent.capabilities.catalog import (
    FrozenExecutionCatalog,
    ProjectionCollision,
    freeze_catalog,
    openai_tools_from_registry,
)
from sovereign_agent.capabilities.commands import RuntimeCommandRegistry, bind_session_commands
from sovereign_agent.capabilities.legacy import registered_tool_to_bound
from sovereign_agent.capabilities.session_fs import (
    SessionFilesystem,
    bind_session_file_capabilities,
)
from sovereign_agent.contracts import FrozenDict, RuntimeCapabilityManifest
from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolRegistry


@dataclass
class CallableSurface:
    capabilities: CapabilityRegistry
    commands: RuntimeCommandRegistry

    def project_openai(self) -> list[dict]:
        command_names = self.commands.names()
        catalog = freeze_catalog(self.capabilities, extra_names=command_names)
        tools = openai_tools_from_registry(self.capabilities)
        for command in self.commands.project_openai():
            name = command["function"]["name"]
            if name in catalog.projection_index:
                raise ProjectionCollision(f"runtime command collides with capability {name!r}")
            tools.append(command)
        return tools

    def freeze(self) -> FrozenExecutionCatalog:
        return freeze_catalog(self.capabilities, extra_names=self.commands.names())


def make_session_callable_surface(
    session: Session,
    extra_tools: ToolRegistry | None = None,
) -> CallableSurface:
    registry = CapabilityRegistry()
    command_names = bind_session_commands(session).names()
    for bound in bind_session_file_capabilities():
        registry.register(bound)
    if extra_tools is not None:
        reserved = set(command_names)
        for bound in registry.list_all():
            reserved.add(bound.definition.projection_name or bound.definition.id.name)
        for tool in extra_tools.list():
            if tool.name in reserved:
                continue
            registry.register(registered_tool_to_bound(tool))
    return CallableSurface(capabilities=registry, commands=bind_session_commands(session))


def session_execution_services(session: Session) -> dict:
    return {"session.filesystem": SessionFilesystem(session)}


def empty_runtime_manifest() -> RuntimeCapabilityManifest:
    return RuntimeCapabilityManifest(FrozenDict())
