"""Immutable provider events with strict, deterministic wire serialization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar

from sovereign_agent.contracts import (
    ContractValidationError,
    ExecutionId,
    FrozenDict,
    InvocationId,
    ProviderSessionId,
)
from sovereign_agent.contracts._core import (
    format_datetime,
    freeze_json,
    parse_datetime,
    require_object,
    require_string,
    thaw_json,
)


@dataclass(frozen=True)
class ProviderEvent:
    """Common identity and ordering envelope carried by every provider event."""

    execution_id: ExecutionId
    invocation_id: InvocationId
    sequence: int
    timestamp: datetime
    EVENT_TYPE: ClassVar[str] = "raw"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise ContractValidationError("execution_id must be ExecutionId")
        if not isinstance(self.invocation_id, InvocationId):
            raise ContractValidationError("invocation_id must be InvocationId")
        if (
            not isinstance(self.sequence, int)
            or isinstance(self.sequence, bool)
            or self.sequence < 0
        ):
            raise ContractValidationError("sequence must be a non-negative integer")
        format_datetime(self.timestamp, "timestamp")

    @property
    def event_type(self) -> str:
        return self.EVENT_TYPE

    def _payload(self) -> dict[str, Any]:
        return {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.EVENT_TYPE,
            "execution_id": str(self.execution_id),
            "invocation_id": str(self.invocation_id),
            "sequence": self.sequence,
            "timestamp": format_datetime(self.timestamp, "timestamp"),
            **self._payload(),
        }

    @classmethod
    def from_dict(cls, value: object) -> ProviderEvent:
        data = require_object(value, "provider_event")
        event_type = require_string(data.get("type"), "provider_event.type")
        event_cls = _EVENT_TYPES.get(event_type)
        if event_cls is None:
            raise ContractValidationError(f"unknown provider event type {event_type!r}")
        expected = _ENVELOPE_FIELDS | event_cls._PAYLOAD_FIELDS
        missing = expected - data.keys()
        extra = data.keys() - expected
        if missing:
            raise ContractValidationError(
                f"provider event missing fields: {', '.join(sorted(missing))}"
            )
        if extra:
            raise ContractValidationError(
                f"provider event has unknown fields: {', '.join(sorted(extra))}"
            )
        common = {
            "execution_id": ExecutionId(require_string(data["execution_id"], "execution_id")),
            "invocation_id": InvocationId(require_string(data["invocation_id"], "invocation_id")),
            "sequence": data["sequence"],
            "timestamp": parse_datetime(data["timestamp"], "timestamp"),
        }
        payload = {name: data[name] for name in event_cls._PAYLOAD_FIELDS}
        return event_cls(**common, **payload)


@dataclass(frozen=True)
class TextEvent(ProviderEvent):
    text: str
    EVENT_TYPE: ClassVar[str] = "text"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset({"text"})

    def __post_init__(self) -> None:
        super().__post_init__()
        require_string(self.text, "text", allow_empty=True)

    def _payload(self) -> dict[str, Any]:
        return {"text": self.text}


@dataclass(frozen=True)
class ToolCallEvent(ProviderEvent):
    tool_call_id: str
    name: str
    arguments: FrozenDict
    EVENT_TYPE: ClassVar[str] = "tool_call"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset({"tool_call_id", "name", "arguments"})

    def __post_init__(self) -> None:
        super().__post_init__()
        require_string(self.tool_call_id, "tool_call_id")
        require_string(self.name, "name")
        object.__setattr__(
            self, "arguments", freeze_json(require_object(self.arguments, "arguments"))
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "arguments": thaw_json(self.arguments),
        }


@dataclass(frozen=True)
class ToolResultEvent(ProviderEvent):
    tool_call_id: str
    name: str
    result: FrozenDict
    EVENT_TYPE: ClassVar[str] = "tool_result"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset({"tool_call_id", "name", "result"})

    def __post_init__(self) -> None:
        super().__post_init__()
        require_string(self.tool_call_id, "tool_call_id")
        require_string(self.name, "name")
        object.__setattr__(self, "result", freeze_json(require_object(self.result, "result")))

    def _payload(self) -> dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "result": thaw_json(self.result),
        }


@dataclass(frozen=True)
class UsageEvent(ProviderEvent):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    EVENT_TYPE: ClassVar[str] = "usage"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"input_tokens", "output_tokens", "total_tokens"}
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        for name in self._PAYLOAD_FIELDS:
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ContractValidationError(f"{name} must be a non-negative integer")
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ContractValidationError("total_tokens must equal input_tokens + output_tokens")

    def _payload(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class ProviderSessionEvent(ProviderEvent):
    provider_session_id: ProviderSessionId
    EVENT_TYPE: ClassVar[str] = "provider_session"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset({"provider_session_id"})

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.provider_session_id, str):
            object.__setattr__(
                self, "provider_session_id", ProviderSessionId(self.provider_session_id)
            )
        if not isinstance(self.provider_session_id, ProviderSessionId):
            raise ContractValidationError("provider_session_id must be ProviderSessionId")

    def _payload(self) -> dict[str, Any]:
        return {"provider_session_id": str(self.provider_session_id)}


@dataclass(frozen=True)
class StructuredResultEvent(ProviderEvent):
    result: FrozenDict
    EVENT_TYPE: ClassVar[str] = "structured_result"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset({"result"})

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "result", freeze_json(require_object(self.result, "result")))

    def _payload(self) -> dict[str, Any]:
        return {"result": thaw_json(self.result)}


@dataclass(frozen=True)
class WarningEvent(ProviderEvent):
    code: str
    message: str
    EVENT_TYPE: ClassVar[str] = "warning"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset({"code", "message"})

    def __post_init__(self) -> None:
        super().__post_init__()
        require_string(self.code, "code")
        require_string(self.message, "message")

    def _payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class RawEvent(ProviderEvent):
    provider_type: str
    payload: FrozenDict = field(default_factory=FrozenDict)
    EVENT_TYPE: ClassVar[str] = "raw"
    _PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset({"provider_type", "payload"})

    def __post_init__(self) -> None:
        super().__post_init__()
        require_string(self.provider_type, "provider_type")
        object.__setattr__(self, "payload", freeze_json(require_object(self.payload, "payload")))

    def _payload(self) -> dict[str, Any]:
        return {"provider_type": self.provider_type, "payload": thaw_json(self.payload)}


ProviderEventType = (
    TextEvent
    | ToolCallEvent
    | ToolResultEvent
    | UsageEvent
    | ProviderSessionEvent
    | StructuredResultEvent
    | WarningEvent
    | RawEvent
)

_ENVELOPE_FIELDS = frozenset({"type", "execution_id", "invocation_id", "sequence", "timestamp"})
_EVENT_TYPES: dict[str, type[ProviderEvent]] = {
    event_cls.EVENT_TYPE: event_cls
    for event_cls in (
        TextEvent,
        ToolCallEvent,
        ToolResultEvent,
        UsageEvent,
        ProviderSessionEvent,
        StructuredResultEvent,
        WarningEvent,
        RawEvent,
    )
}


def utc_now() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "ProviderEvent",
    "ProviderEventType",
    "ProviderSessionEvent",
    "RawEvent",
    "StructuredResultEvent",
    "TextEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "UsageEvent",
    "WarningEvent",
]
