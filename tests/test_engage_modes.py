"""v0.3 Module 2 — engage_mode tests.

Three modes, one knob:

  * interactive : human approves; bot replies only to is_mention=True
  * autonomous  : bot auto-approves; bot replies to all routed events
  * silent      : bot auto-approves; bot replies to nothing (shadow mode)

These tests cover four layers in increasing integration:

  1. Config carries the new field with the right default and env override.
  2. `build_auto_decision()` is pure: same input -> same output, no I/O.
  3. The AutoApprover loop turns awaiting/ files into granted/ files in
     autonomous/silent modes, and is a strict no-op in interactive mode.
  4. The Orchestrator's `_deliver_channel_response` honours engage_mode
     and the is_mention flag on the originating inbox event.

stdlib only; sync tests driving asyncio via asyncio.run(). No pytest-asyncio.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from sovereign_agent.channels.adapter import InboundEvent, OutboundMessage
from sovereign_agent.config import Config
from sovereign_agent.ipc.approval import (
    ApprovalRequest,
    build_auto_decision,
    list_pending_approvals,
    write_approval_request,
)
from sovereign_agent.session.directory import create_session, load_session
from sovereign_agent.session.state import now_utc


# ---------------------------------------------------------------------------
# Fixtures and fakes
# ---------------------------------------------------------------------------


def _fake_request(request_id: str = "appr_test_001") -> ApprovalRequest:
    """Build a minimal ApprovalRequest. The shape is what the executor would
    write; the contents are arbitrary."""
    return ApprovalRequest(
        request_id=request_id,
        session_id="sess_irrelevant",
        subgoal_id="sg1",
        ticket_id="tk1",
        tool_name="payment.charge",
        tool_arguments={"amount_pence": 5000},
        arguments_sha256="0" * 64,
        proposed_output={"charge_id": "ch_xxx"},
        tool_summary="Charge £50 to card xxxx-4242",
        created_at=now_utc().isoformat(),
        reason="amount exceeds auto-charge threshold",
    )


class RecordingAdapter:
    """A ChannelAdapter test double that records every deliver() call."""

    name = "cli"
    channel_type = "cli"
    supports_threads = False

    def __init__(self) -> None:
        self.delivered: list[tuple[str, str | None, OutboundMessage]] = []

    async def setup(self, router) -> None:  # noqa: D401
        pass

    async def teardown(self) -> None:
        pass

    async def deliver(self, platform_id, thread_id, message):
        self.delivered.append((platform_id, thread_id, message))
        return platform_id


class FakeQueue:
    """The InboundRouter's queue dependency. We don't need it to actually
    process anything — just to accept the enqueue call."""

    def __init__(self) -> None:
        self.enqueued: list[str] = []

    async def enqueue_planner(self, session_id: str) -> None:
        self.enqueued.append(session_id)


class FakeHalfResult:
    """The minimal shape `_deliver_channel_response` reads from a HalfResult."""

    def __init__(self, final_answer: str = "the answer", summary: str = "") -> None:
        self.output = {"final_answer": final_answer}
        self.summary = summary
        self.next_action = "complete"


# ---------------------------------------------------------------------------
# 1. Config carries engage_mode with the right default and env override
# ---------------------------------------------------------------------------


def test_default_engage_mode_is_interactive():
    """v0.2 behaviour is preserved by the default value."""
    assert Config().engage_mode == "interactive"


def test_engage_mode_from_env(monkeypatch):
    monkeypatch.setenv("SOVEREIGN_AGENT_ENGAGE_MODE", "autonomous")
    assert Config.from_env().engage_mode == "autonomous"


def test_engage_mode_from_env_silent(monkeypatch):
    monkeypatch.setenv("SOVEREIGN_AGENT_ENGAGE_MODE", "silent")
    assert Config.from_env().engage_mode == "silent"


# ---------------------------------------------------------------------------
# 2. build_auto_decision is pure and matches the mode contract
# ---------------------------------------------------------------------------


def test_build_auto_decision_interactive_returns_none():
    """Interactive must NOT auto-decide — a human is required."""
    assert build_auto_decision(_fake_request(), "interactive") is None


def test_build_auto_decision_autonomous_grants():
    response = build_auto_decision(_fake_request("appr_a"), "autonomous")
    assert response is not None
    assert response.request_id == "appr_a"
    assert response.decision == "granted"
    assert response.approver == "auto:engage_mode_autonomous"
    # The reason is surfaced to the LLM and the audit log — must be
    # informative enough that a reader can tell why it ran without a human.
    assert "autonomous" in response.reason


def test_build_auto_decision_silent_grants_with_silent_approver():
    response = build_auto_decision(_fake_request(), "silent")
    assert response is not None
    assert response.decision == "granted"
    assert response.approver == "auto:engage_mode_silent"


# ---------------------------------------------------------------------------
# 3. AutoApprover end-to-end against a real session directory
# ---------------------------------------------------------------------------


def test_auto_approver_interactive_is_a_strict_noop(tmp_path):
    """In interactive mode the run loop must return without touching the
    file system. Existing awaiting/ requests stay awaiting."""
    from sovereign_agent.orchestrator.auto_approver import AutoApprover

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    session = create_session(scenario="default", task="t", sessions_dir=sessions_dir)
    write_approval_request(session, _fake_request("appr_int"))

    async def _run() -> None:
        approver = AutoApprover(
            sessions_dir=sessions_dir,
            engage_mode="interactive",
            poll_interval_s=0.05,
        )
        # In interactive mode run() should return immediately.
        await asyncio.wait_for(approver.run(), timeout=1.0)

    asyncio.run(_run())

    # The pending request is still awaiting; no grant file was created.
    pending = list_pending_approvals(session)
    assert len(pending) == 1
    assert pending[0].request_id == "appr_int"
    granted_dir = session.directory / "ipc" / "approval_granted"
    if granted_dir.exists():
        assert not list(granted_dir.iterdir())


def test_auto_approver_autonomous_grants_pending_requests(tmp_path):
    """The loop moves awaiting/<id>.json -> approval_granted/<id>.json with
    a synthetic approver. The merged payload preserves the original request."""
    from sovereign_agent.orchestrator.auto_approver import AutoApprover

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    session = create_session(scenario="default", task="t", sessions_dir=sessions_dir)
    write_approval_request(session, _fake_request("appr_auto1"))

    async def _run() -> None:
        approver = AutoApprover(
            sessions_dir=sessions_dir,
            engage_mode="autonomous",
            poll_interval_s=0.02,
        )
        task = asyncio.create_task(approver.run())
        granted = session.directory / "ipc" / "approval_granted" / "appr_auto1.json"
        for _ in range(100):
            if granted.exists():
                break
            await asyncio.sleep(0.02)
        await approver.shutdown()
        await asyncio.wait_for(task, timeout=2.0)

        assert granted.exists(), "approver never produced a granted file"
        awaiting = session.directory / "ipc" / "awaiting_approval" / "appr_auto1.json"
        assert not awaiting.exists(), "awaiting file should have been moved"

        payload = json.loads(granted.read_text(encoding="utf-8"))
        assert payload["response"]["approver"] == "auto:engage_mode_autonomous"
        assert payload["response"]["decision"] == "granted"
        # Request preserved alongside the response.
        assert payload["request"]["request_id"] == "appr_auto1"
        assert payload["request"]["tool_name"] == "payment.charge"

    asyncio.run(_run())


def test_auto_approver_silent_grants_with_silent_approver(tmp_path):
    """Silent mode auto-grants exactly like autonomous; the difference is
    in channel delivery (tested below), not in approval policy."""
    from sovereign_agent.orchestrator.auto_approver import AutoApprover

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    session = create_session(scenario="default", task="t", sessions_dir=sessions_dir)
    write_approval_request(session, _fake_request("appr_silent1"))

    async def _run() -> None:
        approver = AutoApprover(
            sessions_dir=sessions_dir,
            engage_mode="silent",
            poll_interval_s=0.02,
        )
        task = asyncio.create_task(approver.run())
        granted = session.directory / "ipc" / "approval_granted" / "appr_silent1.json"
        for _ in range(100):
            if granted.exists():
                break
            await asyncio.sleep(0.02)
        await approver.shutdown()
        await asyncio.wait_for(task, timeout=2.0)

        assert granted.exists()
        payload = json.loads(granted.read_text(encoding="utf-8"))
        assert payload["response"]["approver"] == "auto:engage_mode_silent"

    asyncio.run(_run())


def test_auto_approver_ignores_non_session_directories(tmp_path):
    """Stray dirs in sessions/ (logs, archive, etc.) must not crash the
    scan. We only touch directories starting with `sess_`."""
    from sovereign_agent.orchestrator.auto_approver import AutoApprover

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "archive").mkdir()
    (sessions_dir / "logs").mkdir()

    async def _run() -> None:
        approver = AutoApprover(
            sessions_dir=sessions_dir,
            engage_mode="autonomous",
            poll_interval_s=0.02,
        )
        # One full scan should suffice; no pending requests means the
        # loop should just iterate and sleep.
        await approver._scan_once()  # type: ignore[attr-defined]

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# 4. Orchestrator-level engage_mode gates on channel delivery
# ---------------------------------------------------------------------------
# Each of these constructs a real Orchestrator with a RecordingAdapter, drives
# a single inbound event through the InboundRouter so the session gets a
# binding (and an inbox entry with a known is_mention value), then invokes
# `_deliver_channel_response` directly and asserts on whether the adapter saw
# a deliver() call.


def _seed_session_with_event(*, sessions_dir: Path, router, is_mention: bool):
    """Push one InboundEvent through the real router. Returns the session."""
    event = InboundEvent(
        channel_type="cli",
        platform_id="cli-main",
        thread_id=None,
        sender_id="cli:local",
        text="hello",
        timestamp=datetime.now(timezone.utc),
        is_mention=is_mention,
    )

    async def _route():
        return await router.route(event)

    session_id = asyncio.run(_route())
    return load_session(session_id, sessions_dir=sessions_dir)


def test_silent_mode_suppresses_channel_delivery(tmp_path):
    """Even with a channel binding and is_mention=True, silent mode never
    calls adapter.deliver()."""
    from sovereign_agent.orchestrator import Orchestrator

    cfg = Config(sessions_dir=tmp_path / "sessions", engage_mode="silent")
    adapter = RecordingAdapter()
    orch = Orchestrator(cfg, adapters=[adapter])

    session = _seed_session_with_event(
        sessions_dir=cfg.sessions_dir, router=orch.router, is_mention=True
    )

    async def _deliver() -> None:
        await orch._deliver_channel_response(session, FakeHalfResult())  # noqa: SLF001

    asyncio.run(_deliver())
    assert adapter.delivered == [], "silent mode must not deliver"


def test_autonomous_mode_delivers_regardless_of_mention(tmp_path):
    """Autonomous mode replies to everything, mention or not."""
    from sovereign_agent.orchestrator import Orchestrator

    cfg = Config(sessions_dir=tmp_path / "sessions", engage_mode="autonomous")
    adapter = RecordingAdapter()
    orch = Orchestrator(cfg, adapters=[adapter])

    session = _seed_session_with_event(
        sessions_dir=cfg.sessions_dir, router=orch.router, is_mention=False
    )

    async def _deliver() -> None:
        await orch._deliver_channel_response(session, FakeHalfResult())  # noqa: SLF001

    asyncio.run(_deliver())
    assert len(adapter.delivered) == 1
    _, _, message = adapter.delivered[0]
    assert message.kind == "text"
    assert message.content["text"] == "the answer"


def test_interactive_mode_delivers_when_mentioned(tmp_path):
    """Interactive default behaviour: replies to direct mentions. CLI always
    sets is_mention=True so this is the normal CLI path."""
    from sovereign_agent.orchestrator import Orchestrator

    cfg = Config(sessions_dir=tmp_path / "sessions", engage_mode="interactive")
    adapter = RecordingAdapter()
    orch = Orchestrator(cfg, adapters=[adapter])

    session = _seed_session_with_event(
        sessions_dir=cfg.sessions_dir, router=orch.router, is_mention=True
    )

    async def _deliver() -> None:
        await orch._deliver_channel_response(session, FakeHalfResult())  # noqa: SLF001

    asyncio.run(_deliver())
    assert len(adapter.delivered) == 1


def test_interactive_mode_stays_quiet_for_non_mentions(tmp_path):
    """Interactive in a group chat: when the triggering event was NOT a
    mention, the bot listens but does not respond. CLI never hits this
    branch (is_mention=True always); a future Telegram/Slack adapter will."""
    from sovereign_agent.orchestrator import Orchestrator

    cfg = Config(sessions_dir=tmp_path / "sessions", engage_mode="interactive")
    adapter = RecordingAdapter()
    orch = Orchestrator(cfg, adapters=[adapter])

    session = _seed_session_with_event(
        sessions_dir=cfg.sessions_dir, router=orch.router, is_mention=False
    )

    async def _deliver() -> None:
        await orch._deliver_channel_response(session, FakeHalfResult())  # noqa: SLF001

    asyncio.run(_deliver())
    assert adapter.delivered == [], "interactive + non-mention must not deliver"
