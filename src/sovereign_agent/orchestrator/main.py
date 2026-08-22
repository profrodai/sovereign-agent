"""Orchestrator: the long-running coordinator.

See docs/architecture.md §2.6. Wires together:

  - SessionQueue (decision 2/4/8)
  - IpcWatcher (decision 3)
  - DriftCorrectedScheduler (decision 6)
  - CredentialGateway (decision 5)

Plus state dispatch: for each session the queue assigns to us, read
session.json, look at `state`, and do the right thing next (run planner,
run executor, dispatch handoff, or mark terminal).
"""

from __future__ import annotations

import asyncio
import logging
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sovereign_agent._internal.llm_client import LLMClient, OpenAICompatibleClient
from sovereign_agent.config import Config
from sovereign_agent.contracts import ExecutionId, FrozenDict, InvocationId
from sovereign_agent.contracts._core import thaw_json
from sovereign_agent.errors import SovereignError, wrap_unexpected
from sovereign_agent.executor import DefaultExecutor
from sovereign_agent.ipc.watcher import IpcWatcher
from sovereign_agent.orchestrator.auto_approver import AutoApprover
from sovereign_agent.orchestrator.credentials import CredentialGateway
from sovereign_agent.orchestrator.liveness import LivenessMonitor
from sovereign_agent.orchestrator.worker import WorkerBackend, WorkerOutcome
from sovereign_agent.orchestrator.worker_factory import make_worker_backend
from sovereign_agent.planner import DefaultPlanner
from sovereign_agent.providers import InvocationRequest, NativeProvider
from sovereign_agent.scheduler.drift_corrected import DriftCorrectedScheduler
from sovereign_agent.session.directory import (
    Session,
    create_session,
    list_sessions,
    load_session,
)
from sovereign_agent.session.queue import SessionQueue
from sovereign_agent.session.state import now_utc
from sovereign_agent.tools.builtin import make_builtin_registry
from sovereign_agent.tools.registry import ToolRegistry

if TYPE_CHECKING:
    # WorkerOutcome is only imported inside advance_session_once() at
    # runtime to avoid a circular import (orchestrator.worker imports
    # from this module). TYPE_CHECKING makes the annotation legible to
    # static checkers without adding a runtime dep.
    from sovereign_agent.channels.adapter import ChannelAdapter
    from sovereign_agent.orchestrator.worker import WorkerOutcome

log = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """What `run_task()` returns to the caller."""

    session_id: str
    session_dir: Path
    success: bool
    summary: str
    output: dict


