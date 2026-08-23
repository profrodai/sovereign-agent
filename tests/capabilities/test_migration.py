"""Capability executor, catalog, builtins, policy, evidence, and cancellation."""

from __future__ import annotations

import asyncio

import pytest
from pydantic import BaseModel
from zeo_core.contracts import (
    CapabilityExample,
    CapabilityResult,
    EffectKind,
)
from zeo_core.tools import (
    BoundCapability,
    CapabilityRegistry,
    ToolContext,
    bound_capability_of,
    capability,
)

from sovereign_agent._internal.llm_client import FakeLLMClient, ScriptedResponse, ToolCall
from sovereign_agent.capabilities.admission import AdmissionRefused, admit_capability
from sovereign_agent.capabilities.approval import ApprovalDisposition, ApprovalPolicy
from sovereign_agent.capabilities.catalog import ProjectionCollision, freeze_catalog
from sovereign_agent.capabilities.context import ExecutionScope
from sovereign_agent.capabilities.executor import CapabilityExecutor
from sovereign_agent.capabilities.invoke import invoke_cancellable
from sovereign_agent.capabilities.legacy import registered_tool_to_bound
from sovereign_agent.capabilities.surface import (
    empty_runtime_manifest,
    make_session_callable_surface,
    session_execution_services,
)
from sovereign_agent.contracts import (
    FrozenDict,
    RuntimeCapabilityAssertion,
    RuntimeCapabilityManifest,
)
from sovereign_agent.contracts.capabilities import EvidenceLevel
from sovereign_agent.executor import PARALLELISM_POLICY_ALWAYS, DefaultExecutor
from sovereign_agent.planner import Subgoal
from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolRegistry, ToolResult, _RegisteredTool


def _scope(session: Session, **kwargs: object) -> ExecutionScope:
    return ExecutionScope(
        id=session.session_id,
        work_dir=session.workspace_dir,
        output_dir=session.directory,
        runtime_manifest=empty_runtime_manifest(),
        services=session_execution_services(session),
        **kwargs,  # type: ignore[arg-type]
    )


def _sg() -> Subgoal:
    return Subgoal(
        id="sg_1",
        description="files",
        success_criterion="done",
        estimated_tool_calls=1,
        assigned_half="loop",
    )


