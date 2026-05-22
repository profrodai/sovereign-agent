"""Liveness monitor: detect stalled sessions, emit heartbeat for external observers.

See docs/sows/MODULE_4b_liveness_monitor.md.

## Why this exists

Operator-grade visibility before v0.3 freeze. Two signals:

  1. **Session-stalled signal.** A session whose last activity is older than
     `stall_threshold_s` gets a ``liveness.session_stalled`` trace event so
     an operator (or a future health endpoint) can flag it. We never kill
     or recover — that's the orchestrator's job. The SOW frames this as
     "ships the signal, not the policy."

  2. **Heartbeat file.** The monitor maintains
     ``<sessions_dir>/.orchestrator_heartbeat`` with `{pid, started_at}`.
     External observers check whether the *mtime* is fresh — content stays
     static, only the timestamp moves. Following NanoClaw's
     ``src/host-sweep.ts`` (60s sweep, mtime-as-liveness): one syscall,
     atomic by construction, survives content corruption with a fresh
     mtime still meaning "writer is alive."

## What it never does

  * Kill sessions or workers. M4b is a sensor, not a fixer.
  * Block on poll cadence (sleeps cooperatively via ``asyncio.sleep``).
  * Mutate session state. Trace events are append-only.
  * Inspect terminal sessions (``completed``/``failed``/``escalated``).

## Pure-decision split

``_decide_stalled`` is pure: it takes a list of session snapshots and
returns the stalled subset. Tests hit it directly with synthetic inputs
instead of writing backdated trace events to disk. The async wrapper
``_scan_once`` does the I/O (``list_sessions``, trace reads, event emits)
and feeds the result in. Mirrors NanoClaw's ``decideStuckAction`` split.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent.session.directory import list_sessions
from sovereign_agent.session.state import now_utc

log = logging.getLogger(__name__)

# Filename for the heartbeat sentinel inside ``sessions_dir``. Dotfile so the
# `entry.name.startswith("sess_")` filter in ``list_sessions()`` already
# skips it — no chance of the heartbeat being mistaken for a session dir.
HEARTBEAT_FILENAME = ".orchestrator_heartbeat"


@dataclass(frozen=True)
class SessionSnapshot:
    """Read-only view of a session's liveness-relevant fields.

    Decouples ``_decide_stalled`` from ``Session`` so tests can build
    synthetic inputs without instantiating sessions on disk.
    """

    session_id: str
    state: str
    created_at: datetime
    last_event_at: datetime | None


@dataclass(frozen=True)
class StalledSession:
    """One stalled session, ready for trace emission.

    ``last_event_age_s`` is the age (in seconds) of the most recent trace
    event, or of ``created_at`` when the session has no trace events yet.
    """

    session_id: str
    state: str
    last_event_age_s: float


def _decide_stalled(
    snapshots: list[SessionSnapshot],
    *,
    stall_threshold_s: float,
    now: datetime,
) -> list[StalledSession]:
    """Pure: which sessions are stalled at ``now``?

    A session is stalled when ``now - max(last_event_at, created_at)`` exceeds
    ``stall_threshold_s``. Terminal sessions are skipped here belt-and-braces;
    ``_scan_once`` also pre-filters them, but having the rule in one place
    is cheap and lets ``_decide_stalled`` be safely reused.

    Convention over configuration (your call from the design phase): there
    is no separate grace period for "just created" — ``created_at`` is the
    floor when no trace events have landed yet. A session that was created
    but never dispatched still gets flagged once it crosses the threshold,
    which is the correct behaviour (it IS stalled).
    """
    from sovereign_agent.session.state import TERMINAL_STATES

    stalled: list[StalledSession] = []
    for snap in snapshots:
        if snap.state in TERMINAL_STATES:
            continue
        floor = snap.last_event_at or snap.created_at
        age_s = (now - floor).total_seconds()
        if age_s > stall_threshold_s:
            stalled.append(
                StalledSession(
                    session_id=snap.session_id,
                    state=snap.state,
                    last_event_age_s=age_s,
                )
            )
    return stalled


def _last_trace_event_at(trace_path: Path) -> datetime | None:
    """Read the timestamp of the last trace event, or None if no events.

    Best-effort: parse failures and missing files both return None.
    Walks lines (vs. seek-from-end) for simplicity; trace.jsonl files in
    v0.3 are small enough that the cost is negligible against the 60s
    poll interval.
    """
    if not trace_path.exists():
        return None
    last_ts: str | None = None
    try:
        with open(trace_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    # Tolerate a truncated final line from a crash mid-write —
                    # mirrors the same survivability iter_inbox_events uses.
                    continue
                ts = event.get("timestamp")
                if isinstance(ts, str):
                    last_ts = ts
    except OSError:
        return None
    if last_ts is None:
        return None
    try:
        return datetime.fromisoformat(last_ts)
    except ValueError:
        return None


class LivenessMonitor:
    """Async subsystem that scans sessions for stalls and writes a heartbeat.

    Peer of ``IpcWatcher`` / ``DriftCorrectedScheduler`` / ``AutoApprover``:
    same ``__init__`` / ``run`` / ``shutdown`` contract, so the orchestrator
    wires it in alongside the other subsystems without special-casing.

    The heartbeat is written on every tick:

      * First tick of a process: ``atomic_write_json`` writes ``{pid,
        started_at}``. Content + mtime both land.
      * Subsequent ticks: ``os.utime(path, None)`` bumps the mtime only.
        Content stays static — readers care about mtime, not body.

    If ``enabled`` is False, ``run`` returns immediately. Same shape as
    the M2 ``AutoApprover``: the toggle is honoured at start, not by
    blocking the task loop. ``shutdown`` is safe on a never-started
    instance.
    """

    def __init__(
        self,
        *,
        sessions_dir: Path,
        stall_threshold_s: float,
        poll_interval_s: float,
        enabled: bool = True,
    ) -> None:
        self.sessions_dir = sessions_dir
        self.stall_threshold_s = float(stall_threshold_s)
        self.poll_interval_s = float(poll_interval_s)
        self.enabled = enabled
        self._running = False
        self._started_at = now_utc()
        self._heartbeat_written = False

    async def run(self) -> None:
        if not self.enabled:
            log.debug("LivenessMonitor disabled; run() returning")
            return
        self._running = True
        log.info(
            "LivenessMonitor started (threshold=%ss, poll=%ss)",
            self.stall_threshold_s,
            self.poll_interval_s,
        )
        try:
            while self._running:
                try:
                    self._write_heartbeat()
                    await self._scan_once()
                except Exception:  # noqa: BLE001
                    # A scan tick must never take down the subsystem — the
                    # orchestrator relies on us continuing to emit signals
                    # even when individual sessions have malformed traces.
                    log.exception("LivenessMonitor scan tick failed; continuing")
                await asyncio.sleep(self.poll_interval_s)
        finally:
            self._running = False

    async def shutdown(self) -> None:
        # Safe to call even if run() never started. Mirrors AutoApprover's
        # pattern so ``Orchestrator.shutdown`` doesn't need a guard.
        self._running = False

    def _write_heartbeat(self) -> None:
        """Refresh the heartbeat file's mtime; write content on first tick.

        The two-mode pattern (full write first, then `utime`) matches
        NanoClaw's heartbeat: static content + fresh mtime is the signal.
        Cheap (one syscall after the first tick) and atomic by construction
        — no observer can see a partially-written body because the body
        never changes.
        """
        path = self.sessions_dir / HEARTBEAT_FILENAME
        if not self._heartbeat_written:
            try:
                atomic_write_json(
                    path,
                    {"pid": os.getpid(), "started_at": self._started_at.isoformat()},
                )
                self._heartbeat_written = True
            except OSError:
                log.exception("LivenessMonitor: heartbeat initial write failed")
            return
        try:
            os.utime(path, None)
        except FileNotFoundError:
            # Heartbeat got deleted out from under us (operator cleanup,
            # test teardown). Re-arm by clearing the flag — next tick
            # will rewrite content.
            self._heartbeat_written = False
        except OSError:
            log.exception("LivenessMonitor: heartbeat mtime bump failed")

    async def _scan_once(self) -> list[StalledSession]:
        """One scan tick: snapshot sessions, decide stalled, emit events.

        Returns the stalled list so callers (tests, future health
        endpoints) can introspect a single tick without a second pass.
        """
        snapshots = self._collect_snapshots()
        now = now_utc()
        stalled = _decide_stalled(
            snapshots,
            stall_threshold_s=self.stall_threshold_s,
            now=now,
        )
        for s in stalled:
            self._emit_stalled(s, now=now)
        return stalled

    def _collect_snapshots(self) -> list[SessionSnapshot]:
        snapshots: list[SessionSnapshot] = []
        for session in list_sessions(sessions_dir=self.sessions_dir):
            if session.state.is_terminal():
                continue
            last_at = _last_trace_event_at(session.trace_path)
            snapshots.append(
                SessionSnapshot(
                    session_id=session.session_id,
                    state=session.state.state,
                    created_at=session.state.created_at,
                    last_event_at=last_at,
                )
            )
        return snapshots

    def _emit_stalled(self, stalled: StalledSession, *, now: datetime) -> None:
        # Reload the session by id to write the trace event — the snapshot
        # we have is read-only, and we don't keep handles across the
        # collection phase to keep the pure decision clean.
        from sovereign_agent.session.directory import load_session

        try:
            session = load_session(stalled.session_id, sessions_dir=self.sessions_dir)
        except Exception:  # noqa: BLE001
            # Session disappeared mid-tick (e.g. operator deleted it).
            # Nothing to emit against; skip quietly.
            log.debug("LivenessMonitor: session %s vanished before emit", stalled.session_id)
            return
        session.append_trace_event(
            {
                "event_type": "liveness.session_stalled",
                "actor": "liveness_monitor",
                "timestamp": now.isoformat(),
                "payload": {
                    "session_id": stalled.session_id,
                    "state": stalled.state,
                    "last_event_age_s": stalled.last_event_age_s,
                },
            }
        )
        log.info(
            "liveness.session_stalled: %s (state=%s, age=%.1fs)",
            stalled.session_id,
            stalled.state,
            stalled.last_event_age_s,
        )


__all__ = [
    "HEARTBEAT_FILENAME",
    "LivenessMonitor",
    "SessionSnapshot",
    "StalledSession",
]
