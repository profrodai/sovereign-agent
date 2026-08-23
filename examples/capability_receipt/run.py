"""End-to-end capability path: project, invoke, evidence, receipt, restart, verify.

python -m examples.capability_receipt.run
"""

from __future__ import annotations

import asyncio
import json

from pydantic import BaseModel
from zeo_core.contracts import CapabilityExample, CapabilityResult, EffectKind
from zeo_core.tools import ToolContext, bound_capability_of, capability

from sovereign_agent._internal.llm_client import FakeLLMClient, ScriptedResponse, ToolCall
from sovereign_agent._internal.paths import example_sessions_dir
from sovereign_agent.capabilities.catalog import bind_session_catalog, freeze_catalog
from sovereign_agent.capabilities.evidence import (
    list_invocation_refs,
    verify_receipt_invocation_linkage,
)
from sovereign_agent.capabilities.surface import make_session_callable_surface
from sovereign_agent.contracts import ExecutionId, ExecutionReceipt, InvocationId, ReceiptStatus
from sovereign_agent.executor import DefaultExecutor
from sovereign_agent.planner import Subgoal
from sovereign_agent.session.directory import create_session
from sovereign_agent.session.state import now_utc
from sovereign_agent.tools.registry import ToolRegistry


class NoteRequest(BaseModel):
    path: str
    content: str


class NoteResponse(BaseModel):
    path: str


@capability(
    id="example.receipt.write_note@1.0.0",
    description="Write a short note into the session workspace.",
    effects={EffectKind.WRITE},
    projection_name="write_note",
    examples=(
        CapabilityExample(
            request={"path": "note.md", "content": "ok"},
            response={"path": "note.md"},
        ),
    ),
)
def write_note(request: NoteRequest, ctx: ToolContext) -> CapabilityResult[NoteResponse]:
    fs = ctx.get_service("session.filesystem")
    resolved = fs.resolve(request.path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(request.content, encoding="utf-8")
    return CapabilityResult.ok(data=NoteResponse(path=request.path), msg="wrote note")


async def _run() -> None:
    with example_sessions_dir("capability_receipt", persist=False) as sessions_root:
        session = create_session(
            scenario="capability-receipt",
            task="write a note and complete",
            sessions_dir=sessions_root,
        )
        surface = make_session_callable_surface(session)
        surface.capabilities.register(bound_capability_of(write_note))
        live = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
        frozen = bind_session_catalog(session.directory, live)
        client = FakeLLMClient(
            [
                ScriptedResponse(
                    tool_calls=[
                        ToolCall(
                            id="1",
                            name="write_note",
                            arguments={"path": "note.md", "content": "hello"},
                        )
                    ]
                ),
                ScriptedResponse(
                    tool_calls=[
                        ToolCall(id="2", name="complete_task", arguments={"result": {"ok": True}})
                    ]
                ),
                ScriptedResponse(content="done"),
            ]
        )
        executor = DefaultExecutor(
            model="fake", client=client, tools=ToolRegistry(), callable_surface=surface
        )
        subgoal = Subgoal(
            id="sg_1",
            description="write note",
            success_criterion="note.md exists",
            estimated_tool_calls=1,
            assigned_half="loop",
        )
        await executor.execute(subgoal, session, max_turns=4)
        # Simulated restart: reload catalog, refuse if it changed.
        restarted = bind_session_catalog(session.directory, live)
        assert restarted.digest == frozen.digest
        refs = list_invocation_refs(session.directory)
        assert refs
        verify_receipt_invocation_linkage(
            session.directory, catalog_digest=frozen.digest, invocation_refs=refs
        )
        receipt = ExecutionReceipt(
            execution_id=ExecutionId(session.session_id),
            invocation_id=InvocationId("inv_receipt_demo"),
            status=ReceiptStatus.SUCCEEDED,
            started_at=now_utc(),
            completed_at=now_utc(),
            capability_catalog_digest=frozen.digest,
            capability_invocation_refs=refs,
        )
        finalized = receipt.finalize()
        print(
            json.dumps(
                {
                    "session": session.session_id,
                    "catalog_digest": frozen.digest,
                    "invocation_refs": list(refs),
                    "receipt": finalized.evidence_sha256,
                    "note": (session.workspace_dir / "note.md").read_text(),
                },
                indent=2,
            )
        )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