class Orchestrator:
    """Long-running coordinator. Owns queue, IPC watcher, scheduler."""

    def __init__(
        self,
        config: Config,
        *,
        llm_client: LLMClient | None = None,
        extra_tools: ToolRegistry | None = None,
        adapters: list[ChannelAdapter] | None = None,
    ) -> None:
        self.config = config
        self.credentials = CredentialGateway()
        self._llm_client = llm_client
        self._extra_tools = extra_tools
        self.queue = SessionQueue(max_concurrent=config.max_concurrent)
        self.queue.set_process_fn(self.process_session)
        self.watcher = IpcWatcher(
            sessions_dir=config.sessions_dir,
            on_complete=self._on_session_complete,
            on_handoff=self._on_handoff,
            poll_interval_s=config.poll_interval_s,
        )
        self.scheduler = DriftCorrectedScheduler(poll_interval_s=config.poll_interval_s)
        # v0.3 Module 2: engage-mode-aware auto-approver. A no-op in
        # 'interactive' mode; auto-grants every approval in 'autonomous'
        # and 'silent' modes (silent suppresses channel delivery instead).
        self.auto_approver = AutoApprover(
            sessions_dir=config.sessions_dir,
            engage_mode=config.engage_mode,
            poll_interval_s=config.poll_interval_s,
        )
        # v0.3 Module 4b: liveness monitor — peer of watcher/scheduler/auto_approver.
        # Emits liveness.session_stalled trace events when a session goes silent
        # past liveness_stall_threshold_s; maintains .orchestrator_heartbeat
        # under sessions_dir for external observers.
        self.liveness_monitor = LivenessMonitor(
            sessions_dir=config.sessions_dir,
            stall_threshold_s=config.liveness_stall_threshold_s,
            poll_interval_s=config.liveness_poll_interval_s,
            enabled=config.liveness_enabled,
        )
        self._running = False
        self._subtasks: list[asyncio.Task] = []
        # Session-scoped caches so repeated dispatches don't rebuild tools.
        self._per_session_tools: dict[str, ToolRegistry] = {}

        # v0.3 Module 1: channels. adapters=None means NO channels — a
        # bare Orchestrator, run_task(), and every v0.2 test path behave
        # exactly as before. `serve` / `chat` pass an explicit adapter
        # list. Imported lazily to keep the channels package optional.
        from sovereign_agent.channels.registry import ChannelRegistry
        from sovereign_agent.channels.router import InboundRouter

        self.channels = ChannelRegistry()
        self.router = InboundRouter(self.queue, sessions_dir=config.sessions_dir)
        for adapter in adapters or []:
            self.channels.register(adapter)

        # v0.3 Module 4a: build the worker backend the queue's dispatch
        # will route through. For worker_backend='subprocess' on a host
        # without a usable isolation primitive, this raises
        # SovereignError(code='SA_NO_SANDBOX_PRIMITIVE') — fail-loud so
        # an operator who asked for sandboxing never silently runs
        # unconfined.
        self._worker_backend = make_worker_backend(config, advance_fn=self._bare_advance)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def run(self) -> None:
        """The main loop. Runs until shutdown() is called (or SIGTERM)."""
        self._running = True
        self._install_signal_handlers()
        # Resume unfinished sessions from disk.
        await self._resume_on_startup()

        # v0.3 Module 1: start channel adapters (open sockets, connect bots).
        for adapter in self.channels.list():
            await adapter.setup(self.router)

        # Spawn subsystems.
        self._subtasks.append(asyncio.create_task(self.watcher.run()))
        self._subtasks.append(asyncio.create_task(self.scheduler.run()))
        # v0.3 Module 2: the auto-approver runs alongside other subsystems.
        self._subtasks.append(asyncio.create_task(self.auto_approver.run()))
        # v0.3 Module 4b: the liveness monitor runs alongside other subsystems.
        # No-op task if liveness_enabled=False (run() returns immediately).
        self._subtasks.append(asyncio.create_task(self.liveness_monitor.run()))
        try:
            while self._running:
                await asyncio.sleep(0.25)
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        if not self._running and not self._subtasks:
            return
        self._running = False
        await self.watcher.shutdown()
        await self.scheduler.shutdown()
        # v0.3 Module 2: stop the auto-approver before cancelling subtasks.
        await self.auto_approver.shutdown()
        # v0.3 Module 4b: stop the liveness monitor before cancelling subtasks.
        # Safe to call even if run() was a no-op (enabled=False).
        await self.liveness_monitor.shutdown()
        for t in self._subtasks:
            t.cancel()
        for t in self._subtasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        self._subtasks.clear()
        # v0.3 Module 1: stop channel adapters cleanly.
        for adapter in self.channels.list():
            try:
                await adapter.teardown()
            except Exception:  # noqa: BLE001
                log.exception("error tearing down channel adapter %s", adapter.name)
        await self.queue.shutdown(grace_period_s=5.0)

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()
        try:
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._on_signal(s)))
        except NotImplementedError:
            # Signal handlers don't work on all platforms (e.g. Windows).
            pass

    async def _on_signal(self, sig: signal.Signals) -> None:
        log.info("received %s; initiating graceful shutdown", sig.name)
        await self.shutdown()

    # ------------------------------------------------------------------
    # v0.3 Module 1: channel adapter management + reply delivery
    # ------------------------------------------------------------------
    async def add_adapter(self, adapter: ChannelAdapter) -> None:
        """Register and (if already running) start a channel adapter."""
        self.channels.register(adapter)
        if self._running:
            await adapter.setup(self.router)

    async def remove_adapter(self, name: str) -> None:
        """Stop and unregister a channel adapter without a restart."""
        if name not in self.channels:
            return
        adapter = self.channels.get(name)
        await adapter.teardown()
        self.channels.unregister(name)

    async def _deliver_channel_response(self, session: Session, result) -> None:
        """If `session` arrived via a channel, send the agent reply back.

        No-op for non-channel sessions (run_task, scripted demos), so
        v0.2 behaviour is untouched. The text is the loop half's final
        answer, falling back to its summary for non-complete outcomes.
        """
        target = self.router.reply_target_for(session.session_id)
        if target is None:
            return
        # v0.3 Module 2: engage_mode-aware delivery.
        #   silent      — never deliver (shadow mode)
        #   autonomous  — always deliver
        #   interactive — deliver only if the originating inbox event
        #                 was a mention. CLI always sets is_mention=True
        #                 so this is a no-op for CLI; group-chat adapters
        #                 get silent-until-@-mentioned for free.
        if self.config.engage_mode == "silent":
            log.info(
                "engage_mode=silent: suppressing channel reply for %s",
                session.session_id,
            )
            return
        if self.config.engage_mode == "interactive":
            events = list(session.iter_inbox_events())
            if events and not events[-1].get("is_mention", True):
                log.info(
                    "engage_mode=interactive: last inbox event not a "
                    "mention; suppressing reply for %s",
                    session.session_id,
                )
                return
        channel_type, platform_id, thread_id = target
        adapter = self.channels.for_channel_type(channel_type)
        if adapter is None:
            return
        from sovereign_agent.channels.adapter import OutboundMessage

        text = (result.output or {}).get("final_answer") or result.summary
        try:
            await adapter.deliver(platform_id, thread_id, OutboundMessage.text(text))
        except Exception:  # noqa: BLE001
            log.exception(
                "failed to deliver channel response for %s",
                session.session_id,
            )

    async def _resume_on_startup(self) -> None:
        sessions = list_sessions(sessions_dir=self.config.sessions_dir)
        resumed = 0
        for session in sessions:
            if session.state.is_terminal():
                continue
            state = session.state.state
            if state == "planning":
                await self.queue.enqueue_planner(session.session_id)
            elif state == "executing":
                await self.queue.enqueue_executor(session.session_id)
            elif state == "handed_off_to_structured":
                await self.queue.enqueue_handoff(session.session_id, "structured")
            elif state == "handed_off_to_research":
                await self.queue.enqueue_handoff(session.session_id, "research")
            resumed += 1
        if resumed:
            log.info("resumed %d session(s) from disk", resumed)

    # ------------------------------------------------------------------
    # Session dispatch (SessionQueue callback)
    # ------------------------------------------------------------------
    async def process_session(self, session_id: str) -> bool:
        """Called by SessionQueue. Routes the session through the configured
        worker backend (bare in-process, sandboxed subprocess, or future Docker).

        # v0.3 Module 4a: process_session routes through worker backend

        The actual step logic lives in advance_session_once (which the
        backends converge on). This method's only job is selecting the
        right backend for THIS session, running one step, and signalling
        the queue whether to re-enqueue.
        """
        try:
            session = load_session(session_id, sessions_dir=self.config.sessions_dir)
        except Exception:  # noqa: BLE001
            log.exception("failed to load session %s", session_id)
            return False

        backend = self._backend_for_session(session)
        try:
            outcome = await backend.run_session(session_id, session.directory)
        except SovereignError as exc:
            log.warning("session %s failed with %s: %s", session_id, exc.code, exc.message)
            try:
                session.mark_failed(f"{exc.code}: {exc.message}")
            except Exception:  # noqa: BLE001
                pass
            return False
        except Exception as exc:  # noqa: BLE001
            wrapped = wrap_unexpected(exc)
            log.exception("unexpected error processing session %s", session_id)
            try:
                session.mark_failed(f"{wrapped.code}: {wrapped.message}")
            except Exception:  # noqa: BLE001
                pass
            return False
        # outcome.terminal True means the session reached completed/failed/escalated.
        # outcome.advanced True means state changed and the queue should re-enqueue.
        return outcome.terminal or outcome.advanced

    # v0.3 Module 4a: helpers backing the WorkerBackend-routed dispatch.

    async def _bare_advance(self, session_id: str, session_dir: Path) -> WorkerOutcome:
        """The advance_fn BareWorker calls. Delegates to advance_session_once
        using THIS orchestrator's config / llm_client / extra_tools, not env
        defaults — so caller-supplied dependencies propagate correctly into
        the in-process step.
        """
        return await advance_session_once(
            session_id=session_id,
            session_dir=session_dir,
            config=self.config,
            llm_client=self._llm_client,
            extra_tools=self._extra_tools,
        )

    def _backend_for_session(self, session: Session) -> WorkerBackend:
        """Pick the WorkerBackend for THIS session.

        If `session.worker_backend` (read from config_overrides) is set
        and differs from `config.worker_backend`, build a one-off backend
        via the factory. Otherwise reuse the orchestrator's shared backend.

        Per-session overrides survive resumes — they live in session.json
        on disk, not in memory. A sandboxed session resumed from disk
        cannot accidentally come back under the bare backend.
        """
        override = session.worker_backend
        if override is None or override == self.config.worker_backend:
            return self._worker_backend
        import dataclasses

        override_config = dataclasses.replace(self.config, worker_backend=override)
        return make_worker_backend(override_config, advance_fn=self._bare_advance)

    async def _dispatch_loop_half(self, session: Session) -> bool:
        llm = self._ensure_llm_client()
        tools = self._tools_for(session)
        planner = DefaultPlanner(model=self.config.llm_planner_model, client=llm)
        executor = DefaultExecutor(model=self.config.llm_executor_model, client=llm, tools=tools)
        provider = NativeProvider(planner=planner, executor=executor)

        # Read the task from SESSION.md (simplest source) if present.
        task = _read_task_from_session_md(session)
        result = await provider.invoke(
            InvocationRequest(
                execution_id=ExecutionId(f"{session.session_id}:execution"),
                invocation_id=InvocationId(f"{session.session_id}:invocation"),
                task=task,
                session=session,
                context=FrozenDict(),
            )
        )

        # v0.3 Module 1: if this session arrived via a channel, send the
        # agent's reply back out. No-op for run_task / scripted sessions.
        await self._deliver_channel_response(session, result)

        if result.next_action == "complete":
            output = thaw_json(result.output)
            assert isinstance(output, dict)
            session.mark_complete(output)
            return True
        if result.next_action == "handoff_to_structured":
            session.update_state(state="handed_off_to_structured")
            return True
        if result.next_action == "escalate":
            session.mark_escalated(result.summary)
            return True
        return True

    async def _dispatch_structured_half(self, session: Session) -> bool:
        # Skeleton: the structured half has no default rules, so for now we
        # escalate rather than silently completing. Users override this
        # dispatch by subclassing Orchestrator or by registering structured
        # rules via a future entry point.
        session.mark_escalated(
            "handoff to structured half received, but no structured rules are registered"
        )
        return True

    def _ensure_llm_client(self) -> LLMClient:
        if self._llm_client is not None:
            return self._llm_client
        self._llm_client = OpenAICompatibleClient(
            base_url=self.config.llm_base_url,
            api_key_env=self.config.llm_api_key_env,
        )
        return self._llm_client

    def _tools_for(self, session: Session) -> ToolRegistry:
        cached = self._per_session_tools.get(session.session_id)
        if cached is not None:
            return cached
        reg = make_builtin_registry(session)
        if self._extra_tools is not None:
            for tool in self._extra_tools.list():
                reg.register(tool)
        self._per_session_tools[session.session_id] = reg
        return reg

    # ------------------------------------------------------------------
    # IpcWatcher callbacks
    # ------------------------------------------------------------------
    async def _on_session_complete(self, session_id: str, payload: dict) -> None:
        try:
            session = load_session(session_id, sessions_dir=self.config.sessions_dir)
        except Exception:  # noqa: BLE001
            return
        if not session.state.is_terminal():
            session.mark_complete(payload.get("result") or payload)

    async def _on_handoff(self, session_id: str, target_half: str, payload: dict) -> None:
        try:
            session = load_session(session_id, sessions_dir=self.config.sessions_dir)
        except Exception:  # noqa: BLE001
            return
        new_state = (
            "handed_off_to_structured"
            if target_half == "structured"
            else ("handed_off_to_research" if target_half == "research" else session.state.state)
        )
        try:
            session.update_state(
                state=new_state, handoff_history=session.state.handoff_history + [payload]
            )
        except Exception:  # noqa: BLE001
            log.exception("failed to update state on handoff for %s", session_id)
        if new_state == "handed_off_to_structured":
            await self.queue.enqueue_handoff(session_id, "structured")


