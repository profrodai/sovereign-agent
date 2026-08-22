"""Worker backends (v0.2, Module 2 foundation).

## Why this exists

In v0.1.0, when the orchestrator wanted to drive a session through its
ReAct loop, it called `executor.execute()` directly — in the same
process, same Python interpreter, same filesystem view. This is simple
for teaching, but it has the problems the class transcript keeps
surfacing:

  * Tenant isolation is only as strong as Python's import system.
    A misbehaving tool can read any file the process can read.
  * A runaway loop that hogs CPU or RAM takes the orchestrator with it.
  * Scaling out across hosts means distributing Python runtimes, not
    just shipping a container.

The orchestrator should not care HOW a session gets worked on. It
should tell SOMEONE to advance the session, then wait for artifacts
to appear on disk (tickets, handoff files, session_complete). That
"someone" is a worker backend.

## The protocols

    class WorkerBackend(Protocol):
        async def prepare(self, request: WorkerRequest) -> RuntimeHandle: ...
        async def execute(self, handle: RuntimeHandle, invocation: InvocationSpec | None) -> ExecResult: ...
        async def close(self, handle: RuntimeHandle, preserve: bool) -> CloseResult: ...

The v0.2 ``run_session`` surface remains available through a compatibility
adapter. Correctness guarantees come from the session directory contract, not
from backend-owned orchestration state.

## Built-in backends

  BareWorker         — runs in-process via existing DefaultExecutor.
                       Same behaviour as v0.1.0. Default.
  SubprocessWorker   — process separation only; it does not claim filesystem
                       or network isolation.
  OSIsolatedWorker   — composes SubprocessWorker with a proven Landlock or
                       sandbox-exec policy and fails closed when requested
                       enforcement cannot be demonstrated.
  DockerWorker       — NOT IMPLEMENTED. A stub defined below that
                       satisfies the Protocol so the 'docker' config
                       value constructs, then raises
                       NotImplementedError from run_session(). There is
                       no docker_worker module, no Dockerfile, and no
                       container code path anywhere in this repository.

Users pick via `Config.worker_backend`. Scenarios can override
per-invocation. Tests use `BareWorker` by default. Anyone reaching for
'docker' wants 'subprocess'.

## What a backend MUST do

  1. Advance the session through exactly one "step" — typically one
     planner call followed by one executor call.
  2. Write all state changes through the Session directory APIs. No
     smuggling state via return values, env vars, or stdout.
  3. Return a WorkerOutcome that summarises what happened, so the
     orchestrator can log and re-enqueue as needed.
  4. Honour the `_close` sentinel and timeouts. A backend that doesn't
     exit when asked is a bug.

## What a backend MUST NOT do

  * Hold state across calls. Every call re-reads the session's current
    state from disk.
  * Reach into the orchestrator's memory. The only shared state is the
    session directory.
  * Depend on its own network ingress. The worker reaches out; nothing
    reaches in.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sovereign_agent.contracts import (
    Capability,
    CapabilityManifest,
    EvidenceLevel,
    ExecutionId,
    FrozenDict,
)
from sovereign_agent.contracts.redaction import REDACTED, redact_text
from sovereign_agent.orchestrator.lifecycle import (
    CloseResult,
    ExecResult,
    ExecutionLifecycle,
    InvocationSpec,
    LifecycleTimeouts,
    RuntimeHandle,
    TerminalReason,
    WorkerBackend,
    WorkerRequest,
)

log = logging.getLogger(__name__)


def _emit_worker_timeout(
    *,
    session_id: str,
    session_dir: Path,
    backend: str,
    pid: int | None,
    elapsed_s: float | None,
) -> None:
    """v0.3 Module 4b: append a liveness.worker_timeout trace event.

    Best-effort. Failures are logged and swallowed — the caller's
    WorkerOutcome already reflects the timeout, and we don't want a trace
    write failure to mask the original signal.
    """
    try:
        from sovereign_agent.session.directory import load_session
        from sovereign_agent.session.state import now_utc

        session = load_session(session_id, sessions_dir=session_dir.parent)
        session.append_trace_event(
            {
                "event_type": "liveness.worker_timeout",
                "actor": "worker",
                "timestamp": now_utc().isoformat(),
                "payload": {
                    "session_id": session_id,
                    "backend": backend,
                    "pid": pid,
                    "elapsed_s": elapsed_s,
                },
            }
        )
    except Exception:  # noqa: BLE001
        log.exception("failed to emit liveness.worker_timeout for %s", session_id)


@dataclass
class WorkerOutcome:
    """Result of one worker step.

    Fields:
      session_id: the session that was advanced.
      terminal: True if the session reached a terminal state during
        this step (completed/failed/escalated) — the orchestrator
        will not re-enqueue.
      advanced: True if the worker changed the session's state or
        produced new artifacts. False means "I looked at the session
        and there was nothing to do" (idle tick).
      summary: one-line human-readable description of the step.
      raw: backend-specific extra payload (timings, container id,
        exit code). Do NOT rely on its shape.
    """

    session_id: str
    terminal: bool
    advanced: bool
    summary: str
    raw: dict = field(default_factory=dict)


def _manifest(**values: tuple[bool | None, EvidenceLevel]) -> CapabilityManifest:
    return CapabilityManifest(
        capabilities=FrozenDict(
            tuple(
                (name, Capability(available=available, evidence_level=evidence))
                for name, (available, evidence) in values.items()
            )
        )
    )


class IsolationUnavailable(RuntimeError):
    terminal_reason = TerminalReason.ISOLATION_UNAVAILABLE


async def run_session_compat(
    backend: Any,
    session_id: str,
    session_dir: Path,
    *,
    timeout_s: float | None = None,
) -> WorkerOutcome:
    """Adapt the v0.2 ``run_session`` call to the Unit 3 lifecycle.

    Third-party v0.2 backends are still accepted and called directly. Built-in
    and Unit 3 backends take the new prepare/execute/close route.
    """
    if not isinstance(backend, WorkerBackend):
        return await backend.run_session(session_id, session_dir, timeout_s=timeout_s)
    request = WorkerRequest(
        execution_id=ExecutionId(f"{session_id}:worker"),
        session_id=session_id,
        session_dir=session_dir,
        timeouts=LifecycleTimeouts(execute_s=timeout_s),
    )
    result = await ExecutionLifecycle().run(backend, request)
    if result.exec_result is not None and isinstance(result.exec_result.value, WorkerOutcome):
        return result.exec_result.value
    if result.reason in {
        TerminalReason.WORKER_TIMEOUT,
        TerminalReason.LIFECYCLE_TIMEOUT,
        TerminalReason.COMPLETION_TIMEOUT,
        TerminalReason.IDLE_TIMEOUT,
    }:
        return WorkerOutcome(
            session_id=session_id,
            terminal=False,
            advanced=False,
            summary=f"{backend.name} worker timed out",
            raw={"timeout": True, "terminal_reason": result.reason.value},
        )
    execution = result.exec_result
    if execution is not None and execution.returncode == 0:
        terminal = False
        advanced = False
        summary = "subprocess exited 0"
        if execution.stdout.strip():
            last = execution.stdout.strip().splitlines()[-1]
            try:
                payload = json.loads(last)
                if isinstance(payload, dict):
                    terminal = bool(payload.get("terminal", False))
                    advanced = bool(payload.get("advanced", False))
                    summary = str(payload.get("summary", summary))
            except json.JSONDecodeError:
                summary = last
        return WorkerOutcome(
            session_id=session_id,
            terminal=terminal,
            advanced=advanced,
            summary=summary,
            raw={
                "returncode": execution.returncode,
                "stdout_tail": execution.stdout[-2000:],
                "stderr_tail": execution.stderr[-2000:],
            },
        )
    detail = result.error or (execution.stderr if execution is not None else result.reason.value)
    return WorkerOutcome(
        session_id=session_id,
        terminal=False,
        advanced=False,
        summary=f"{backend.name} worker failed: {detail}",
        raw={"terminal_reason": result.reason.value},
    )


# ---------------------------------------------------------------------------
# BareWorker — v0.1.0 behaviour, preserved as the default
# ---------------------------------------------------------------------------


class BareWorker:
    """Runs the session step in-process.

    This is what v0.1.0 did implicitly. We give it a name now so that
    "no isolation" is a choice, not an assumption. Useful for teaching,
    debugging, and tests where a fresh process per step would be too
    slow.

    Use Config.worker_backend='bare' (the default) to get this.
    """

    name = "bare"

    def __init__(
        self,
        advance_fn: Callable[[str, Path], Awaitable[WorkerOutcome]],
    ) -> None:
        """advance_fn is an async callable ``(session_id, session_dir) -> WorkerOutcome``.

        The orchestrator builds the callable from its own state-dispatch
        code and hands it to the worker. This lets us decouple "what a
        step does" from "where the step runs".
        """
        self._advance_fn = advance_fn

    def capabilities(self) -> CapabilityManifest:
        return _manifest(
            process_isolation=(False, EvidenceLevel.ENFORCED),
            filesystem_isolation=(False, EvidenceLevel.ENFORCED),
            network_isolation=(False, EvidenceLevel.ENFORCED),
        )

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        if request.require_filesystem_isolation or request.require_network_isolation:
            raise IsolationUnavailable("BareWorker cannot enforce requested isolation")
        return RuntimeHandle(request=request, invocation=InvocationSpec())

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        del invocation
        outcome = await self._advance_fn(
            handle.request.session_id,
            handle.request.session_dir,
        )
        return ExecResult(returncode=0, value=outcome)

    async def run_session(
        self,
        session_id: str,
        session_dir: Path,
        *,
        timeout_s: float | None = None,
    ) -> WorkerOutcome:
        coro = self._advance_fn(session_id, session_dir)
        if timeout_s is None:
            return await coro
        try:
            return await asyncio.wait_for(coro, timeout=timeout_s)
        except TimeoutError:
            # v0.3 Module 4b: surface worker timeouts as trace events for the
            # operator/monitor. Best-effort — the outcome still reflects the
            # timeout even if trace emission fails.
            _emit_worker_timeout(
                session_id=session_id,
                session_dir=session_dir,
                backend="bare",
                pid=None,
                elapsed_s=timeout_s,
            )
            return WorkerOutcome(
                session_id=session_id,
                terminal=False,
                advanced=False,
                summary=f"bare worker timed out after {timeout_s}s",
                raw={"timeout": True},
            )

    async def close(
        self, handle: RuntimeHandle | None = None, preserve: bool = False
    ) -> CloseResult:
        del preserve
        if handle is not None:
            handle.closed = True
        return CloseResult(closed=True)


# ---------------------------------------------------------------------------
# SubprocessWorker — OS process isolation, no Docker required
# ---------------------------------------------------------------------------


class SubprocessWorker:
    """Runs the session step in a separate Python process via
    `python -m sovereign_agent.orchestrator.worker_entrypoint`.

    The subprocess inherits just enough environment to find the same
    sovereign-agent install and the session's LLM credentials. Session
    state is exchanged via the session directory — the subprocess reads
    and writes files there, and its exit code tells us whether the step
    succeeded.

    v0.2 Module 2 addition: optional `isolation_policy`. When set, the
    subprocess is launched through an IsolationPolicy that wraps it in
    Landlock (Linux) or sandbox-exec (macOS) with a filesystem
    allow-list consisting of:

      * The session directory (read-write)
      * The Python runtime and site-packages (read-only)
      * /etc/resolv.conf and other read-only system paths the runtime needs

    See sovereign_agent._internal.isolation for available policies and
    detect_best_policy() to pick the right one automatically.

    Trade-offs compared to BareWorker:

      + OS-level isolation: a segfault or runaway import doesn't take
        the orchestrator down.
      + With isolation_policy, filesystem isolation is kernel-enforced.
      + Same isolation guarantees as Docker without the daemon.
      - Adds ~100-300ms fork overhead per step.
      - Without an isolation_policy, shares the host filesystem outside
        the session directory.

    Use Config.worker_backend='subprocess' to opt in.
    """

    name = "subprocess"

    def __init__(
        self,
        *,
        python_executable: str | None = None,
        extra_env: dict[str, str] | None = None,
        isolation_policy: Any = None,
        extra_allowed_paths: list[Path] | None = None,
        allow_network: bool = True,
        credential_allowlist: tuple[str, ...] = (),
        environment_allowlist: tuple[str, ...] = (),
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.extra_env = extra_env or {}
        # IsolationPolicy is optional. If None, runs unconfined (same as
        # v0.1.0 behaviour). Scenarios that need confinement should pass
        # sovereign_agent._internal.isolation.detect_best_policy().
        self.isolation_policy = isolation_policy
        # Extra read-only paths the child needs access to. Typically
        # includes sys.prefix (Python runtime) and site-packages. If
        # not provided and isolation is active, we auto-discover them.
        self._extra_allowed_paths = extra_allowed_paths
        self.allow_network = allow_network
        self.credential_allowlist = tuple(credential_allowlist)
        self.environment_allowlist = tuple(environment_allowlist)

    def capabilities(self) -> CapabilityManifest:
        return _manifest(
            process_isolation=(True, EvidenceLevel.PROBED),
            filesystem_isolation=(False, EvidenceLevel.ENFORCED),
            network_isolation=(False, EvidenceLevel.ENFORCED),
        )

    def _environment_for(self, request: WorkerRequest) -> dict[str, str]:
        """Build a child environment without inheriting the parent wholesale."""
        baseline_names = (
            "PATH",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "TZ",
            "TMPDIR",
            "TEMP",
            "TMP",
            "SYSTEMROOT",
            "WINDIR",
            "PYTHONPATH",
            "PYTHONHOME",
            "VIRTUAL_ENV",
        )
        env = {name: os.environ[name] for name in baseline_names if name in os.environ}
        allowed = (
            set(self.credential_allowlist)
            | set(self.environment_allowlist)
            | set(request.credential_allowlist)
            | set(request.environment_allowlist)
        )
        env.update({name: os.environ[name] for name in allowed if name in os.environ})
        env.update(self.extra_env)
        return env

    def _invocation_for(self, request: WorkerRequest) -> InvocationSpec:
        return InvocationSpec(
            command=(
                self.python_executable,
                "-m",
                "sovereign_agent.orchestrator.worker_entrypoint",
                "--session-id",
                request.session_id,
                "--session-dir",
                str(request.session_dir),
            ),
            environment=self._environment_for(request),
        )

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        if request.require_filesystem_isolation or request.require_network_isolation:
            raise IsolationUnavailable(
                "SubprocessWorker provides process separation only; use OSIsolatedWorker"
            )
        return RuntimeHandle(request=request, invocation=self._invocation_for(request))

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        spec = invocation or handle.invocation
        try:
            proc = await asyncio.create_subprocess_exec(
                *spec.command,
                env=dict(spec.environment),
                cwd=str(spec.cwd) if spec.cwd is not None else None,
                stdin=asyncio.subprocess.PIPE if spec.stdin is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            return ExecResult(
                returncode=None,
                stderr=str(exc),
                started=False,
                terminal_reason=TerminalReason.WORKER_ERROR,
            )
        handle.state["process"] = proc
        handle.state["force_close"] = proc.kill
        stdout, stderr = await proc.communicate(spec.stdin)
        stdout_text = self._redact_diagnostic(
            stdout.decode("utf-8", errors="replace"), spec.environment, handle.request
        )
        stderr_text = self._redact_diagnostic(
            stderr.decode("utf-8", errors="replace"), spec.environment, handle.request
        )
        return ExecResult(
            returncode=proc.returncode,
            stdout=stdout_text,
            stderr=stderr_text,
            terminal_reason=(None if proc.returncode == 0 else TerminalReason.WORKER_ERROR),
        )

    def _redact_diagnostic(
        self, text: str, environment: Mapping[str, str], request: WorkerRequest
    ) -> str:
        redacted = redact_text(text)
        credential_names = set(self.credential_allowlist) | set(request.credential_allowlist)
        for name in credential_names:
            value = environment.get(name)
            if value:
                redacted = redacted.replace(value, REDACTED)
        return redacted

    def _default_readonly_paths(self) -> list[Path]:
        """Paths every Python child needs read access to. Covers the
        interpreter, stdlib, and common site-packages locations.

        This is the allow-list that makes the sandbox usable at all —
        without these, `import os` would fail under Landlock.
        """
        import site
        import sysconfig

        paths: set[Path] = set()
        # Python runtime
        paths.add(Path(sys.prefix))
        if hasattr(sys, "base_prefix"):
            paths.add(Path(sys.base_prefix))
        # Stdlib + ext modules + site-packages
        for key in ("stdlib", "purelib", "platlib", "include"):
            try:
                p = sysconfig.get_path(key)
                if p:
                    paths.add(Path(p))
            except KeyError:
                pass
        for sp in site.getsitepackages():
            paths.add(Path(sp))
        if hasattr(site, "getusersitepackages"):
            paths.add(Path(site.getusersitepackages()))
        # Common system paths the runtime reads
        for p in ("/etc/resolv.conf", "/etc/hosts", "/etc/ssl/certs", "/usr/share/ca-certificates"):
            pp = Path(p)
            if pp.exists():
                paths.add(pp)
        # Resolve and deduplicate.
        return sorted({p.resolve() for p in paths if p.exists()})

    async def run_session(
        self,
        session_id: str,
        session_dir: Path,
        *,
        timeout_s: float | None = None,
    ) -> WorkerOutcome:
        request = WorkerRequest(
            execution_id=ExecutionId(f"{session_id}:worker"),
            session_id=session_id,
            session_dir=session_dir,
            credential_allowlist=self.credential_allowlist,
            environment_allowlist=self.environment_allowlist,
        )
        env = self._environment_for(request)

        raw_command = [
            self.python_executable,
            "-m",
            "sovereign_agent.orchestrator.worker_entrypoint",
            "--session-id",
            session_id,
            "--session-dir",
            str(session_dir),
        ]

        # Apply isolation if configured. The policy is pure: it returns
        # a wrapped command and any extra env. We honour both.
        if self.isolation_policy is not None:
            allowed = [session_dir.resolve()]
            if self._extra_allowed_paths is not None:
                allowed.extend(p.resolve() for p in self._extra_allowed_paths)
            else:
                allowed.extend(self._default_readonly_paths())
            args, extra_env = self.isolation_policy.wrap_command(
                raw_command,
                allowed_paths=allowed,
                allow_network=self.allow_network,
            )
            env.update(extra_env)
            log.debug(
                "isolation policy %r wrapping command (%d allow paths)",
                self.isolation_policy.name,
                len(allowed),
            )
        else:
            args = raw_command

        log.debug("spawning subprocess worker: %s", args)

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            return WorkerOutcome(
                session_id=session_id,
                terminal=False,
                advanced=False,
                summary=f"subprocess spawn failed: {exc}",
                raw={"error": str(exc)},
            )

        try:
            if timeout_s is not None:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            else:
                stdout, stderr = await proc.communicate()
        except TimeoutError:
            proc.kill()
            await proc.wait()
            # v0.3 Module 4b: surface worker timeouts as trace events for the
            # operator/monitor. Best-effort — we have proc.pid here since the
            # process was alive long enough to time out.
            _emit_worker_timeout(
                session_id=session_id,
                session_dir=session_dir,
                backend="subprocess",
                pid=proc.pid,
                elapsed_s=timeout_s,
            )
            return WorkerOutcome(
                session_id=session_id,
                terminal=False,
                advanced=False,
                summary=f"subprocess worker timed out after {timeout_s}s",
                raw={"timeout": True},
            )

        stdout_text = (
            self._redact_diagnostic(stdout.decode("utf-8", errors="replace"), env, request)
            if stdout
            else ""
        )
        stderr_text = (
            self._redact_diagnostic(stderr.decode("utf-8", errors="replace"), env, request)
            if stderr
            else ""
        )

        # Convention: the worker entrypoint writes a WorkerOutcome-shaped
        # JSON line as its LAST line of stdout. If it didn't, we fall
        # back to an exit-code-based outcome.
        summary_line = ""
        terminal = False
        advanced = False
        if stdout_text.strip():
            last = stdout_text.strip().splitlines()[-1]
            # We parse defensively — if it isn't JSON, treat as free text.
            try:
                payload = json.loads(last)
                if isinstance(payload, dict):
                    terminal = bool(payload.get("terminal", False))
                    advanced = bool(payload.get("advanced", False))
                    summary_line = str(payload.get("summary", ""))
            except json.JSONDecodeError:
                summary_line = last

        if proc.returncode == 0:
            return WorkerOutcome(
                session_id=session_id,
                terminal=terminal,
                advanced=advanced,
                summary=summary_line or "subprocess exited 0",
                raw={
                    "returncode": proc.returncode,
                    "stdout_tail": stdout_text[-2000:],
                    "stderr_tail": stderr_text[-2000:],
                },
            )
        return WorkerOutcome(
            session_id=session_id,
            terminal=False,
            advanced=False,
            summary=(
                f"subprocess exited {proc.returncode}: "
                f"{(stderr_text or summary_line or '').splitlines()[-1] if stderr_text or summary_line else 'no stderr'}"
            ),
            raw={
                "returncode": proc.returncode,
                "stdout_tail": stdout_text[-2000:],
                "stderr_tail": stderr_text[-2000:],
            },
        )

    async def close(
        self, handle: RuntimeHandle | None = None, preserve: bool = False
    ) -> CloseResult:
        if handle is None:
            return CloseResult(closed=True)
        proc = handle.state.get("process")
        forced = False
        if proc is not None and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=1.0)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                forced = True
        handle.closed = True
        return CloseResult(closed=True, preserved=preserve, forced=forced)


# ---------------------------------------------------------------------------
# OSIsolatedWorker — native policy composed over a process worker
# ---------------------------------------------------------------------------


class OSIsolatedWorker(SubprocessWorker):
    """Compose a process-only worker with Landlock or sandbox-exec."""

    # Keep the v0.2 operator-facing backend name while exposing the distinct
    # implementation type.
    name = "subprocess"

    def __init__(
        self,
        process_worker: SubprocessWorker | None = None,
        *,
        isolation_policy: Any,
        extra_allowed_paths: list[Path] | None = None,
        allow_network: bool = True,
    ) -> None:
        self.process_worker = process_worker or SubprocessWorker()
        super().__init__(
            python_executable=self.process_worker.python_executable,
            extra_env=self.process_worker.extra_env,
            isolation_policy=isolation_policy,
            extra_allowed_paths=extra_allowed_paths,
            allow_network=allow_network,
            credential_allowlist=self.process_worker.credential_allowlist,
            environment_allowlist=self.process_worker.environment_allowlist,
        )

    def capabilities(self) -> CapabilityManifest:
        policy_name = getattr(self.isolation_policy, "name", "unknown")
        filesystem = policy_name in {"landlock", "sandbox-exec"}
        network = policy_name == "sandbox-exec"
        return _manifest(
            process_isolation=(True, EvidenceLevel.PROBED),
            filesystem_isolation=(filesystem, EvidenceLevel.ENFORCED),
            network_isolation=(network, EvidenceLevel.ENFORCED),
        )

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        capabilities = self.capabilities()
        if request.require_filesystem_isolation and not (
            capabilities.is_available("filesystem_isolation")
            and capabilities.has_evidence("filesystem_isolation", EvidenceLevel.ENFORCED)
        ):
            raise IsolationUnavailable("filesystem isolation cannot be proven")
        if request.require_network_isolation and not (
            capabilities.is_available("network_isolation")
            and capabilities.has_evidence("network_isolation", EvidenceLevel.ENFORCED)
        ):
            raise IsolationUnavailable("network isolation cannot be proven")

        invocation = self.process_worker._invocation_for(request)
        allowed = [request.session_dir.resolve()]
        if self._extra_allowed_paths is not None:
            allowed.extend(path.resolve() for path in self._extra_allowed_paths)
        else:
            allowed.extend(self._default_readonly_paths())
        command, policy_env = self.isolation_policy.wrap_command(
            list(invocation.command),
            allowed_paths=allowed,
            allow_network=not request.require_network_isolation and self.allow_network,
        )
        environment = dict(invocation.environment)
        environment.update(policy_env)
        return RuntimeHandle(
            request=request,
            invocation=InvocationSpec(
                command=tuple(command),
                environment=environment,
                cwd=invocation.cwd,
                stdin=invocation.stdin,
            ),
        )

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        return await self.process_worker.execute(handle, invocation)

    async def close(
        self, handle: RuntimeHandle | None = None, preserve: bool = False
    ) -> CloseResult:
        return await self.process_worker.close(handle, preserve)


# ---------------------------------------------------------------------------
# DockerWorker — UNIMPLEMENTED STUB (slot reserved; no container code exists)
# ---------------------------------------------------------------------------


class DockerWorker:
    """UNIMPLEMENTED STUB. Reserves the WorkerBackend slot; raises on use.

    Docker-based isolation does not exist in this repository. There is no
    container image, no Dockerfile, and no bind-mount logic — only this
    class, and it raises.

    The stub exists so the operator-facing config knob ('bare' /
    'subprocess' / 'docker') maps cleanly to three classes and so that
    selecting 'docker' fails with a clear NotImplementedError at
    run_session() rather than a confusing AttributeError or a
    missing-class import error at construction.

    The supported isolated backend is SubprocessWorker, which gets
    kernel-enforced filesystem isolation from Landlock (Linux >= 5.13)
    or sandbox-exec (macOS) without a container runtime.

    The `docker` pip extra installs the Docker SDK but is deliberately
    excluded from the `all` meta-extra, because installing a dependency
    for a code path that does not exist advertises a capability the
    library does not have.
    """

    name = "docker"

    def __init__(self, **kwargs: Any) -> None:
        del kwargs
        log.warning(
            "DockerWorker is an unimplemented stub; no container code path "
            "exists. SubprocessWorker is the supported isolated backend. Set "
            "worker_backend='subprocess' for kernel-level isolation."
        )

    def capabilities(self) -> CapabilityManifest:
        return _manifest(
            process_isolation=(False, EvidenceLevel.PROBED),
            filesystem_isolation=(False, EvidenceLevel.PROBED),
            network_isolation=(False, EvidenceLevel.PROBED),
            available=(False, EvidenceLevel.PROBED),
        )

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        del request
        raise IsolationUnavailable(
            "DockerWorker is unavailable; invocation was refused before preparation"
        )

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        del handle, invocation
        raise NotImplementedError("DockerWorker is unavailable")

    async def run_session(
        self,
        session_id: str,
        session_dir: Path,
        *,
        timeout_s: float | None = None,
    ) -> WorkerOutcome:
        raise NotImplementedError(
            "DockerWorker is not implemented; there is no container code path in "
            "sovereign-agent. Use worker_backend='subprocess' for OS-level "
            "isolation (Landlock on Linux >=5.13, sandbox-exec on macOS)."
        )

    async def close(
        self, handle: RuntimeHandle | None = None, preserve: bool = False
    ) -> CloseResult:
        del preserve
        if handle is not None:
            handle.closed = True
        return CloseResult(closed=True)


__all__ = [
    "BareWorker",
    "DockerWorker",
    "OSIsolatedWorker",
    "SubprocessWorker",
    "WorkerBackend",
    "WorkerOutcome",
    "IsolationUnavailable",
]
