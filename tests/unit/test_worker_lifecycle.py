from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

from sovereign_agent.contracts import EvidenceLevel, ExecutionId
from sovereign_agent.orchestrator.lifecycle import (
    CloseResult,
    ExecResult,
    ExecutionLifecycle,
    InvocationSpec,
    LifecycleState,
    LifecycleTimeouts,
    RuntimeHandle,
    TerminalReason,
    WorkerRequest,
)
from sovereign_agent.orchestrator.worker import (
    BareWorker,
    DockerWorker,
    OSIsolatedWorker,
    SubprocessWorker,
)


def request(tmp_path: Path, **kwargs: object) -> WorkerRequest:
    return WorkerRequest(
        execution_id=ExecutionId("exec-test"),
        session_id="sess-test",
        session_dir=tmp_path,
        **kwargs,  # type: ignore[arg-type]
    )


class RecordingBackend:
    name = "recording"

    def __init__(self, *, delay: float = 0, result: ExecResult | None = None) -> None:
        self.delay = delay
        self.result = result or ExecResult(returncode=0)
        self.preserve: bool | None = None

    def capabilities(self):  # type: ignore[no-untyped-def]
        async def advance(_sid: str, _path: Path):  # type: ignore[no-untyped-def]
            raise AssertionError

        return BareWorker(advance).capabilities()

    async def prepare(self, item: WorkerRequest) -> RuntimeHandle:
        return RuntimeHandle(item, InvocationSpec())

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        del handle, invocation
        await asyncio.sleep(self.delay)
        return self.result

    async def close(self, handle: RuntimeHandle, preserve: bool = False) -> CloseResult:
        self.preserve = preserve
        handle.closed = True
        return CloseResult(closed=True, preserved=preserve)


@pytest.mark.asyncio
async def test_lifecycle_is_forward_only(tmp_path: Path) -> None:
    result = await ExecutionLifecycle().run(RecordingBackend(), request(tmp_path))
    assert result.reason is TerminalReason.SUCCEEDED
    assert [item.state for item in result.transitions] == [
        LifecycleState.CREATED,
        LifecycleState.PREPARING,
        LifecycleState.PREPARED,
        LifecycleState.EXECUTING,
        LifecycleState.CLOSING,
        LifecycleState.TERMINATED,
    ]


@pytest.mark.asyncio
async def test_per_execution_cancellation_closes_worker(tmp_path: Path) -> None:
    lifecycle = ExecutionLifecycle()
    item = request(tmp_path)
    task = asyncio.create_task(lifecycle.run(RecordingBackend(delay=30), item))
    await asyncio.sleep(0.01)
    assert lifecycle.cancel(item.execution_id)
    result = await asyncio.wait_for(task, timeout=1)
    assert result.reason is TerminalReason.ABORTED
    assert result.close_result is not None and result.close_result.closed


@pytest.mark.asyncio
async def test_worker_timeout_and_preserve_policy(tmp_path: Path) -> None:
    backend = RecordingBackend(delay=30)
    item = request(
        tmp_path,
        preserve_on_failure=True,
        timeouts=LifecycleTimeouts(execute_s=0.01),
    )
    result = await ExecutionLifecycle().run(backend, item)
    assert result.reason is TerminalReason.WORKER_TIMEOUT
    assert backend.preserve is True


@pytest.mark.parametrize(
    "reason",
    [
        TerminalReason.IDLE_TIMEOUT,
        TerminalReason.COMPLETION_TIMEOUT,
        TerminalReason.PROVIDER_TIMEOUT,
        TerminalReason.PROVIDER_ERROR,
        TerminalReason.WORKER_ERROR,
        TerminalReason.INVALID_STRUCTURED_OUTPUT,
        TerminalReason.VERIFICATION_FAILED,
        TerminalReason.DELIVERY_FAILED,
        TerminalReason.BUSINESS_VERIFICATION_FAILED,
    ],
)
@pytest.mark.asyncio
async def test_backend_terminal_reasons_remain_distinct(
    tmp_path: Path, reason: TerminalReason
) -> None:
    backend = RecordingBackend(
        result=ExecResult(returncode=None, terminal_reason=reason),
    )

    result = await ExecutionLifecycle().run(backend, request(tmp_path))

    assert result.reason is reason
    assert result.exec_result is not None
    assert result.exec_result.terminal_reason is reason


@pytest.mark.asyncio
async def test_lifecycle_timeout_is_distinct_from_worker_timeout(tmp_path: Path) -> None:
    item = request(
        tmp_path,
        timeouts=LifecycleTimeouts(lifecycle_s=0.01, force_teardown_s=0.01),
    )

    result = await ExecutionLifecycle().run(RecordingBackend(delay=30), item)

    assert result.reason is TerminalReason.LIFECYCLE_TIMEOUT
    assert result.error == TerminalReason.LIFECYCLE_TIMEOUT.value


