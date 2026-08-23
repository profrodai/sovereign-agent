"""Runtime commands: meaningful only inside a Sovereign session."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent.errors import ToolError
from sovereign_agent.session.directory import Session


@dataclass(frozen=True)
class RuntimeCommand:
    name: str
    description: str
    parameters_schema: dict[str, Any]
    handler: Callable[[dict[str, Any], Session], dict[str, Any]]
    exclusive: bool = True


class RuntimeCommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, RuntimeCommand] = {}

    def register(self, command: RuntimeCommand) -> None:
        if command.name in self._commands:
            raise ValueError(f"runtime command {command.name!r} is already registered")
        self._commands[command.name] = command

    def get(self, name: str) -> RuntimeCommand:
        if name not in self._commands:
            raise ToolError(
                code="SA_TOOL_NOT_FOUND",
                message=f"runtime command {name!r} is not registered",
                context={"available": sorted(self._commands)},
            )
        return self._commands[name]

    def list_all(self) -> list[RuntimeCommand]:
        return [self._commands[name] for name in sorted(self._commands)]

    def names(self) -> frozenset[str]:
        return frozenset(self._commands)

    def project_openai(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": command.name,
                    "description": command.description,
                    "parameters": command.parameters_schema,
                },
            }
            for command in self.list_all()
        ]


def bind_session_commands(session: Session) -> RuntimeCommandRegistry:
    registry = RuntimeCommandRegistry()

    def handoff_to_structured(arguments: dict[str, Any], bound: Session) -> dict[str, Any]:
        payload = {
            "version": 1,
            "from_half": "loop",
            "to_half": "structured",
            "written_at": datetime.now(tz=UTC).isoformat(),
            "session_id": bound.session_id,
            "reason": arguments["reason"],
            "context": arguments["context"],
            "data": arguments["data"],
            "return_instructions": arguments["data"].get("return_instructions", ""),
        }
        atomic_write_json(bound.ipc_dir / "handoff_to_structured.json", payload)
        return {"handoff_written": True, "exit_reason": "handoff"}

    def complete_task(arguments: dict[str, Any], bound: Session) -> dict[str, Any]:
        payload = {"session_id": bound.session_id, "result": arguments["result"]}
        atomic_write_json(bound.ipc_dir / "session_complete.json", payload)
        return {"session_complete": True}

    registry.register(
        RuntimeCommand(
            name="handoff_to_structured",
            description="Hand off control to the structured half for rule-following work.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "context": {"type": "string"},
                    "data": {"type": "object"},
                },
                "required": ["reason", "context", "data"],
            },
            handler=handoff_to_structured,
        )
    )

    def abort_execution(arguments: dict[str, Any], bound: Session) -> dict[str, Any]:
        payload = {
            "session_id": bound.session_id,
            "reason": arguments.get("reason", "operator abort"),
            "aborted_at": datetime.now(tz=UTC).isoformat(),
        }
        atomic_write_json(bound.ipc_dir / "execution_aborted.json", payload)
        return {"aborted": True}

    def session_status(arguments: dict[str, Any], bound: Session) -> dict[str, Any]:
        del arguments
        return {
            "session_id": bound.session_id,
            "state": bound.state.state,
            "directory": str(bound.directory),
        }

    registry.register(
        RuntimeCommand(
            name="abort_execution",
            description="Abort the current session execution without invoking a capability.",
            parameters_schema={
                "type": "object",
                "properties": {"reason": {"type": "string"}},
            },
            handler=abort_execution,
        )
    )
    registry.register(
        RuntimeCommand(
            name="session_status",
            description="Report current session identity and lifecycle state.",
            parameters_schema={"type": "object", "properties": {}},
            handler=session_status,
        )
    )
    registry.register(
        RuntimeCommand(
            name="complete_task",
            description="Mark the session as complete with the given result payload.",
            parameters_schema={
                "type": "object",
                "properties": {"result": {"type": "object"}},
                "required": ["result"],
            },
            handler=complete_task,
        )
    )
    return registry
