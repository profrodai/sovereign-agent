"""Sovereign adapter around ZeoCore capabilities. Does not redefine capability schema."""

from sovereign_agent.capabilities.approval import ApprovalDisposition, ApprovalPolicy
from sovereign_agent.capabilities.catalog import (
    CatalogMismatch,
    FrozenExecutionCatalog,
    ProjectedCapability,
    freeze_catalog,
)
from sovereign_agent.capabilities.commands import RuntimeCommand, RuntimeCommandRegistry
from sovereign_agent.capabilities.context import CapabilityContextFactory, ExecutionScope
from sovereign_agent.capabilities.executor import CapabilityExecutor, RuntimeInvocationResult
from sovereign_agent.capabilities.session_fs import bind_session_file_capabilities
from sovereign_agent.capabilities.surface import CallableSurface, make_session_callable_surface

__all__ = [
    "ApprovalDisposition",
    "ApprovalPolicy",
    "CatalogMismatch",
    "CallableSurface",
    "CapabilityContextFactory",
    "CapabilityExecutor",
    "ExecutionScope",
    "FrozenExecutionCatalog",
    "ProjectedCapability",
    "RuntimeCommand",
    "RuntimeCommandRegistry",
    "RuntimeInvocationResult",
    "bind_session_file_capabilities",
    "freeze_catalog",
    "make_session_callable_surface",
]
