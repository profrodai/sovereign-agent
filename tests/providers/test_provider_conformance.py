from __future__ import annotations

import inspect
from datetime import UTC, datetime
from pathlib import Path
from typing import get_type_hints

import pytest

from sovereign_agent._internal.llm_client import FakeLLMClient, ScriptedResponse
from sovereign_agent.config import Config
from sovereign_agent.contracts import (
    ContractValidationError,
    ExecutionId,
    FrozenDict,
    InvocationId,
)
from sovereign_agent.halves import HalfResult
from sovereign_agent.orchestrator import TaskResult, run_task
from sovereign_agent.providers import (
    AgentProvider,
    InvocationRequest,
    NativeProvider,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRegistry,
    ProviderSessionEvent,
    ProviderUnavailable,
    StructuredResultEvent,
    UsageEvent,
)


def _common(sequence: int = 0) -> dict:
    return {
        "execution_id": ExecutionId("exec-1"),
        "invocation_id": InvocationId("invoke-1"),
        "sequence": sequence,
        "timestamp": datetime(2026, 8, 22, tzinfo=UTC),
    }


def test_event_round_trip_is_strict_and_immutable() -> None:
    event = UsageEvent(**_common(), input_tokens=2, output_tokens=3, total_tokens=5)
    assert ProviderEvent.from_dict(event.to_dict()) == event
    with pytest.raises(ContractValidationError, match="unknown fields"):
        ProviderEvent.from_dict({**event.to_dict(), "surprise": True})
    with pytest.raises(ContractValidationError, match="total_tokens"):
        UsageEvent(**_common(), input_tokens=2, output_tokens=3, total_tokens=4)
    with pytest.raises(AttributeError):
        event.sequence = 2  # type: ignore[misc]


def test_session_and_structured_events_round_trip() -> None:
    session = ProviderSessionEvent(**_common(), provider_session_id="provider-session")
    structured = StructuredResultEvent(**_common(1), result=FrozenDict((("answer", "done"),)))
    assert ProviderEvent.from_dict(session.to_dict()) == session
    assert ProviderEvent.from_dict(structured.to_dict()) == structured


def test_capabilities_are_contract_compatible() -> None:
    capabilities = ProviderCapabilities(tools=True, structured_result=True)
    assert ProviderCapabilities.from_manifest(capabilities.to_manifest()) == capabilities


class _FakeLoop:
    async def run(self, session, input_payload):  # type: ignore[no-untyped-def]
        return HalfResult(
            success=True,
            output={"final_answer": "done", "executor_results": []},
            summary="complete",
            next_action="complete",
        )


@pytest.mark.asyncio
async def test_native_provider_ordering_and_observer_containment(fresh_session) -> None:
    provider = NativeProvider(loop_half=_FakeLoop())  # type: ignore[arg-type]
    observed: list[int] = []
    activity: list[int] = []

    def broken(event):  # type: ignore[no-untyped-def]
        observed.append(event.sequence)
        raise RuntimeError("observer broke")

    request = InvocationRequest(
        execution_id=ExecutionId("exec-1"),
        invocation_id=InvocationId("invoke-1"),
        task="test",
        session=fresh_session,
    )
    result = await provider.invoke(
        request,
        observers=[broken],
        activity_callbacks=[lambda event: activity.append(event.sequence)],
    )
    assert [event.sequence for event in result.events] == list(range(len(result.events)))
    assert [event.event_type for event in result.events] == [
        "text",
        "structured_result",
    ]
    assert observed == activity == [0, 1]
    assert len(provider.last_observer_failures) == 2


@pytest.mark.asyncio
async def test_native_provider_refuses_external_resume(fresh_session) -> None:
    provider = NativeProvider(loop_half=_FakeLoop())  # type: ignore[arg-type]
    request = InvocationRequest(
        execution_id=ExecutionId("exec-1"),
        invocation_id=InvocationId("invoke-1"),
        task="test",
        session=fresh_session,
        provider_session_id="external-session",
    )
    with pytest.raises(ProviderUnavailable, match="no external provider session"):
        await provider.invoke(request)


def test_provider_registry_uses_plugin_contract() -> None:
    provider = NativeProvider(loop_half=_FakeLoop())  # type: ignore[arg-type]
    registry = ProviderRegistry()
    registry.register(provider)
    assert registry.get("native") is provider
    assert isinstance(provider, AgentProvider)


def test_run_task_signature_and_result_are_backward_compatible(tmp_path: Path) -> None:
    signature = inspect.signature(run_task)
    assert list(signature.parameters) == [
        "task",
        "config",
        "scenario",
        "user_id",
        "llm_client",
        "extra_tools",
        "extra_capabilities",
    ]
    assert signature.parameters["task"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in list(signature.parameters.values())[1:]
    )
    assert signature.parameters["scenario"].default == "default"
    assert get_type_hints(run_task)["return"] is TaskResult
    client = FakeLLMClient(
        [
            ScriptedResponse(
                content=(
                    '[{"id":"sg_1","description":"answer","success_criterion":"answered",'
                    '"estimated_tool_calls":1}]'
                )
            ),
            ScriptedResponse(content="native provider answer"),
        ]
    )
    result = run_task(
        "answer",
        config=Config(sessions_dir=tmp_path / "sessions"),
        scenario="compat",
        user_id="user-1",
        llm_client=client,
    )
    assert isinstance(result, TaskResult)
    assert result.success is True
    assert result.output["final_answer"] == "native provider answer"
    assert (result.session_dir / "SESSION.md").exists()
