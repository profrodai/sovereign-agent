"""Single-node soak harness. Compressed by default; --hours 72 for the release gate."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from sovereign_agent._internal.llm_client import ToolCall
from sovereign_agent.capabilities.approval import decide_capability_approval
from sovereign_agent.capabilities.catalog import freeze_catalog
from sovereign_agent.capabilities.context import ExecutionScope
from sovereign_agent.capabilities.executor import CapabilityExecutor
from sovereign_agent.capabilities.surface import (
    empty_runtime_manifest,
    make_session_callable_surface,
    session_execution_services,
)
from sovereign_agent.session.directory import create_session


def _scope(session, **kwargs):
    return ExecutionScope(
        id=session.session_id,
        work_dir=session.workspace_dir,
        output_dir=session.directory,
        runtime_manifest=empty_runtime_manifest(),
        services=session_execution_services(session),
        session=session,
        **kwargs,
    )


async def _once(root: Path) -> dict:
    sessions = root / "sessions"
    session = create_session(scenario="soak", task="soak", sessions_dir=sessions)
    surface = make_session_callable_surface(session)
    catalog = freeze_catalog(surface.capabilities, extra_names=surface.commands.names())
    executor = CapabilityExecutor(surface.capabilities, catalog=catalog)
    paused = await executor.invoke(
        execution=_scope(session, require_approval_for_mutations=True),
        provider_call=ToolCall(
            id="1", name="write_file", arguments={"path": "soak.md", "content": "x"}
        ),
    )
    assert paused.paused_for_approval and paused.approval_id
    decide_capability_approval(
        session.directory, paused.approval_id, decision="approved", actor="soak", reason="ok"
    )
    await executor.invoke(
        execution=_scope(session, require_approval_for_mutations=True),
        provider_call=ToolCall(
            id="1", name="write_file", arguments={"path": "soak.md", "content": "x"}
        ),
        resume_approval_id=paused.approval_id,
    )
    receipt = {
        "started_at": datetime.now(UTC).isoformat(),
        "mode": "compressed",
        "session_id": session.session_id,
        "catalog_digest": catalog.digest,
        "ok": (session.workspace_dir / "soak.md").exists(),
    }
    path = root / "soak-receipt.json"
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=0)
    parser.add_argument("--runtime", type=Path, default=Path("_transient/soak"))
    args = parser.parse_args()
    args.runtime.mkdir(parents=True, exist_ok=True)
    if args.hours and args.hours > 0:
        deadline = time.time() + args.hours * 3600
        last = None
        while time.time() < deadline:
            last = asyncio.run(_once(args.runtime))
            time.sleep(min(60.0, 1.0))
        print(json.dumps(last, indent=2))
        return 0 if last and last.get("ok") else 1
    receipt = asyncio.run(_once(args.runtime))
    print(json.dumps(receipt, indent=2))
    return 0 if receipt.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