@pytest.mark.asyncio
async def test_close_timeout_forces_bounded_teardown(tmp_path: Path) -> None:
    force_called = False

    class SlowCloseBackend(RecordingBackend):
        async def prepare(self, item: WorkerRequest) -> RuntimeHandle:
            handle = await super().prepare(item)

            def force_close() -> None:
                nonlocal force_called
                force_called = True

            handle.state["force_close"] = force_close
            return handle

        async def close(self, handle: RuntimeHandle, preserve: bool = False) -> CloseResult:
            del handle, preserve
            await asyncio.sleep(30)
            return CloseResult(closed=True)

    item = request(
        tmp_path,
        timeouts=LifecycleTimeouts(close_s=0.01, force_teardown_s=0.01),
    )

    result = await ExecutionLifecycle().run(SlowCloseBackend(), item)

    assert result.reason is TerminalReason.SUCCEEDED
    assert result.close_result is not None and result.close_result.forced
    assert force_called is True


@pytest.mark.asyncio
async def test_noncooperative_backend_cannot_hold_lifecycle_open(tmp_path: Path) -> None:
    release = asyncio.Event()

    class NoncooperativeBackend(RecordingBackend):
        async def execute(
            self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
        ) -> ExecResult:
            del handle, invocation
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                await release.wait()
            return ExecResult(returncode=0)

    item = request(
        tmp_path,
        timeouts=LifecycleTimeouts(execute_s=0.01, force_teardown_s=0.01),
    )
    result = await asyncio.wait_for(
        ExecutionLifecycle().run(NoncooperativeBackend(), item),
        timeout=0.25,
    )
    assert result.reason is TerminalReason.WORKER_TIMEOUT
    release.set()
    await asyncio.sleep(0)


def test_all_distinct_terminal_reasons_are_present() -> None:
    expected = {
        "aborted",
        "idle-timeout",
        "completion-timeout",
        "worker-timeout",
        "lifecycle-timeout",
        "provider-error",
        "worker-error",
        "isolation-unavailable",
        "invalid-structured-output",
        "verification-failed",
        "delivery-failed",
        "business-verification-failed",
    }
    assert expected <= {item.value for item in TerminalReason}


def test_subprocess_environment_is_allowlisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UNIT3_SECRET", "secret-value")
    monkeypatch.setenv("UNIT3_UNRELATED", "must-not-leak")
    worker = SubprocessWorker(credential_allowlist=("UNIT3_SECRET",))
    env = worker._environment_for(request(tmp_path))  # noqa: SLF001
    assert env["UNIT3_SECRET"] == "secret-value"
    assert "UNIT3_UNRELATED" not in env


@pytest.mark.asyncio
async def test_subprocess_redacts_allowed_credential(tmp_path: Path) -> None:
    worker = SubprocessWorker(credential_allowlist=("UNIT3_SECRET",))
    item = request(tmp_path, credential_allowlist=("UNIT3_SECRET",))
    handle = RuntimeHandle(
        item,
        InvocationSpec(
            command=(sys.executable, "-c", "print('secret-value')"),
            environment={"UNIT3_SECRET": "secret-value"},
        ),
    )
    result = await worker.execute(handle)
    assert "secret-value" not in result.stdout
    assert "[REDACTED]" in result.stdout
    await worker.close(handle)


@pytest.mark.asyncio
async def test_subprocess_redacts_backend_declared_credential(tmp_path: Path) -> None:
    worker = SubprocessWorker(credential_allowlist=("UNIT3_SECRET",))
    item = request(tmp_path)
    handle = RuntimeHandle(
        item,
        InvocationSpec(
            command=(sys.executable, "-c", "print('secret-value')"),
            environment={"UNIT3_SECRET": "secret-value"},
        ),
    )
    result = await worker.execute(handle)
    assert "secret-value" not in result.stdout
    assert "[REDACTED]" in result.stdout
    await worker.close(handle)


@pytest.mark.asyncio
async def test_process_only_worker_fails_closed_for_isolation(tmp_path: Path) -> None:
    worker = SubprocessWorker()
    item = request(tmp_path, require_filesystem_isolation=True)
    result = await ExecutionLifecycle().run(worker, item)
    assert result.reason is TerminalReason.ISOLATION_UNAVAILABLE


@pytest.mark.asyncio
async def test_landlock_fails_closed_for_network_isolation(tmp_path: Path) -> None:
    class LandlockStub:
        name = "landlock"

        def wrap_command(self, command, *, allowed_paths, allow_network):  # type: ignore[no-untyped-def]
            return command, {}

    worker = OSIsolatedWorker(SubprocessWorker(), isolation_policy=LandlockStub())
    item = request(tmp_path, require_network_isolation=True)
    result = await ExecutionLifecycle().run(worker, item)
    assert result.reason is TerminalReason.ISOLATION_UNAVAILABLE
    capability = worker.capabilities().get("network_isolation")
    assert capability is not None
    assert capability.evidence_level is EvidenceLevel.ENFORCED
    assert not capability.is_available()


@pytest.mark.asyncio
async def test_docker_refuses_during_prepare(tmp_path: Path) -> None:
    result = await ExecutionLifecycle().run(DockerWorker(), request(tmp_path))
    assert result.reason is TerminalReason.ISOLATION_UNAVAILABLE
    assert result.exec_result is None


def test_diagnostics_do_not_mutate_parent_environment(tmp_path: Path) -> None:
    before = dict(os.environ)
    SubprocessWorker()._environment_for(request(tmp_path))  # noqa: SLF001
    assert dict(os.environ) == before
