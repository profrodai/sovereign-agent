"""Deterministic helpers shared by fixture-driven CLI event parsers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from sovereign_agent.contracts import FrozenDict, ProviderSessionId
from sovereign_agent.contracts._core import freeze_json

from .events import (
    ProviderEventType,
    ProviderSessionEvent,
    RawEvent,
    StructuredResultEvent,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
    UsageEvent,
    WarningEvent,
    utc_now,
)
from .models import InvocationRequest


class EventBuilder:
    """Append normalized events with contiguous sequence numbers."""

    def __init__(self, request: InvocationRequest) -> None:
        self.request = request
        self.events: list[ProviderEventType] = []
        self._sessions: set[str] = set()
        self._tool_names: dict[str, str] = {}

    def _common(self) -> dict[str, Any]:
        return {
            "execution_id": self.request.execution_id,
            "invocation_id": self.request.invocation_id,
            "sequence": len(self.events),
            "timestamp": utc_now(),
        }

    def text(self, text: str) -> None:
        self.events.append(TextEvent(**self._common(), text=text))

    @property
    def has_text(self) -> bool:
        return any(isinstance(event, TextEvent) for event in self.events)

    def tool_call(self, call_id: str, name: str, arguments: Mapping[str, Any]) -> None:
        self._tool_names[call_id] = name
        self.events.append(
            ToolCallEvent(
                **self._common(),
                tool_call_id=call_id,
                name=name,
                arguments=freeze_json(dict(arguments)),
            )
        )

    def tool_name(self, call_id: str) -> str | None:
        return self._tool_names.get(call_id)

    def tool_result(self, call_id: str, name: str, result: Mapping[str, Any]) -> None:
        self.events.append(
            ToolResultEvent(
                **self._common(),
                tool_call_id=call_id,
                name=name,
                result=freeze_json(dict(result)),
            )
        )

    def usage(self, input_tokens: object, output_tokens: object) -> bool:
        if not _nonnegative_int(input_tokens) or not _nonnegative_int(output_tokens):
            self.warning("invalid_usage", "usage token counts must be non-negative integers")
            return False
        assert isinstance(input_tokens, int)
        assert isinstance(output_tokens, int)
        input_count = input_tokens
        output_count = output_tokens
        self.events.append(
            UsageEvent(
                **self._common(),
                input_tokens=input_count,
                output_tokens=output_count,
                total_tokens=input_count + output_count,
            )
        )
        return True

    def session(self, value: object) -> bool:
        if not isinstance(value, str):
            self.warning("invalid_provider_session", "provider session ID must be a string")
            return False
        try:
            session_id = ProviderSessionId(value)
        except (TypeError, ValueError) as exc:
            self.warning("invalid_provider_session", str(exc))
            return False
        if value in self._sessions:
            return True
        self._sessions.add(value)
        self.events.append(ProviderSessionEvent(**self._common(), provider_session_id=session_id))
        return True

    def structured(self, result: Mapping[str, Any]) -> None:
        self.events.append(
            StructuredResultEvent(**self._common(), result=freeze_json(dict(result)))
        )

    def warning(self, code: str, message: str) -> None:
        self.events.append(WarningEvent(**self._common(), code=code, message=message))

    def raw(self, provider_type: str, payload: Mapping[str, Any]) -> None:
        self.events.append(
            RawEvent(
                **self._common(),
                provider_type=provider_type,
                payload=FrozenDict(tuple(payload.items())),
            )
        )


def parse_json_lines(stdout: str, builder: EventBuilder) -> list[dict[str, Any]]:
    """Parse JSONL with a stable recovery policy.

    Blank lines are ignored. Every malformed, truncated, or non-object line
    produces one ``malformed_provider_line`` warning and parsing continues.
    No evidence is inferred from a failed line.
    """

    objects: list[dict[str, Any]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            builder.warning(
                "malformed_provider_line",
                f"line {line_number}: JSON decode failed at column {exc.colno}",
            )
            continue
        if not isinstance(value, dict):
            builder.warning(
                "malformed_provider_line",
                f"line {line_number}: expected a JSON object",
            )
            continue
        objects.append(value)
    return objects


def object_value(value: object) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


__all__ = ["EventBuilder", "object_value", "parse_json_lines"]
