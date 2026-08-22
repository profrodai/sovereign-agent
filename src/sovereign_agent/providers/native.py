"""Native provider adapter for the existing planner/executor LoopHalf."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from sovereign_agent.contracts import FrozenDict
from sovereign_agent.contracts._core import thaw_json
from sovereign_agent.executor import DefaultExecutor
from sovereign_agent.halves.loop import LoopHalf
from sovereign_agent.planner import DefaultPlanner

from .cli import ProviderUnavailable
from .events import (
    ProviderEventType,
    StructuredResultEvent,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
    WarningEvent,
    utc_now,
)
from .models import InvocationRequest, InvocationResult, ProviderCapabilities
from .observers import EventFanout, ObserverFailure
from .protocol import EventCallback


class NativeProvider:
    """Expose Sovereign Agent's v0.2 loop through the provider contract."""

    kind: ClassVar[str] = "provider"
    capabilities = ProviderCapabilities(
        tools=True,
        structured_result=True,
    )

    def __init__(
        self,
        *,
        loop_half: LoopHalf | None = None,
        planner: DefaultPlanner | None = None,
        executor: DefaultExecutor | None = None,
        name: str = "native",
    ) -> None:
        if loop_half is None:
            if planner is None or executor is None:
                raise TypeError("provide loop_half or both planner and executor")
            loop_half = LoopHalf(planner=planner, executor=executor)
        self.name = name
        self.loop_half = loop_half
        self.last_observer_failures: tuple[ObserverFailure, ...] = ()

    async def invoke(
        self,
        request: InvocationRequest,
        *,
        observers: Sequence[EventCallback] = (),
        activity_callbacks: Sequence[EventCallback] = (),
    ) -> InvocationResult:
        if request.provider_session_id is not None:
            raise ProviderUnavailable("native provider has no external provider session to resume")
        fanout = EventFanout(observers, activity_callbacks)
        events: list[ProviderEventType] = []

        async def emit(event: ProviderEventType) -> None:
            events.append(event)
            await fanout.emit(event)

        context = thaw_json(request.context)
        assert isinstance(context, dict)
        result = await self.loop_half.run(
            request.session,
            {"task": request.task, "context": context},
        )

        for index, call in enumerate(_tool_calls(result.output)):
            call_id = f"native-tool-{index}"
            name = str(call.get("name") or "unknown")
            arguments = call.get("arguments")
            if not isinstance(arguments, dict):
                arguments = {}
            await emit(
                ToolCallEvent(
                    execution_id=request.execution_id,
                    invocation_id=request.invocation_id,
                    sequence=len(events),
                    timestamp=utc_now(),
                    tool_call_id=call_id,
                    name=name,
                    arguments=FrozenDict(tuple(arguments.items())),
                )
            )
            await emit(
                ToolResultEvent(
                    execution_id=request.execution_id,
                    invocation_id=request.invocation_id,
                    sequence=len(events),
                    timestamp=utc_now(),
                    tool_call_id=call_id,
                    name=name,
                    result=FrozenDict(
                        (
                            ("success", bool(call.get("success", True))),
                            ("summary", str(call.get("summary") or "")),
                        )
                    ),
                )
            )

        text = str(result.output.get("final_answer") or result.summary)
        await emit(
            TextEvent(
                execution_id=request.execution_id,
                invocation_id=request.invocation_id,
                sequence=len(events),
                timestamp=utc_now(),
                text=text,
            )
        )
        await emit(
            StructuredResultEvent(
                execution_id=request.execution_id,
                invocation_id=request.invocation_id,
                sequence=len(events),
                timestamp=utc_now(),
                result=FrozenDict(tuple(result.output.items())),
            )
        )
        if not result.success:
            await emit(
                WarningEvent(
                    execution_id=request.execution_id,
                    invocation_id=request.invocation_id,
                    sequence=len(events),
                    timestamp=utc_now(),
                    code="native_invocation_failed",
                    message=result.summary,
                )
            )

        self.last_observer_failures = fanout.failures
        return InvocationResult(
            success=result.success,
            output=FrozenDict(tuple(result.output.items())),
            summary=result.summary,
            next_action=result.next_action,
            events=tuple(events),
        )


def _tool_calls(output: dict) -> list[dict]:
    calls: list[dict] = []
    executor_results = output.get("executor_results") or []
    if not isinstance(executor_results, list):
        return calls
    for executor_result in executor_results:
        if not isinstance(executor_result, dict):
            continue
        raw_calls = executor_result.get("tool_calls_made") or []
        if isinstance(raw_calls, list):
            calls.extend(call for call in raw_calls if isinstance(call, dict))
    return calls


__all__ = ["NativeProvider"]
