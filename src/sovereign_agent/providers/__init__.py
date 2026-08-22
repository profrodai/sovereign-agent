"""Agent provider contracts, normalized events, and native implementation."""

from .events import (
    ProviderEvent,
    ProviderEventType,
    ProviderSessionEvent,
    RawEvent,
    StructuredResultEvent,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
    UsageEvent,
    WarningEvent,
)
from .models import InvocationRequest, InvocationResult, ProviderCapabilities
from .native import NativeProvider
from .observers import EventFanout, ObserverFailure
from .protocol import AgentProvider, EventCallback
from .registry import PROVIDER_REGISTRY, ProviderRegistry

__all__ = [
    "PROVIDER_REGISTRY",
    "AgentProvider",
    "EventCallback",
    "EventFanout",
    "InvocationRequest",
    "InvocationResult",
    "NativeProvider",
    "ObserverFailure",
    "ProviderCapabilities",
    "ProviderEvent",
    "ProviderEventType",
    "ProviderRegistry",
    "ProviderSessionEvent",
    "RawEvent",
    "StructuredResultEvent",
    "TextEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "UsageEvent",
    "WarningEvent",
]
