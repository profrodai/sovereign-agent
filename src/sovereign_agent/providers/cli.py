"""Shared execution and probing machinery for native command-line providers."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from sovereign_agent.contracts import EvidenceLevel, FrozenDict
from sovereign_agent.contracts._core import thaw_json
from sovereign_agent.orchestrator.lifecycle import (
    ExecResult,
    ExecutionLifecycle,
    InvocationSpec,
    LifecycleTimeouts,
    WorkerBackend,
    WorkerRequest,
)
from sovereign_agent.orchestrator.worker import SubprocessWorker

from .events import (
    ProviderEventType,
    StructuredResultEvent,
    TextEvent,
    WarningEvent,
    utc_now,
)
from .models import InvocationRequest, InvocationResult, ProviderCapabilities
from .observers import EventFanout, ObserverFailure
from .protocol import EventCallback


class ProviderUnavailable(RuntimeError):
    """Raised before invocation when a requested CLI feature is unproven."""


@dataclass(frozen=True)
class ProbeEvidence:
    executable: str
    version: str | None
    version_stdout: str
    version_stderr: str
    help_stdout: str
    help_stderr: str
    capabilities: ProviderCapabilities


class CliProvider(ABC):
    """A CLI provider executed exclusively through the Unit 3 lifecycle seam."""

    kind: ClassVar[str] = "provider"
    credential_names: ClassVar[tuple[str, ...]] = ()
    environment_names: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        *,
        executable: str,
        name: str,
        backend: WorkerBackend | None = None,
        lifecycle: ExecutionLifecycle | None = None,
        environment: Mapping[str, str] | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.executable = executable
        self.name = name
        self.backend = backend or SubprocessWorker(credential_allowlist=self.credential_names)
        self.lifecycle = lifecycle or ExecutionLifecycle()
        self.environment = (
            dict(environment) if environment is not None else self._default_environment()
        )
        self.timeout_s = timeout_s
        self.capabilities = ProviderCapabilities(
            available=False, evidence_level=EvidenceLevel.UNKNOWN
        )
        self.probe_evidence: ProbeEvidence | None = None
        self.last_observer_failures: tuple[ObserverFailure, ...] = ()

    def _default_environment(self) -> dict[str, str]:
        names = {
            "PATH",
            "HOME",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "TERM",
            "TMPDIR",
            "TEMP",
            "TMP",
            *self.credential_names,
            *self.environment_names,
        }
        return {name: os.environ[name] for name in names if name in os.environ}

    @abstractmethod
    def version_spec(self) -> InvocationSpec:
        """Return the side-effect-free version probe."""

    @abstractmethod
    def help_spec(self) -> InvocationSpec:
        """Return the side-effect-free invocation help probe."""

    @abstractmethod
    def capabilities_from_probe(
        self, version: ExecResult, help_result: ExecResult
    ) -> ProviderCapabilities:
        """Derive only capabilities evidenced by probe output."""

    @abstractmethod
    def invocation_spec(self, request: InvocationRequest) -> InvocationSpec:
        """Build an argv/environment invocation without executing it."""

    @abstractmethod
    def parse_output(self, stdout: str, request: InvocationRequest) -> list[ProviderEventType]:
        """Parse documented provider output into normalized immutable events."""

    async def probe(self, request: InvocationRequest) -> ProbeEvidence:
        version = await self._execute(request, self.version_spec())
        help_result = await self._execute(request, self.help_spec())
        capabilities = self.capabilities_from_probe(version, help_result)
        version_text = (version.stdout or version.stderr).strip().splitlines()
        evidence = ProbeEvidence(
            executable=self.executable,
            version=version_text[0] if version_text and version.succeeded else None,
            version_stdout=version.stdout,
            version_stderr=version.stderr,
            help_stdout=help_result.stdout,
            help_stderr=help_result.stderr,
            capabilities=capabilities,
        )
        self.capabilities = capabilities
        self.probe_evidence = evidence
        return evidence

    async def invoke(
        self,
        request: InvocationRequest,
        *,
        observers: Sequence[EventCallback] = (),
        activity_callbacks: Sequence[EventCallback] = (),
    ) -> InvocationResult:
        if self.probe_evidence is None:
            await self.probe(request)
        self._refuse_unproven_features(request)
        execution = await self._execute(request, self.invocation_spec(request))
        events = self.parse_output(execution.stdout, request)
        if execution.stderr.strip():
            events.append(
                self._warning(
                    request,
                    len(events),
                    "provider_stderr",
                    execution.stderr.strip(),
                )
            )
        if not execution.succeeded:
            detail = execution.stderr.strip() or execution.terminal_reason or execution.returncode
            events.append(
                self._warning(
                    request,
                    len(events),
                    "provider_nonzero_exit",
                    f"provider invocation failed: {detail}",
                )
            )

        fanout = EventFanout(observers, activity_callbacks)
        for event in events:
            await fanout.emit(event)
        self.last_observer_failures = fanout.failures

        texts = [event.text for event in events if isinstance(event, TextEvent)]
        structured = [
            thaw_json(event.result) for event in events if isinstance(event, StructuredResultEvent)
        ]
        output: dict[str, Any] = {"final_answer": "".join(texts)}
        if structured:
            output["structured_result"] = structured[-1]
        success = execution.succeeded
        summary = output["final_answer"] or (
            "provider invocation completed" if success else "provider invocation failed"
        )
        return InvocationResult(
            success=success,
            output=FrozenDict(tuple(output.items())),
            summary=str(summary),
            next_action="complete" if success else "escalate",
            events=tuple(events),
        )

    async def _execute(self, request: InvocationRequest, spec: InvocationSpec) -> ExecResult:
        worker_request = WorkerRequest(
            execution_id=request.execution_id,
            session_id=request.session.session_id,
            session_dir=request.session.directory,
            credential_allowlist=self.credential_names,
            environment_allowlist=self.environment_names,
            timeouts=LifecycleTimeouts(execute_s=self.timeout_s),
        )
        result = await self.lifecycle.run(self.backend, worker_request, spec)
        if result.exec_result is not None:
            return result.exec_result
        return ExecResult(
            returncode=None,
            stderr=result.error or result.reason.value,
            started=False,
            terminal_reason=result.reason,
        )

    def _refuse_unproven_features(self, request: InvocationRequest) -> None:
        if (
            not self.capabilities.available
            or self.capabilities.evidence_level < EvidenceLevel.PROBED
        ):
            raise ProviderUnavailable(
                f"{self.name} executable/output mode was not proven by version and help probes"
            )
        if request.provider_session_id is not None and not self.capabilities.resume:
            raise ProviderUnavailable(f"{self.name} resume support was not proven")
        context = thaw_json(request.context)
        assert isinstance(context, dict)
        requested = {
            "tools": bool(context.get("require_tools")),
            "usage": bool(context.get("require_usage")),
            "structured_result": bool(context.get("require_structured_result")),
            "streaming": bool(context.get("require_streaming")),
        }
        for feature, required in requested.items():
            if required and not bool(getattr(self.capabilities, feature)):
                raise ProviderUnavailable(f"{self.name} capability {feature!r} is unavailable")

    def _warning(
        self, request: InvocationRequest, sequence: int, code: str, message: str
    ) -> WarningEvent:
        return WarningEvent(
            execution_id=request.execution_id,
            invocation_id=request.invocation_id,
            sequence=sequence,
            timestamp=utc_now(),
            code=code,
            message=message,
        )

    def spec(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        stdin: bytes | None = None,
    ) -> InvocationSpec:
        return InvocationSpec(
            command=tuple(command),
            environment=self.environment,
            cwd=cwd,
            stdin=stdin,
        )

    def working_directory(self, request: InvocationRequest) -> Path:
        """Use an admitted repository worktree when the execution engine supplies one."""
        context = thaw_json(request.context)
        assert isinstance(context, dict)
        configured = context.get("repository_worktree")
        if configured is None:
            return request.session.directory
        if not isinstance(configured, str):
            raise ProviderUnavailable("repository_worktree must be an absolute directory path")
        path = Path(configured)
        if not path.is_absolute() or path.is_symlink() or not path.is_dir():
            raise ProviderUnavailable(
                "repository_worktree must be an existing non-symlink absolute directory"
            )
        return path


__all__ = ["CliProvider", "ProbeEvidence", "ProviderUnavailable"]
