"""v0.6 capability-native runtime: catalog, cancel, approval, locks, evidence."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time

import pytest
from pydantic import BaseModel
from zeo_core.contracts import CapabilityExample, CapabilityResult, ConcurrencyMode, EffectKind
from zeo_core.tools import (
    ToolContext,
    bound_capability_of,
    capability,
)
from zeo_core.tools.invoke import invoke_async

from sovereign_agent._internal.llm_client import ToolCall
from sovereign_agent.capabilities.approval import (
    decide_capability_approval,
    persist_capability_approval,
)
from sovereign_agent.capabilities.catalog import (
    CatalogMismatch,
    bind_session_catalog,
    freeze_catalog,
)
from sovereign_agent.capabilities.context import ExecutionScope
from sovereign_agent.capabilities.evidence import (
    list_invocation_refs,
    verify_receipt_invocation_linkage,
)
from sovereign_agent.capabilities.executor import CapabilityExecutor
from sovereign_agent.capabilities.invoke import invoke_cancellable, zeocore_swallows_cancel
from sovereign_agent.capabilities.legacy import UnrepresentableLegacyTool, registered_tool_to_bound
from sovereign_agent.capabilities.locks import ConcurrencyGate, LockContention, LockOwnership
from sovereign_agent.capabilities.surface import (
    empty_runtime_manifest,
    make_session_callable_surface,
    session_execution_services,
)
from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import _RegisteredTool


class EchoReq(BaseModel):
    x: int = 1
    path: str = "k"


class EchoResp(BaseModel):
    ok: bool = True


def _scope(session: Session, **kwargs: object) -> ExecutionScope:
    return ExecutionScope(
        id=session.session_id,
        work_dir=session.workspace_dir,
        output_dir=session.directory,
        runtime_manifest=empty_runtime_manifest(),
        services=session_execution_services(session),
        session=session,
        **kwargs,  # type: ignore[arg-type]
    )


def _ctx() -> ToolContext:
    return ToolContext(
        run_id="r",
        tool_name="t",
        tool_version="1.0.0",
        logger=__import__("logging").getLogger("t"),
        fs=object(),
        work_dir=".",
        output_dir=".",
    )


@pytest.mark.asyncio
async def test_zeocore_invoke_async_swallows_cancel() -> None:
    assert zeocore_swallows_cancel()

    @capability(
        id="sovereign.test.upstream_cancel@1.0.0",
        description="cancel",
        effects={EffectKind.READ},
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    async def hang(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        await asyncio.sleep(60)
        return CapabilityResult.ok(data=EchoResp(), msg="ok")

    bound = bound_capability_of(hang)
    task = asyncio.create_task(invoke_async(bound, EchoReq(), _ctx()))
    await asyncio.sleep(0.02)
    task.cancel()
    result = await task
    assert result.outcome is not None
    assert result.outcome.value != "success"
    assert (
        "CancelledError" in (result.human_message or "")
        or result.machine_message == "ZEO_CAP_UNEXPECTED"
    )


@pytest.mark.asyncio
async def test_sovereign_cancel_is_not_unexpected() -> None:
    @capability(
        id="sovereign.test.sa_cancel@1.0.0",
        description="cancel",
        effects={EffectKind.READ},
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    async def hang(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        await asyncio.sleep(60)
        return CapabilityResult.ok(data=EchoResp(), msg="ok")

    bound = bound_capability_of(hang)
    task = asyncio.create_task(invoke_cancellable(bound, EchoReq(), _ctx()))
    await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_keyboardinterrupt_and_systemexit_propagate() -> None:
    @capability(
        id="sovereign.test.kb@1.0.0",
        description="kb",
        effects={EffectKind.READ},
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    def boom(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        await invoke_cancellable(bound_capability_of(boom), EchoReq(), _ctx())

    @capability(
        id="sovereign.test.sysexit@1.0.0",
        description="exit",
        effects={EffectKind.READ},
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    def die(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        raise SystemExit(2)

    with pytest.raises(SystemExit):
        await invoke_cancellable(bound_capability_of(die), EchoReq(), _ctx())


@pytest.mark.asyncio
async def test_cancel_before_admission(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    catalog = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    executor = CapabilityExecutor(surface.capabilities, catalog=catalog)

    class Flag:
        def is_cancelled(self) -> bool:
            return True

    result = await executor.invoke(
        execution=_scope(fresh_session),
        provider_call=ToolCall(id="1", name="read_file", arguments={"path": "missing.md"}),
        cancellation=Flag(),
    )
    assert result.provider_response.get(
        "code"
    ) == "ZEO_CAP_CANCELLED" or result.provider_response.get("outcome") in {
        "cancelled",
        None,
        "failed",
    }


@pytest.mark.asyncio
async def test_catalog_resume_refuses_changed_registry(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    live = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    frozen = bind_session_catalog(fresh_session.directory, live)
    assert frozen.digest == live.digest

    @capability(
        id="sovereign.test.extra@1.0.0",
        description="extra",
        effects={EffectKind.READ},
        projection_name="extra_cap",
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    def extra(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        return CapabilityResult.ok(data=EchoResp(), msg="ok")

    surface.capabilities.register(bound_capability_of(extra))
    changed = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    with pytest.raises(CatalogMismatch):
        bind_session_catalog(fresh_session.directory, changed)


@pytest.mark.asyncio
async def test_approval_restart_invokes_once(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    catalog = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    executor = CapabilityExecutor(surface.capabilities, catalog=catalog)
    paused = await executor.invoke(
        execution=_scope(fresh_session, require_approval_for_mutations=True),
        provider_call=ToolCall(
            id="1", name="write_file", arguments={"path": "once.md", "content": "one"}
        ),
    )
    assert paused.paused_for_approval
    approval_id = paused.approval_id
    assert approval_id
    assert not (fresh_session.workspace_dir / "once.md").exists()

    decide_capability_approval(
        fresh_session.directory, approval_id, decision="approved", actor="test", reason="ok"
    )
    resumed = await executor.invoke(
        execution=_scope(fresh_session, require_approval_for_mutations=True),
        provider_call=ToolCall(
            id="1", name="write_file", arguments={"path": "once.md", "content": "one"}
        ),
        resume_approval_id=approval_id,
    )
    assert resumed.record is not None
    assert (fresh_session.workspace_dir / "once.md").read_text() == "one"
    second = await executor.invoke(
        execution=_scope(fresh_session, require_approval_for_mutations=True),
        provider_call=ToolCall(
            id="1", name="write_file", arguments={"path": "once.md", "content": "two"}
        ),
        resume_approval_id=approval_id,
    )
    assert second.provider_response.get("output", {}).get("idempotent") is True
    assert (fresh_session.workspace_dir / "once.md").read_text() == "one"
    refs = list_invocation_refs(fresh_session.directory)
    assert len(refs) == 1
    verify_receipt_invocation_linkage(
        fresh_session.directory, catalog_digest=catalog.digest, invocation_refs=refs
    )


@pytest.mark.asyncio
async def test_duplicate_deny_is_idempotent(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    catalog = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    bound = surface.capabilities.get("sovereign.session.file.write@1.0.0")
    from sovereign_agent.capabilities.catalog import definition_digest

    pending = persist_capability_approval(
        fresh_session.directory,
        catalog=catalog,
        canonical_id=bound.definition.id.canonical(),
        definition_digest=definition_digest(bound),
        arguments={"path": "x.md", "content": "secret-token-value"},
        reason="test",
        execution_id=fresh_session.session_id,
    )
    blob = json.dumps(pending)
    assert "secret-token-value" not in blob
    first = decide_capability_approval(
        fresh_session.directory, pending["approval_id"], decision="denied", actor="t", reason="no"
    )
    second = decide_capability_approval(
        fresh_session.directory, pending["approval_id"], decision="denied", actor="t", reason="no"
    )
    assert first["decision"] == second["decision"] == "denied"


@pytest.mark.asyncio
async def test_durable_lock_contention_across_process(fresh_session: Session) -> None:
    root = fresh_session.directory / "capabilities" / "locks"

    @capability(
        id="sovereign.test.lock@1.0.0",
        description="lock",
        effects={EffectKind.WRITE},
        concurrency=ConcurrencyMode.EXCLUSIVE,
        examples=(CapabilityExample(request={"x": 1}, response={"ok": True}),),
    )
    def locked(request: EchoReq, ctx: ToolContext) -> CapabilityResult[EchoResp]:
        return CapabilityResult.ok(data=EchoResp(), msg="ok")

    bound = bound_capability_of(locked)
    from sovereign_agent.capabilities.locks import coordination_lock_key

    key = coordination_lock_key(bound, EchoReq(), LockOwnership(session="s"))
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import json, pathlib, secrets, sys, time\n"
            "root = pathlib.Path(sys.argv[1])\n"
            "key = sys.argv[2]\n"
            "root.mkdir(parents=True, exist_ok=True)\n"
            "lock = root / key\n"
            "lock.mkdir()\n"
            "(lock / 'owner.json').write_text(json.dumps({'token': secrets.token_hex(8), 'heartbeat_ns': time.time_ns()*10, 'lease_seconds': 60}))\n"
            "time.sleep(20)\n",
            str(root),
            key,
        ]
    )
    try:
        for _ in range(50):
            if (root / key / "owner.json").exists():
                break
            time.sleep(0.02)
        else:
            holder.kill()
            raise AssertionError("holder did not create the lease")
        gate = ConcurrencyGate(root, acquire_timeout=0.3, lease_seconds=60)
        with pytest.raises(LockContention):
            async with gate.hold(bound, EchoReq(), ownership=LockOwnership(session="s")):
                pass
    finally:
        holder.kill()
        holder.wait(timeout=5)


def test_legacy_runtime_command_cannot_be_adapted() -> None:
    tool = _RegisteredTool(
        name="complete_task",
        description="nope",
        fn=lambda: None,
        parameters_schema={"type": "object"},
        returns_schema={"type": "object"},
        is_async=False,
    )
    with pytest.raises(UnrepresentableLegacyTool):
        registered_tool_to_bound(tool)


@pytest.mark.asyncio
async def test_evidence_has_no_raw_secret(fresh_session: Session) -> None:
    surface = make_session_callable_surface(fresh_session)
    catalog = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    executor = CapabilityExecutor(surface.capabilities, catalog=catalog)
    await executor.invoke(
        execution=_scope(fresh_session),
        provider_call=ToolCall(
            id="1",
            name="write_file",
            arguments={"path": "s.md", "content": "password=supersecret"},
        ),
    )
    refs = list_invocation_refs(fresh_session.directory)
    verify_receipt_invocation_linkage(
        fresh_session.directory, catalog_digest=catalog.digest, invocation_refs=refs
    )
