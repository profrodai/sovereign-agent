"""Native Anthropic Claude Code CLI provider (no Sandcastle dependency)."""

from __future__ import annotations

import json
from typing import Any

from sovereign_agent.contracts import EvidenceLevel
from sovereign_agent.contracts._core import thaw_json
from sovereign_agent.orchestrator.lifecycle import ExecResult, InvocationSpec

from ._parse import EventBuilder, object_value, parse_json_lines
from .cli import CliProvider, ProviderUnavailable
from .events import ProviderEventType
from .models import InvocationRequest, ProviderCapabilities


class ClaudeCodeProvider(CliProvider):
    """Execute Claude Code print mode and normalize documented stream-json."""

    credential_names = ("ANTHROPIC_API_KEY",)
    environment_names = ("CLAUDE_CONFIG_DIR",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            executable=str(kwargs.pop("executable", "claude")),
            name=str(kwargs.pop("name", "claude")),
            **kwargs,
        )

    def version_spec(self) -> InvocationSpec:
        return self.spec((self.executable, "--version"))

    def help_spec(self) -> InvocationSpec:
        return self.spec((self.executable, "--help"))

    def capabilities_from_probe(
        self, version: ExecResult, help_result: ExecResult
    ) -> ProviderCapabilities:
        help_text = f"{help_result.stdout}\n{help_result.stderr}".lower()
        available = version.succeeded and help_result.succeeded
        stream_json = available and "--output-format" in help_text and "stream-json" in help_text
        return ProviderCapabilities(
            available=available,
            streaming=stream_json,
            tools=stream_json,
            usage=stream_json,
            provider_session=stream_json,
            structured_result=stream_json and "--json-schema" in help_text,
            resume=stream_json and "--resume" in help_text,
            evidence_level=EvidenceLevel.PROBED,
        )

    def invocation_spec(self, request: InvocationRequest) -> InvocationSpec:
        context = thaw_json(request.context)
        assert isinstance(context, dict)
        cwd = self.working_directory(request)
        schema = object_value(context.get("json_schema"))
        if context.get("require_structured_result") and schema is None:
            raise ProviderUnavailable("claude structured results require context.json_schema")
        command = [
            self.executable,
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        if request.provider_session_id is not None:
            command.extend(("--resume", str(request.provider_session_id)))
        if schema is not None:
            command.extend(("--json-schema", json.dumps(schema, sort_keys=True)))
        command.append(request.task)
        return self.spec(command, cwd=cwd)

    def parse_output(self, stdout: str, request: InvocationRequest) -> list[ProviderEventType]:
        builder = EventBuilder(request)
        for event in parse_json_lines(stdout, builder):
            event_type = event.get("type")
            if event_type == "system":
                if event.get("subtype") == "init":
                    builder.session(event.get("session_id"))
                else:
                    builder.raw("system", event)
            elif event_type == "assistant":
                self._message(event, builder, assistant=True)
            elif event_type == "user":
                self._message(event, builder, assistant=False)
            elif event_type == "result":
                self._result(event, builder)
            elif event_type in {"error", "warning"}:
                builder.warning(
                    "provider_error" if event_type == "error" else "provider_warning",
                    str(event.get("message") or event.get("error") or event_type),
                )
            elif isinstance(event_type, str):
                builder.raw(event_type, event)
            else:
                builder.warning("missing_event_type", "Claude event requires a string type")
        return builder.events

    def _message(self, event: dict[str, Any], builder: EventBuilder, *, assistant: bool) -> None:
        message = object_value(event.get("message"))
        if message is None:
            builder.warning("invalid_message", "message event requires an object message")
            return
        content = message.get("content")
        if not isinstance(content, list):
            builder.warning("invalid_message", "message content must be a list")
            return
        for block in content:
            if not isinstance(block, dict):
                builder.warning("invalid_content_block", "content block must be an object")
                continue
            block_type = block.get("type")
            if assistant and block_type == "text":
                text = block.get("text")
                if isinstance(text, str):
                    builder.text(text)
                else:
                    builder.warning("invalid_text", "text block requires string text")
            elif assistant and block_type == "tool_use":
                call_id = block.get("id")
                name = block.get("name")
                arguments = object_value(block.get("input"))
                if isinstance(call_id, str) and isinstance(name, str) and arguments is not None:
                    builder.tool_call(call_id, name, arguments)
                else:
                    builder.warning(
                        "invalid_tool_call",
                        "tool_use requires string id/name and object input",
                    )
            elif not assistant and block_type == "tool_result":
                call_id = block.get("tool_use_id")
                if not isinstance(call_id, str):
                    builder.warning(
                        "invalid_tool_result", "tool_result requires string tool_use_id"
                    )
                    continue
                content_value = block.get("content")
                name_value = block.get("name")
                name = name_value if isinstance(name_value, str) else builder.tool_name(call_id)
                if name is None:
                    builder.warning(
                        "unmatched_tool_result",
                        f"tool_result {call_id!r} has no observed tool call",
                    )
                    builder.raw("content.tool_result", block)
                    continue
                result = (
                    content_value
                    if isinstance(content_value, dict)
                    else {
                        "content": content_value,
                        "is_error": bool(block.get("is_error", False)),
                    }
                )
                builder.tool_result(call_id, name, result)
            else:
                builder.raw(f"content.{block_type or 'unknown'}", block)
        usage = object_value(message.get("usage"))
        if usage is not None:
            builder.usage(usage.get("input_tokens"), usage.get("output_tokens"))

    def _result(self, event: dict[str, Any], builder: EventBuilder) -> None:
        if "session_id" in event:
            builder.session(event.get("session_id"))
        result_text = event.get("result")
        if isinstance(result_text, str) and not builder.has_text:
            builder.text(result_text)
        structured = object_value(event.get("structured_output"))
        if structured is not None:
            builder.structured(structured)
        usage = object_value(event.get("usage"))
        if usage is not None:
            builder.usage(usage.get("input_tokens"), usage.get("output_tokens"))
        if event.get("is_error"):
            builder.warning(
                "provider_error",
                str(event.get("result") or event.get("error") or "Claude reported an error"),
            )
        elif not structured and not usage and "session_id" not in event:
            builder.raw("result", event)


__all__ = ["ClaudeCodeProvider"]