def _read_task_from_session_md(session: Session) -> str:
    """Parse the 'Task description' section out of SESSION.md."""
    path = session.session_md_path
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    # Crude but serviceable: find "## Task description" then take until next "##".
    import re

    m = re.search(r"## Task description\s*\n(.*?)(?:\n## |\Z)", text, flags=re.DOTALL)
    if not m:
        return text.strip()
    return m.group(1).strip()


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------


def run_task(
    task: str,
    *,
    config: Config | None = None,
    scenario: str = "default",
    user_id: str | None = None,
    llm_client: LLMClient | None = None,
    extra_tools: ToolRegistry | None = None,
) -> TaskResult:
    """Create a session, run one task to completion, return the result.

    Synchronous wrapper around an async one-shot orchestrator. For
    long-running or multi-task deployments, instantiate Orchestrator
    directly and drive it yourself.
    """
    cfg = config or Config.from_env()
    session = create_session(
        scenario=scenario, task=task, user_id=user_id, sessions_dir=cfg.sessions_dir
    )

    async def _main() -> TaskResult:
        orch = Orchestrator(cfg, llm_client=llm_client, extra_tools=extra_tools)
        # Drive one session through to a terminal state.
        success = await orch.process_session(session.session_id)
        # Reload to get the final state.
        final = load_session(session.session_id, sessions_dir=cfg.sessions_dir)
        return TaskResult(
            session_id=session.session_id,
            session_dir=final.directory,
            success=success and final.state.is_terminal() and final.state.state != "failed",
            summary=_summary_from_state(final),
            output=final.state.result or {},
        )

    return asyncio.run(_main())


