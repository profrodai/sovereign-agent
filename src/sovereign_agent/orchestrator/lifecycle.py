"""Provider-independent worker execution lifecycle.

The lifecycle deliberately knows nothing about agent providers.  It moves an
immutable request through a backend, records forward-only state transitions,
and gives cancellation and timeout failures stable terminal reasons.
"""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from sovereign_agent.contracts import CapabilityManifest, ExecutionId, FrozenDict
from sovereign_agent.contracts._core import freeze_json


class LifecycleState(StrEnum):
    CREATED = "created"
    PREPARING = "preparing"
    PREPARED = "prepared"
    EXECUTING = "executing"
    CLOSING = "closing"
    TERMINATED = "terminated"


class TerminalReason(StrEnum):
    SUCCEEDED = "succeeded"
    ABORTED = "aborted"
    IDLE_TIMEOUT = "idle-timeout"
    COMPLETION_TIMEOUT = "completion-timeout"
    WORKER_TIMEOUT = "worker-timeout"
    PROVIDER_TIMEOUT = "provider-timeout"
    LIFECYCLE_TIMEOUT = "lifecycle-timeout"
    PROVIDER_ERROR = "provider-error"
    WORKER_ERROR = "worker-error"
    ISOLATION_UNAVAILABLE = "isolation-unavailable"
    INVALID_STRUCTURED_OUTPUT = "invalid-structured-output"
    VERIFICATION_FAILED = "verification-failed"
    DELIVERY_FAILED = "delivery-failed"
    BUSINESS_VERIFICATION_FAILED = "business-verification-failed"


@dataclass(frozen=True)
class LifecycleTimeouts:
    prepare_s: float | None = None
    execute_s: float | None = None
    close_s: float | None = 5.0
    lifecycle_s: float | None = None
    idle_s: float | None = None
    completion_s: float | None = None
    force_teardown_s: float = 2.0

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")


@dataclass(frozen=True)
class WorkerRequest:
    execution_id: ExecutionId
    session_id: str
    session_dir: Path
    require_filesystem_isolation: bool = False
    require_network_isolation: bool = False
    preserve_on_failure: bool = False
    credential_allowlist: tuple[str, ...] = ()
    environment_allowlist: tuple[str, ...] = ()
    timeouts: LifecycleTimeouts = field(default_factory=LifecycleTimeouts)
    metadata: FrozenDict = field(default_factory=FrozenDict)

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise TypeError("execution_id must be ExecutionId")
        if not self.session_id:
            raise ValueError("session_id must not be empty")
        object.__setattr__(self, "session_dir", Path(self.session_dir))
        object.__setattr__(self, "credential_allowlist", tuple(self.credential_allowlist))
        object.__setattr__(self, "environment_allowlist", tuple(self.environment_allowlist))
        object.__setattr__(self, "metadata", freeze_json(self.metadata))


@dataclass(frozen=True)
class InvocationSpec:
    command: tuple[str, ...] = ()
    environment: Mapping[str, str] = field(default_factory=dict)
    cwd: Path | None = None
    stdin: bytes | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "command", tuple(self.command))
        object.__setattr__(self, "environment", dict(self.environment))
        if self.cwd is not None:
            object.__setattr__(self, "cwd", Path(self.cwd))


@dataclass
class RuntimeHandle:
    request: WorkerRequest
    invocation: InvocationSpec
    handle_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: dict[str, Any] = field(default_factory=dict, repr=False)
    closed: bool = False


@dataclass(frozen=True)
class ExecResult:
    returncode: int | None
    stdout: str = ""
    stderr: str = ""
    value: Any = None
    started: bool = True
    terminal_reason: TerminalReason | None = None

    @property
    def succeeded(self) -> bool:
        return self.terminal_reason is None and (self.returncode in (None, 0))


@dataclass(frozen=True)
class CloseResult:
    closed: bool
    preserved: bool = False
    forced: bool = False
    detail: str = ""


@runtime_checkable
class WorkerBackend(Protocol):
    name: str

    def capabilities(self) -> CapabilityManifest: ...

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle: ...

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult: ...

    async def close(self, handle: RuntimeHandle, preserve: bool = False) -> CloseResult: ...


