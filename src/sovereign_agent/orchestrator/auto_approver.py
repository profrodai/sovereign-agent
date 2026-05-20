"""v0.3 Module 2 — engage-mode-aware auto-approver.

Turns `Config.engage_mode` into behaviour. The subsystem watches every
session's `ipc/awaiting_approval/` directory and applies a policy:

  - interactive : do nothing. A human must call `sovereign-agent approvals
                  grant/deny` (or write the decision file directly). This
                  is the default and preserves v0.2 behaviour exactly —
                  the loop in `run()` returns immediately.
  - autonomous  : auto-grant every pending request with approver
                  `auto:engage_mode_autonomous`. The audit trail is
                  identical to a human grant; you can grep `approver:
                  auto:*` to find every approval the bot gave itself.
  - silent      : auto-grant exactly like autonomous. The visible
                  difference between silent and autonomous is decided
                  elsewhere — in the orchestrator's `_deliver_channel_
                  response`, which suppresses outbound replies for silent.

Why a separate subsystem rather than a hook inside the executor?

  * The executor doesn't need to know engage_mode. It writes its
    approval request to the file system and exits, exactly as in v0.2.
    Auto-approval is then orchestration-layer policy applied
    out-of-band — a different concern at a different layer.
  * Decoupling means the policy can grow (rate limits, allowlists,
    per-tool overrides) without touching the executor.
  * The file system is the contract, so we can test the approver
    against a session directory without spinning up an orchestrator,
    an LLM, or a real tool.

The polling implementation is deliberately simple. Production systems
might use inotify / FSEvents / kqueue; we don't, because this is
teaching code and the polling latency (default 1s) is unobservable
against the timescales of real LLM-driven sessions.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)

# Repeated at module level so callers can type-check what they pass in
# without importing Config. Keep in sync with Config.engage_mode.
EngageMode = Literal["interactive", "autonomous", "silent"]


class AutoApprover:
    """Polls awaiting_approval/ across all sessions and applies the
    engage_mode policy. Designed to live as one of the orchestrator's
    subtasks alongside the IpcWatcher and the scheduler.

    `interactive` mode short-circuits: `run()` returns immediately so
    we don't even spin a polling loop. This keeps the v0.2 behaviour
    bit-identical when no engage_mode is configured.
    """

    def __init__(
        self,
        *,
        sessions_dir: Path,
        engage_mode: EngageMode,
        poll_interval_s: float = 1.0,
    ) -> None:
        self.sessions_dir = Path(sessions_dir)
        self.engage_mode = engage_mode
        self.poll_interval_s = poll_interval_s
        self._running = False

    async def run(self) -> None:
        if self.engage_mode == "interactive":
            log.debug("AutoApprover noop (engage_mode=interactive)")
            return
        self._running = True
        log.info("AutoApprover starting (engage_mode=%s)", self.engage_mode)
        try:
            while self._running:
                try:
                    await self._scan_once()
                except Exception:  # noqa: BLE001
                    # A bad request file or a transient FS error must not
                    # kill the loop; the next iteration will see the same
                    # files (or, after a real fix, won't).
                    log.exception("AutoApprover scan failed; will retry")
                await asyncio.sleep(self.poll_interval_s)
        finally:
            log.info("AutoApprover stopped")

    async def shutdown(self) -> None:
        self._running = False

    async def _scan_once(self) -> None:
        if not self.sessions_dir.exists():
            return
        for sess_dir in self.sessions_dir.iterdir():
            if not sess_dir.is_dir() or not sess_dir.name.startswith("sess_"):
                continue
            awaiting = sess_dir / "ipc" / "awaiting_approval"
            if not awaiting.is_dir():
                continue
            for request_file in sorted(awaiting.glob("*.json")):
                await self._auto_decide_one(sess_dir.name, request_file)

    async def _auto_decide_one(self, session_id: str, request_file: Path) -> None:
        # Lazy imports keep the test boundary small: tests for this
        # class don't pay the cost of importing the orchestrator or
        # the LLM client just to assert on file movements.
        from sovereign_agent.ipc.approval import (
            build_auto_decision,
            get_pending_approval,
            record_decision,
        )
        from sovereign_agent.session.directory import load_session

        try:
            session = load_session(session_id, sessions_dir=self.sessions_dir)
        except Exception:  # noqa: BLE001
            log.exception("auto-approver: failed to load %s", session_id)
            return
        request = get_pending_approval(session, request_file.stem)
        if request is None:
            # Race: file disappeared between iterdir() and this call.
            # Benign — the next scan won't see it either.
            return
        response = build_auto_decision(request, self.engage_mode)
        if response is None:
            # interactive policy. Defensive — we shouldn't reach here
            # because run() exits early in interactive mode, but a
            # subclass might call _scan_once() in interactive mode and
            # we should still do the right thing.
            return
        try:
            record_decision(session, response)
        except Exception:  # noqa: BLE001
            log.exception(
                "auto-approver: failed to record decision for %s",
                request.request_id,
            )


__all__ = ["AutoApprover", "EngageMode"]