async def advance_session_once(
    session_id: str,
    session_dir: Path,
    *,
    config: Config | None = None,
    llm_client: LLMClient | None = None,
    extra_tools: ToolRegistry | None = None,
) -> WorkerOutcome:
    """Advance one session by one step.

    This is the function that all worker backends converge on. The
    in-process BareWorker calls it directly, SubprocessWorker calls it
    via `python -m sovereign_agent.orchestrator.worker_entrypoint`, and
    a future DockerWorker calls the same entrypoint inside a container.

    Semantics:
      * Loads the session at `session_dir` (session_id is redundant but
        kept for logging and for workers that can't cheaply derive it).
      * Looks at session.state and dispatches exactly one planner or
        executor or structured-half step.
      * Returns a WorkerOutcome summarising what happened.

    This helper does NOT loop. Callers choose whether to call it
    repeatedly. That decision belongs to the orchestrator, not the
    worker.
    """
    from sovereign_agent.orchestrator.worker import WorkerOutcome

    cfg = config or Config.from_env()
    # session_dir overrides the config's sessions_dir for this call —
    # workers know exactly where the session lives and should trust it
    # even if config.sessions_dir disagrees (e.g. a containerized worker
    # sees /workspace/session while the host sees /host/sessions/sess_xxx).
    sessions_root = session_dir.parent
    try:
        session = load_session(session_id, sessions_dir=sessions_root)
    except Exception as exc:  # noqa: BLE001
        return WorkerOutcome(
            session_id=session_id,
            terminal=False,
            advanced=False,
            summary=f"failed to load session: {exc}",
            raw={"error": str(exc)},
        )

    state_before = session.state.state
    if session.state.is_terminal():
        return WorkerOutcome(
            session_id=session_id,
            terminal=True,
            advanced=False,
            summary=f"session already terminal ({state_before})",
            raw={"state": state_before},
        )

    # Build an Orchestrator purely for its dispatch helpers. We do NOT
    # call its process_session() because that would recursively go
    # through the worker layer. Instead we call the internal dispatchers
    # directly — they're the unit of "one step".
    orch = Orchestrator(cfg, llm_client=llm_client, extra_tools=extra_tools)

    session.append_trace_event(
        {
            "event_type": "session.state_changed",
            "actor": "worker",
            "timestamp": now_utc().isoformat(),
            "payload": {"state": state_before, "step": "begin"},
        }
    )

    try:
        if state_before in ("planning", "executing"):
            await orch._dispatch_loop_half(session)  # noqa: SLF001
        elif state_before == "handed_off_to_structured":
            await orch._dispatch_structured_half(session)  # noqa: SLF001
        else:
            return WorkerOutcome(
                session_id=session_id,
                terminal=False,
                advanced=False,
                summary=f"unknown session state {state_before!r}; skipped",
                raw={"state": state_before},
            )
    except SovereignError as exc:
        session.mark_failed(f"{exc.code}: {exc.message}")
        return WorkerOutcome(
            session_id=session_id,
            terminal=True,
            advanced=True,
            summary=f"step failed: {exc.code}",
            raw={"error": exc.to_dict()},
        )
    except Exception as exc:  # noqa: BLE001
        wrapped = wrap_unexpected(exc)
        session.mark_failed(f"{wrapped.code}: {wrapped.message}")
        return WorkerOutcome(
            session_id=session_id,
            terminal=True,
            advanced=True,
            summary=f"step failed with unexpected error: {type(exc).__name__}",
            raw={"error": wrapped.to_dict()},
        )

    # Reload to see what the step wrote.
    session = load_session(session_id, sessions_dir=sessions_root)
    state_after = session.state.state
    return WorkerOutcome(
        session_id=session_id,
        terminal=session.state.is_terminal(),
        advanced=(state_after != state_before) or session.state.is_terminal(),
        summary=f"{state_before} -> {state_after}",
        raw={"state_before": state_before, "state_after": state_after},
    )


def _summary_from_state(session: Session) -> str:
    if session.state.state == "completed":
        r = session.state.result or {}
        return r.get("final_answer") or r.get("summary") or "completed"
    if session.state.state == "failed":
        r = session.state.result or {}
        return f"failed: {r.get('reason', 'unknown')}"
    if session.state.state == "escalated":
        r = session.state.result or {}
        return f"escalated: {r.get('reason', 'unknown')}"
    return f"session in state {session.state.state!r}"


__all__ = ["Orchestrator", "TaskResult", "advance_session_once", "run_task"]
