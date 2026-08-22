"""Native OpenAI Codex CLI provider (no Sandcastle dependency)."""

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


class CodexCliProvider(CliProvider):
    """Execute ``codex exec --json`` and normalize its documented JSONL."""

    credential_names = ("OPENAI_API_KEY",)
    environment_names = ("CODEX_HOME",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            executable=str(kwargs.pop("executable", "codex")),
            name=str(kwargs.pop("name", "codex")),
            **kwargs,
        )

    def version_spec(self) -> InvocationSpec:
        return self.spec((self.executable, "--version"))

    def help_spec(self) -> InvocationSpec:
        return self.spec((self.executable, "exec", "--help"))

    def capabilities_from_probe(
        self, version: ExecResult, help_result: ExecResult
    ) -> ProviderCapabilities:
        help_text = f"{help_result.stdout}\n{help_result.stderr}".lower()
        available = version.succeeded and help_result.succeeded
        json_mode = available and "--json" in help_text
        return ProviderCapabilities(
            available=available,
            streaming=json_mode,
            tools=json_mode,
            usage=json_mode,
            provider_session=json_mode,
            structured_result=json_mode and "--output-schema" in help_text,
            resume=json_mode and "resume" in help_text,
            evidence_level=EvidenceLevel.PROBED,
        )

    def invocation_spec(self, request: InvocationRequest) -> InvocationSpec:
        context = thaw_json(request.context)
        assert isinstance(context, dict)
        cwd = self.working_directory(request)
        schema_path = context.get("output_schema_path")
        if context.get("require_structured_result") and not isinstance(schema_path, str):
            raise ProviderUnavailable("codex structured results require context.output_schema_path")
        command: tuple[str, ...]
        if request.provider_session_id is None:
            parts = [
                self.executable,
                "exec",
                "--json",
                "--skip-git-repo-check",
            ]
            if isinstance(schema_path, str):
                parts.extend(("--output-schema", schema_path))
            parts.append(request.task)
            command = tuple(parts)
        else:
            parts = [
                self.executable,
                "exec",
                "resume",
                "--json",
            ]
            if isinstance(schema_path, str):
                parts.extend(("--output-schema", schema_path))
            parts.extend((str(request.provider_session_id), request.task))
            command = tuple(parts)
        return self.spec(command, cwd=cwd)

    def parse_output(self, stdout: str, request: InvocationRequest) -> list[ProviderEventType]:
        builder = EventBuilder(request)
        for event in parse_json_lines(stdout, builder):
            event_type = event.get("type")
            if event_type == "thread.started":
                builder.session(event.get("thread_id"))
            elif event_type == "item.completed":
                self._completed_item(event, builder)
            elif event_type == "item.started":
                item = object_value(event.get("item"))
                if item is None:
                    builder.warning("invalid_item", "item.started requires an object item")
                elif item.get("type") not in {"command_execution", "mcp_tool_call"}:
                    builder.raw(str(event_type), event)
            elif event_type == "turn.completed":
                usage = object_value(event.get("usage"))
                if usage is None:
                    builder.warning("missing_usage", "turn.completed did not contain usage")
                else:
                    builder.usage(usage.get("input_tokens"), usage.get("output_tokens"))
            elif event_type in {"turn.started"}:
                builder.raw(str(event_type), event)
            elif event_type in {"error", "turn.failed"}:
                message = event.get("message") or event.get("error") or "Codex reported an error"
                builder.warning("provider_error", str(message))
            elif isinstance(event_type, str):
                builder.raw(event_type, event)
            else:
                builder.warning("missing_event_type", "Codex event requires a string type")
        return builder.events

    def _completed_item(self, event: dict[str, Any], builder: EventBuilder) -> None:
        item = object_value(event.get("item"))
        if item is None:
            builder.warning("invalid_item", "item.completed requires an object item")
            return
        item_type = item.get("type")
        if item_type == "agent_message":
            text = item.get("text")
            if isinstance(text, str):
                builder.text(text)
                context = thaw_json(builder.request.context)
                assert isinstance(context, dict)
                if context.get("require_structured_result"):
                    try:
                        structured = json.loads(text)
                    except json.JSONDecodeError:
                        structured = None
                    if isinstance(structured, dict):
                        builder.structured(structured)
                    else:
                        builder.warning(
                            "invalid_structured_result",
                            "schema-constrained Codex answer must be a JSON object",
                        )
            else:
                builder.warning("invalid_text", "agent_message text must be a string")
            return
        if item_type == "command_execution":
            call_id = item.get("id")
            command = item.get("command")
            if not isinstance(call_id, str) or not isinstance(command, str):
                builder.warning(
                    "invalid_tool_call", "command_execution requires string id and command"
                )
                return
            builder.tool_call(call_id, "shell", {"command": command})
            builder.tool_result(
                call_id,
                "shell",
                {
                    "output": item.get("aggregated_output", ""),
                    "exit_code": item.get("exit_code"),
                    "status": item.get("status"),
                },
            )
            return
        if item_type == "mcp_tool_call":
            call_id = item.get("id")
            name = item.get("tool")
            arguments = object_value(item.get("arguments"))
            if not isinstance(call_id, str) or not isinstance(name, str) or arguments is None:
                builder.warning(
                    "invalid_tool_call",
                    "mcp_tool_call requires string id/tool and object arguments",
                )
                return
            builder.tool_call(call_id, name, arguments)
            result = object_value(item.get("result"))
            if result is not None:
                builder.tool_result(call_id, name, result)
            elif item.get("error") is not None:
                builder.tool_result(call_id, name, {"error": item["error"]})
            return
        if item_type == "structured_output":
            value = object_value(item.get("value"))
            if value is None:
                builder.warning("invalid_structured_result", "structured output must be an object")
            else:
                builder.structured(value)
            return
        builder.raw("item.completed", event)


__all__ = ["CodexCliProvider"]