class CancellationToken:
    """Execution-local cooperative cancellation signal."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        self._event.set()

    async def wait(self) -> None:
        await self._event.wait()


@dataclass(frozen=True)
class LifecycleTransition:
    state: LifecycleState
    monotonic_s: float


@dataclass(frozen=True)
class LifecycleResult:
    execution_id: ExecutionId
    reason: TerminalReason
    exec_result: ExecResult | None
    close_result: CloseResult | None
    transitions: tuple[LifecycleTransition, ...]
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.reason is TerminalReason.SUCCEEDED


async def run_step[T](
    awaitable: Awaitable[T],
    *,
    timeout_s: float | None,
    timeout_reason: TerminalReason,
) -> T:
    """Run one lifecycle step with a stable, inspectable timeout reason."""
    try:
        if timeout_s is None:
            return await awaitable
        return await asyncio.wait_for(awaitable, timeout=timeout_s)
    except TimeoutError as exc:
        raise LifecycleStepTimeout(timeout_reason) from exc


class LifecycleStepTimeout(TimeoutError):
    def __init__(self, reason: TerminalReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


class ExecutionLifecycle:
    """Independent, reusable, forward-only backend lifecycle runner."""

    def __init__(self) -> None:
        self._tokens: dict[ExecutionId, CancellationToken] = {}

    def cancel(self, execution_id: ExecutionId) -> bool:
        token = self._tokens.get(execution_id)
        if token is None:
            return False
        token.cancel()
        return True

    async def run(
        self,
        backend: WorkerBackend,
        request: WorkerRequest,
        invocation: InvocationSpec | None = None,
    ) -> LifecycleResult:
        token = CancellationToken()
        if request.execution_id in self._tokens:
            raise ValueError(f"execution {request.execution_id} is already active")
        self._tokens[request.execution_id] = token
        transitions: list[LifecycleTransition] = []

        async def _run_inner() -> LifecycleResult:
            handle: RuntimeHandle | None = None
            exec_result: ExecResult | None = None
            close_result: CloseResult | None = None
            reason = TerminalReason.WORKER_ERROR
            error: str | None = None

            def move(state: LifecycleState) -> None:
                if transitions and list(LifecycleState).index(state) <= list(LifecycleState).index(
                    transitions[-1].state
                ):
                    raise RuntimeError("lifecycle transitions must move forward")
                transitions.append(LifecycleTransition(state, time.monotonic()))

            move(LifecycleState.CREATED)
            try:
                move(LifecycleState.PREPARING)
                handle = await self._cancel_aware(
                    lambda: backend.prepare(request),
                    token,
                    timeout_s=request.timeouts.prepare_s,
                    timeout_reason=TerminalReason.WORKER_TIMEOUT,
                    cancellation_grace_s=request.timeouts.force_teardown_s,
                )
                move(LifecycleState.PREPARED)
                if token.cancelled:
                    reason = TerminalReason.ABORTED
                else:
                    move(LifecycleState.EXECUTING)
                    exec_result = await self._cancel_aware(
                        lambda: backend.execute(handle, invocation),
                        token,
                        timeout_s=request.timeouts.execute_s,
                        timeout_reason=TerminalReason.WORKER_TIMEOUT,
                        cancellation_grace_s=request.timeouts.force_teardown_s,
                    )
                    reason = exec_result.terminal_reason or (
                        TerminalReason.SUCCEEDED
                        if exec_result.succeeded
                        else TerminalReason.WORKER_ERROR
                    )
            except asyncio.CancelledError:
                reason = TerminalReason.ABORTED
            except LifecycleStepTimeout as exc:
                reason = exc.reason
                error = str(exc)
            except Exception as exc:  # noqa: BLE001
                reason = getattr(exc, "terminal_reason", TerminalReason.WORKER_ERROR)
                error = f"{type(exc).__name__}: {exc}"
            finally:
                if handle is not None:
                    move(LifecycleState.CLOSING)
                    preserve = (
                        request.preserve_on_failure and reason is not TerminalReason.SUCCEEDED
                    )
                    close_result = await self._bounded_close(
                        backend, handle, preserve, request.timeouts
                    )
                move(LifecycleState.TERMINATED)
            return LifecycleResult(
                execution_id=request.execution_id,
                reason=reason,
                exec_result=exec_result,
                close_result=close_result,
                transitions=tuple(transitions),
                error=error,
            )

        try:
            if request.timeouts.lifecycle_s is None:
                return await _run_inner()
            lifecycle_task = asyncio.create_task(_run_inner())
            done, _ = await asyncio.wait({lifecycle_task}, timeout=request.timeouts.lifecycle_s)
            if done:
                return await lifecycle_task
            token.cancel()
            partial = await lifecycle_task
            return LifecycleResult(
                execution_id=request.execution_id,
                reason=TerminalReason.LIFECYCLE_TIMEOUT,
                exec_result=partial.exec_result,
                close_result=partial.close_result,
                transitions=partial.transitions,
                error=TerminalReason.LIFECYCLE_TIMEOUT.value,
            )
        finally:
            self._tokens.pop(request.execution_id, None)

    async def _cancel_aware[T](
        self,
        factory: Callable[[], Awaitable[T]],
        token: CancellationToken,
        *,
        timeout_s: float | None,
        timeout_reason: TerminalReason,
        cancellation_grace_s: float,
    ) -> T:
        # The backend coroutine is constructed inside this owned task, so an
        # immediate parent cancellation cannot strand an un-awaited coroutine.
        task: asyncio.Future[T] = asyncio.ensure_future(factory())
        cancelled = asyncio.create_task(token.wait())
        waiting: set[asyncio.Future[Any]] = {task, cancelled}
        done, _ = await asyncio.wait(
            waiting,
            timeout=timeout_s,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if task in done:
            cancelled.cancel()
            return await task
        cancelled.cancel()
        task.cancel()
        stopped, _ = await asyncio.wait({task}, timeout=cancellation_grace_s)
        if task in stopped:
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:  # noqa: BLE001
                pass
        else:
            # A backend that suppresses cancellation must not hold the lifecycle
            # open forever. Its close hook gets the opportunity to terminate the
            # underlying process; consume any eventual task exception quietly.
            task.add_done_callback(_consume_task_result)
        if cancelled in done:
            raise asyncio.CancelledError
        raise LifecycleStepTimeout(timeout_reason)

    async def _bounded_close(
        self,
        backend: WorkerBackend,
        handle: RuntimeHandle,
        preserve: bool,
        timeouts: LifecycleTimeouts,
    ) -> CloseResult:
        close_task = asyncio.create_task(backend.close(handle, preserve))
        done, _ = await asyncio.wait({close_task}, timeout=timeouts.close_s)
        if close_task in done:
            try:
                return await close_task
            except Exception:  # noqa: BLE001
                pass
        else:
            close_task.cancel()
            close_task.add_done_callback(_consume_task_result)
        try:
            force = handle.state.get("force_close")
            if callable(force):
                value = force()
                if inspect.isawaitable(value):
                    try:
                        await asyncio.wait_for(value, timeout=timeouts.force_teardown_s)
                    except (TimeoutError, Exception):  # noqa: BLE001
                        pass
        finally:
            handle.closed = True
        return CloseResult(closed=True, preserved=False, forced=True, detail="forced teardown")


def _consume_task_result(task: asyncio.Future[Any]) -> None:
    """Prevent warnings if a non-cooperative backend task eventually exits."""
    try:
        task.result()
    except (asyncio.CancelledError, Exception):  # noqa: BLE001
        pass


__all__ = [
    "CancellationToken",
    "CloseResult",
    "ExecResult",
    "ExecutionLifecycle",
    "InvocationSpec",
    "LifecycleResult",
    "LifecycleState",
    "LifecycleStepTimeout",
    "LifecycleTimeouts",
    "LifecycleTransition",
    "RuntimeHandle",
    "TerminalReason",
    "WorkerBackend",
    "WorkerRequest",
    "run_step",
]
