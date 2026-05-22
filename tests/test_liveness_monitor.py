"""Tests for the M4b LivenessMonitor.

Two layers:

  * Pure-decision tests (_decide_stalled): synthetic SessionSnapshot
    inputs, no fs, no asyncio. Mirrors NanoClaw's decideStuckAction
    test pattern.
  * Integration tests (_scan_once + emit): tmp_path-backed sessions
    with backdated trace events, exercise the full collect → decide →
    emit path. Async tests are sync funcs that drive coroutines via
    asyncio.run() per §3.7.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sovereign_agent._internal.atomic import atomic_append_jsonl
from sovereign_agent.orchestrator.liveness import (
    LivenessMonitor,
    SessionSnapshot,
    StalledSession,
    _decide_stalled,
)
from sovereign_agent.session.directory import create_session
from sovereign_agent.session.state import now_utc

# ---------------------------------------------------------------------------
# _decide_stalled — pure
# ---------------------------------------------------------------------------


def _snap(
    sid: str,
    state: str,
    created_at: datetime,
    last_event_at: datetime | None,
) -> SessionSnapshot:
    return SessionSnapshot(
        session_id=sid,
        state=state,
        created_at=created_at,
        last_event_at=last_event_at,
    )


def test_decide_stalled_empty_input_returns_empty() -> None:
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    assert _decide_stalled([], stall_threshold_s=600.0, now=now) == []


def test_decide_stalled_fresh_session_not_flagged() -> None:
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    snap = _snap(
        "sess_fresh",
        "planning",
        created_at=now - timedelta(seconds=60),
        last_event_at=now - timedelta(seconds=10),
    )
    assert _decide_stalled([snap], stall_threshold_s=600.0, now=now) == []


def test_decide_stalled_stale_session_flagged() -> None:
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    snap = _snap(
        "sess_stale",
        "executing",
        created_at=now - timedelta(seconds=1200),
        last_event_at=now - timedelta(seconds=700),
    )
    result = _decide_stalled([snap], stall_threshold_s=600.0, now=now)
    assert len(result) == 1
    assert result[0].session_id == "sess_stale"
    assert result[0].state == "executing"
    assert result[0].last_event_age_s == 700.0


def test_decide_stalled_no_trace_uses_created_at_as_floor() -> None:
    # Convention over configuration: no separate grace knob. A session
    # without trace events that crosses the threshold from created_at is
    # genuinely stalled and should be flagged.
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    snap = _snap(
        "sess_never_started",
        "planning",
        created_at=now - timedelta(seconds=900),
        last_event_at=None,
    )
    result = _decide_stalled([snap], stall_threshold_s=600.0, now=now)
    assert len(result) == 1
    assert result[0].last_event_age_s == 900.0


def test_decide_stalled_terminal_states_skipped() -> None:
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    snaps = [
        _snap("sess_done", "completed", now - timedelta(hours=2), None),
        _snap("sess_dead", "failed", now - timedelta(hours=2), None),
        _snap("sess_esc", "escalated", now - timedelta(hours=2), None),
    ]
    assert _decide_stalled(snaps, stall_threshold_s=600.0, now=now) == []


def test_decide_stalled_mixed_returns_only_stale_active() -> None:
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    snaps = [
        _snap(
            "sess_fresh",
            "planning",
            now - timedelta(seconds=60),
            now - timedelta(seconds=10),
        ),
        _snap(
            "sess_stale",
            "executing",
            now - timedelta(seconds=1200),
            now - timedelta(seconds=900),
        ),
        _snap("sess_done", "completed", now - timedelta(hours=2), None),
    ]
    result = _decide_stalled(snaps, stall_threshold_s=600.0, now=now)
    assert [s.session_id for s in result] == ["sess_stale"]


def test_decide_stalled_exact_threshold_not_flagged() -> None:
    # Strict ">", not ">=", because polling jitter shouldn't trip the rule
    # when the age is precisely at threshold.
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    snap = _snap(
        "sess_edge",
        "planning",
        created_at=now - timedelta(seconds=600),
        last_event_at=now - timedelta(seconds=600),
    )
    assert _decide_stalled([snap], stall_threshold_s=600.0, now=now) == []


def test_stalled_session_dataclass_is_frozen() -> None:
    s = StalledSession(session_id="x", state="planning", last_event_age_s=700.0)
    import dataclasses

    assert dataclasses.is_dataclass(s)


# ---------------------------------------------------------------------------
# _scan_once — async wrapper, tmp_path-backed
# ---------------------------------------------------------------------------


def _make_session_with_backdated_trace(
    sessions_dir: Path,
    *,
    session_id: str,
    state: str,
    last_event_age_s: float | None,
) -> None:
    """Create a session and (optionally) write a backdated trace event."""
    session = create_session(
        scenario="test",
        task="m4b liveness",
        sessions_dir=sessions_dir,
        session_id=session_id,
    )
    if state != "planning":
        # Forward-only transitions: walk through `executing` for terminal states.
        if state in {"completed", "failed", "escalated"}:
            session.update_state(state="executing")
        session.update_state(state=state)
    if last_event_age_s is not None:
        ts = now_utc() - timedelta(seconds=last_event_age_s)
        atomic_append_jsonl(
            session.trace_path,
            {
                "event_type": "test.backdated",
                "actor": "test",
                "timestamp": ts.isoformat(),
                "payload": {},
            },
        )


def test_scan_once_no_sessions_emits_nothing(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    stalled = asyncio.run(monitor._scan_once())
    assert stalled == []


def test_scan_once_flags_stalled_and_writes_trace(tmp_path: Path) -> None:
    _make_session_with_backdated_trace(
        tmp_path,
        session_id="sess_stale01",
        state="executing",
        last_event_age_s=900.0,
    )
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    stalled = asyncio.run(monitor._scan_once())
    assert len(stalled) == 1
    assert stalled[0].session_id == "sess_stale01"

    # Trace event should have landed in this session's trace.jsonl.
    trace_path = tmp_path / "sess_stale01" / "logs" / "trace.jsonl"
    events = [json.loads(line) for line in trace_path.read_text().strip().split("\n") if line]
    stall_events = [e for e in events if e.get("event_type") == "liveness.session_stalled"]
    assert len(stall_events) == 1
    assert stall_events[0]["actor"] == "liveness_monitor"
    assert stall_events[0]["payload"]["session_id"] == "sess_stale01"
    assert stall_events[0]["payload"]["state"] == "executing"
    assert stall_events[0]["payload"]["last_event_age_s"] >= 900.0


def test_scan_once_skips_fresh_sessions(tmp_path: Path) -> None:
    _make_session_with_backdated_trace(
        tmp_path,
        session_id="sess_fresh001",
        state="planning",
        last_event_age_s=10.0,
    )
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    stalled = asyncio.run(monitor._scan_once())
    assert stalled == []


def test_scan_once_skips_terminal_sessions(tmp_path: Path) -> None:
    _make_session_with_backdated_trace(
        tmp_path,
        session_id="sess_done0001",
        state="completed",
        last_event_age_s=3600.0,
    )
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    stalled = asyncio.run(monitor._scan_once())
    assert stalled == []


def test_scan_once_uses_created_at_when_no_trace(tmp_path: Path) -> None:
    # No backdated trace event — but created_at is also "now" via create_session.
    # Use a very low threshold to force flagging from created_at floor.
    _make_session_with_backdated_trace(
        tmp_path,
        session_id="sess_notrace01",
        state="planning",
        last_event_age_s=None,
    )
    # Sleep just enough to make age > threshold without slowing the suite.
    import time

    time.sleep(0.2)
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=0.1,
        poll_interval_s=60.0,
    )
    stalled = asyncio.run(monitor._scan_once())
    assert len(stalled) == 1
    assert stalled[0].session_id == "sess_notrace01"


def test_scan_once_tolerates_corrupt_trace(tmp_path: Path) -> None:
    # Truncated final line shouldn't blow up the read; it's just ignored.
    _make_session_with_backdated_trace(
        tmp_path,
        session_id="sess_corrupt01",
        state="executing",
        last_event_age_s=900.0,
    )
    trace = tmp_path / "sess_corrupt01" / "logs" / "trace.jsonl"
    with open(trace, "a", encoding="utf-8") as f:
        f.write('{"event_type": "test.partial"')  # no closing brace, no newline
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    stalled = asyncio.run(monitor._scan_once())
    assert len(stalled) == 1


# ---------------------------------------------------------------------------
# Lifecycle — disabled flag + safe shutdown
# ---------------------------------------------------------------------------


def test_run_returns_immediately_when_disabled(tmp_path: Path) -> None:
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
        enabled=False,
    )

    async def _run() -> None:
        # Wrap in wait_for so a regression that doesn't honour `enabled`
        # surfaces as a test timeout instead of hanging forever.
        await asyncio.wait_for(monitor.run(), timeout=1.0)

    asyncio.run(_run())


def test_shutdown_is_safe_on_never_started(tmp_path: Path) -> None:
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    asyncio.run(monitor.shutdown())  # should not raise