@pytest.mark.asyncio
async def test_session_file_capabilities_round_trip(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    catalog = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    executor = CapabilityExecutor(surface.capabilities, catalog=catalog)
    write = await executor.invoke(
        execution=_scope(fresh_session),
        provider_call=ToolCall(
            id="1", name="write_file", arguments={"path": "a.md", "content": "hi"}
        ),
    )
    assert write.provider_response["success"] is True
    assert write.record is not None
    read = await executor.invoke(
        execution=_scope(fresh_session),
        provider_call=ToolCall(id="2", name="read_file", arguments={"path": "a.md"}),
    )
    assert read.provider_response["output"]["content"] == "hi"
    listed = await executor.invoke(
        execution=_scope(fresh_session),
        provider_call=ToolCall(id="3", name="list_files", arguments={"path": "."}),
    )
    names = [item["name"] for item in listed.provider_response["output"]["entries"]]
    assert "a.md" in names


@pytest.mark.asyncio
async def test_runtime_commands_complete_and_handoff(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    client = FakeLLMClient(
        [
            ScriptedResponse(
                tool_calls=[
                    ToolCall(id="c", name="complete_task", arguments={"result": {"ok": True}}),
                ]
            ),
            ScriptedResponse(content="done"),
        ]
    )
    executor = DefaultExecutor(
        model="fake",
        client=client,
        tools=ToolRegistry(),
        callable_surface=surface,
    )
    result = await executor.execute(_sg(), fresh_session, max_turns=3)
    assert result.success
    assert (fresh_session.ipc_dir / "session_complete.json").exists()


@pytest.mark.asyncio
async def test_projection_rejects_colliding_names() -> None:
    surface_caps = bind_two_same_projection()
    with pytest.raises(ProjectionCollision):
        freeze_catalog(surface_caps)


def bind_two_same_projection() -> CapabilityRegistry:
    registry = CapabilityRegistry()

    @capability(
        id="sovereign.test.one@1.0.0",
        description="one",
        effects={EffectKind.READ},
        projection_name="shared_name",
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    def one(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        return CapabilityResult.ok(data=EchoResp(ok=True), msg="ok")

    @capability(
        id="sovereign.test.two@1.0.0",
        description="two",
        effects={EffectKind.READ},
        projection_name="shared_name",
        examples=(CapabilityExample(request={"x": 2}, response={"ok": True}),),
    )
    def two(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        return CapabilityResult.ok(data=EchoResp(ok=True), msg="ok")

    registry.register(bound_capability_of(one))
    registry.register(bound_capability_of(two))
    return registry


class EchoReq(BaseModel):
    x: int


class EchoResp(BaseModel):
    ok: bool


def test_admission_rejects_ungranted_capability(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    bound = surface.capabilities.get("sovereign.session.file.read@1.0.0")
    with pytest.raises(AdmissionRefused):
        admit_capability(
            capability=bound,
            execution=_scope(fresh_session, granted_capabilities=frozenset({"other@1.0.0"})),
        )


def test_approval_required_before_write(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    bound = surface.capabilities.get("sovereign.session.file.write@1.0.0")
    policy = ApprovalPolicy()
    scope = _scope(fresh_session, require_approval_for_mutations=True)
    assert policy.evaluate(bound, scope) is ApprovalDisposition.REQUIRED


@pytest.mark.asyncio
async def test_pre_invoke_approval_does_not_write(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    catalog = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    executor = CapabilityExecutor(surface.capabilities, catalog=catalog)
    scope = _scope(fresh_session, require_approval_for_mutations=True)
    result = await executor.invoke(
        execution=scope,
        provider_call=ToolCall(
            id="1", name="write_file", arguments={"path": "x.md", "content": "nope"}
        ),
    )
    assert result.paused_for_approval is True
    assert not (fresh_session.workspace_dir / "x.md").exists()


@pytest.mark.asyncio
async def test_cancellation_is_not_swallowed() -> None:
    @capability(
        id="sovereign.test.cancel@1.0.0",
        description="cancel",
        effects={EffectKind.READ},
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    async def hang(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        await asyncio.sleep(60)
        return CapabilityResult.ok(data=EchoResp(ok=True), msg="ok")

    bound = bound_capability_of(hang)
    ctx = ToolContext(
        run_id="r",
        tool_name="cancel",
        tool_version="1.0.0",
        logger=__import__("logging").getLogger("t"),
        fs=object(),
        work_dir=".",
        output_dir=".",
    )
    task = asyncio.create_task(invoke_cancellable(bound, EchoReq(x=1), ctx))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_legacy_tool_adapts_to_bound_capability() -> None:
    def ping(label: str) -> ToolResult:
        return ToolResult(success=True, output={"label": label}, summary="ok")

    tool = _RegisteredTool(
        name="ping",
        description="ping",
        fn=ping,
        parameters_schema={"type": "object", "properties": {"label": {"type": "string"}}},
        returns_schema={"type": "object"},
        is_async=False,
        examples=[{"input": {"label": "a"}, "output": {"label": "a"}}],
    )
    bound = registered_tool_to_bound(tool)
    assert isinstance(bound, BoundCapability)


def test_always_parallelism_rejected_outside_tests() -> None:
    with pytest.raises(ValueError, match="not a product option"):
        DefaultExecutor(
            model="fake",
            client=FakeLLMClient([]),
            tools=ToolRegistry(),
            parallelism_policy=PARALLELISM_POLICY_ALWAYS,
        )


def test_runtime_manifest_alias_round_trip() -> None:
    manifest = RuntimeCapabilityManifest(
        FrozenDict(
            (
                (
                    "network",
                    RuntimeCapabilityAssertion(available=True, evidence_level=EvidenceLevel.PROBED),
                ),
            )
        )
    )
    assert RuntimeCapabilityManifest.from_dict(manifest.to_dict()).is_available("network")


@pytest.mark.asyncio
async def test_executor_surface_emits_capability_trace(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    client = FakeLLMClient(
        [
            ScriptedResponse(
                tool_calls=[
                    ToolCall(id="1", name="write_file", arguments={"path": "t.md", "content": "x"}),
                ]
            ),
            ScriptedResponse(content="done"),
        ]
    )
    executor = DefaultExecutor(
        model="fake", client=client, tools=ToolRegistry(), callable_surface=surface
    )
    await executor.execute(_sg(), fresh_session, max_turns=4)
    from sovereign_agent.observability.trace import TraceReader

    events = [
        e for e in TraceReader(fresh_session) if e.event_type == "executor.capability_invoked"
    ]
    assert events
    payload = events[0].payload
    assert "arguments" not in payload
    assert payload["capability_id"] == "sovereign.session.file.write@1.0.0"
    assert payload["request_digest"]
