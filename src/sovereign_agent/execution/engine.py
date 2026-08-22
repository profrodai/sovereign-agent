"""Governed, durable composition of the v0.3 execution primitives."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
from collections.abc import Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sovereign_agent._internal.atomic import atomic_append_jsonl, atomic_write_bytes
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent.contracts import (
    CommitEvidence,
    EvidenceLevel,
    ExecutionId,
    ExecutionReceipt,
    FrozenDict,
    GovernedExecutionRequest,
    ReceiptStatus,
    ReceiptTermination,
    RelayMessageId,
    RepositoryReceipt,
    VerificationCommand,
    canonical_json_bytes,
    redact_json,
    redact_text,
)
from sovereign_agent.contracts._core import thaw_json
from sovereign_agent.orchestrator.lifecycle import (
    CloseResult,
    ExecResult,
    ExecutionLifecycle,
    LifecycleResult,
    LifecycleTimeouts,
    RuntimeHandle,
    TerminalReason,
    WorkerBackend,
    WorkerRequest,
)
from sovereign_agent.providers import (
    AgentProvider,
    CliProvider,
    InvocationRequest,
    InvocationResult,
    ProviderRegistry,
    StructuredResultEvent,
)
from sovereign_agent.registry import RuntimeAddress, SeatInstance, SeatRegistry
from sovereign_agent.relay import DurableRelay, RelayMessage
from sovereign_agent.repository import (
    DeliveryResult,
    DeliveryState,
    DirtyWorktreePolicy,
    GitEvidence,
    RepositoryExecution,
    RepositoryManager,
)
from sovereign_agent.runtime import RuntimeRoot
from sovereign_agent.session import Session, create_session, load_session

Clock = Callable[[], datetime]

_SUPPORTED_CONSTRAINTS = frozenset(
    {
        "base_ref",
        "dirty_worktree",
        "filesystem_isolation",
        "network_isolation",
        "preserve_on_failure",
        "structured_output",
        "timeouts",
        "trunk_mutation",
        "self_merge",
        "sandbox_minimum",
        "network",
        "max_invocations",
        "idle_timeout_seconds",
        "delivery_enabled",
        "delivery_remote",
        "delivery_branch",
    }
)
_TERMINAL_PHASES = frozenset({"finalized", "rejected"})


class AdmissionRejected(ValueError):
    """A request failed deterministic admission before execution side effects."""

    def __init__(self, reason: str, detail: str) -> None:
        self.reason = reason
        self.detail = redact_text(detail)
        super().__init__(f"{reason}: {self.detail}")


class ExecutionNotFound(LookupError):
    """No execution or rejection exists for an execution ID."""


@dataclass(frozen=True)
class ExecutionStatus:
    execution_id: str
    phase: str
    terminal: bool
    receipt_sha256: str | None = None
    cancellation_requested: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _ProviderLifecycleBackend:
    """Run a provider inside Unit 3's prepare/close lifecycle.

    The configured backend remains responsible for preparation, isolation
    evidence, cancellation teardown and close. Provider invocation is the
    lifecycle's execute operation, avoiding a second provider-specific runner.
    """

    def __init__(
        self,
        backend: WorkerBackend,
        provider: AgentProvider,
        invocation: InvocationRequest,
        observer: Callable[[Any], None],
    ) -> None:
        self.name = backend.name
        self._backend = backend
        self._provider = provider
        self._invocation = invocation
        self._observer = observer

    def capabilities(self) -> Any:
        return self._backend.capabilities()

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        return await self._backend.prepare(request)

    async def execute(self, handle: RuntimeHandle, invocation: Any = None) -> ExecResult:
        del invocation
        try:
            result = await self._provider.invoke(
                self._invocation,
                observers=(self._observer,),
                activity_callbacks=(),
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise _ProviderInvocationError(str(exc)) from exc
        return ExecResult(
            returncode=0 if result.success else 1,
            value=result,
            terminal_reason=None if result.success else TerminalReason.PROVIDER_ERROR,
        )

    async def close(self, handle: RuntimeHandle, preserve: bool = False) -> CloseResult:
        return await self._backend.close(handle, preserve)


class GovernedExecutionEngine:
    """Admission, execution, verification, delivery and receipt finalization."""

    def __init__(
        self,
        *,
        runtime_root: RuntimeRoot,
        repository_manager: RepositoryManager,
        seat_registry: SeatRegistry,
        providers: ProviderRegistry | Mapping[str, AgentProvider],
        backends: Mapping[str, WorkerBackend],
        relay: DurableRelay | None = None,
        relay_recipient: RuntimeAddress | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.runtime = runtime_root.initialize()
        self.repositories = repository_manager
        self.seats = seat_registry
        self.providers = providers
        self.backends = dict(backends)
        self.relay = relay
        self.relay_recipient = relay_recipient
        self._clock = clock or (lambda: datetime.now(UTC))
        self.lifecycle = ExecutionLifecycle()
        self._active_tasks: dict[ExecutionId, asyncio.Task[ExecutionReceipt]] = {}

    async def run(self, request: GovernedExecutionRequest) -> ExecutionReceipt:
        """Run or safely resume one execution ID."""
        if not isinstance(request, GovernedExecutionRequest):
            raise TypeError("request must be GovernedExecutionRequest")
        paths = self._paths(request.execution_id)
        paths["directory"].mkdir(mode=0o700, parents=True, exist_ok=True)
        async with _async_file_lock(paths["lock"]):
            existing = self._read_receipt(paths["receipt"])
            if existing is not None:
                return existing
            state = self._read_state(paths["state"])
            if state is None:
                try:
                    admitted = self._admit(request)
                except AdmissionRejected as exc:
                    return self._persist_rejection(request, exc, paths)
                state = {
                    "schema_version": 1,
                    "execution_id": str(request.execution_id),
                    "invocation_id": str(request.invocation_id),
                    "phase": "admitted",
                    "started_at": self._now().isoformat(),
                    "request": _redact_persistence(request.to_dict()),
                    "request_sha256": hashlib.sha256(
                        canonical_json_bytes(request.to_dict())
                    ).hexdigest(),
                    "seat": admitted["seat"].to_dict(),
                    "provider": admitted["provider"].name,
                    "backend": admitted["backend"].name,
                    "cancellation_requested": False,
                }
                self._checkpoint(paths, state, "admitted")
                self._emit(request, admitted["seat"], "execution.requested", {}, None)
            else:
                self._validate_resume_identity(request, state)
                admitted = self._admit(request)

            if state["phase"] == "provider_invoking":
                return self._finalize_failure(
                    request,
                    state,
                    paths,
                    "ambiguous-provider-invocation",
                    "recovery refused to duplicate an invocation whose outcome was not journaled",
                    admitted["seat"],
                )
            if state["phase"] == "delivering":
                return self._finalize_failure(
                    request,
                    state,
                    paths,
                    "ambiguous-delivery",
                    "recovery refused to duplicate a delivery whose outcome was not journaled",
                    admitted["seat"],
                )
            if state.get("cancellation_requested") or paths["cancel"].exists():
                return self._finalize_failure(
                    request,
                    state,
                    paths,
                    TerminalReason.ABORTED.value,
                    "execution was cancelled",
                    admitted["seat"],
                    cancelled=True,
                )

            task = asyncio.current_task()
            if task is not None:
                self._active_tasks[request.execution_id] = task
            try:
                return await self._continue(request, admitted, state, paths)
            finally:
                self._active_tasks.pop(request.execution_id, None)

    async def _continue(
        self,
        request: GovernedExecutionRequest,
        admitted: dict[str, Any],
        state: dict[str, Any],
        paths: dict[str, Path],
    ) -> ExecutionReceipt:
        seat: SeatInstance = admitted["seat"]
        provider: AgentProvider = admitted["provider"]
        backend: WorkerBackend = admitted["backend"]
        governance = _mapping(request.governance)
        constraints = request.constraints.to_dict()

        try:
            repo = self._repository_from_state(state)
            if repo is None:
                repo = self.repositories.prepare(
                    request.repository_id,
                    request.execution_id,
                    base_ref=request.base_ref,
                    dirty_policy=DirtyWorktreePolicy(
                        str(constraints.get("dirty_worktree", "fail"))
                    ),
                )
                state["repository"] = _repository_to_dict(repo)
                self._checkpoint(paths, state, "repository_prepared")
            else:
                resumed = self.repositories.resume(repo)
                if resumed.lock_token != repo.lock_token:
                    repo = resumed
                    state["repository"] = _repository_to_dict(repo)
                    self._checkpoint(paths, state, "repository_recovered")

            session = self._session(request)
            if "session_id" not in state:
                state["session_id"] = session.session_id
                self._checkpoint(paths, state, "session_ready")

            if "provider_result" not in state:
                if state.get("cancellation_requested"):
                    raise _TerminalFailure(TerminalReason.ABORTED, "execution was cancelled")
                events: list[dict[str, Any]] = []

                def observe(event: Any) -> None:
                    payload = _redact_persistence(event.to_dict())
                    assert isinstance(payload, dict)
                    events.append(payload)
                    atomic_append_jsonl(paths["events"], payload)

                task_text = str(_mapping(request.input).get("task", request.operation))
                invocation_context = _mapping(request.input)
                invocation_context["repository_worktree"] = str(repo.worktree_path)
                invocation_context["governance"] = _redact_persistence(governance)
                invocation_context["constraints"] = request.constraints.to_dict()
                invocation_context["authority_refs"] = list(request.authority_refs)
                invocation_context["work_artifact_refs"] = list(request.work_artifact_refs)
                invocation = InvocationRequest(
                    execution_id=request.execution_id,
                    invocation_id=request.invocation_id,
                    task=task_text,
                    session=session,
                    context=FrozenDict(tuple(invocation_context.items())),
                    provider_session_id=request.provider_session_id,
                )
                worker_request = WorkerRequest(
                    execution_id=request.execution_id,
                    session_id=session.session_id,
                    session_dir=session.directory,
                    require_filesystem_isolation=bool(
                        constraints.get("filesystem_isolation", False)
                    )
                    or request.constraints.sandbox_minimum.value
                    in {"filesystem-isolated", "network-restricted"},
                    require_network_isolation=bool(constraints.get("network_isolation", False))
                    or request.constraints.sandbox_minimum.value == "network-restricted"
                    or request.constraints.network.value in {"restricted", "denied"},
                    preserve_on_failure=bool(constraints.get("preserve_on_failure", True)),
                    timeouts=_timeouts_from_request(request),
                    metadata=FrozenDict(
                        (
                            ("repository_worktree", str(repo.worktree_path)),
                            ("operation", request.operation),
                        )
                    ),
                )
                self._checkpoint(paths, state, "provider_invoking")
                self._emit(request, seat, "execution.started", {}, "execution.requested")
                wrapped = _ProviderLifecycleBackend(backend, provider, invocation, observe)
                lifecycle = await self._run_lifecycle_with_cancellation(
                    wrapped, worker_request, paths["cancel"]
                )
                state["worker_lifecycle"] = {
                    "reason": lifecycle.reason.value,
                    "error": redact_text(lifecycle.error or ""),
                    "transitions": [item.state.value for item in lifecycle.transitions],
                    "close": (
                        asdict(lifecycle.close_result)
                        if lifecycle.close_result is not None
                        else None
                    ),
                }
                if lifecycle.reason is not TerminalReason.SUCCEEDED:
                    lifecycle_reason = lifecycle.reason
                    if lifecycle_reason is TerminalReason.WORKER_TIMEOUT and any(
                        item.state.value == "executing" for item in lifecycle.transitions
                    ):
                        lifecycle_reason = TerminalReason.PROVIDER_TIMEOUT
                    raise _TerminalFailure(
                        lifecycle_reason,
                        lifecycle.error or lifecycle.reason.value,
                    )
                result = lifecycle.exec_result.value if lifecycle.exec_result else None
                if not isinstance(result, InvocationResult):
                    raise _TerminalFailure(
                        TerminalReason.PROVIDER_ERROR,
                        "provider lifecycle returned no normalized InvocationResult",
                    )
                normalized_events = [
                    _redact_persistence(event.to_dict()) for event in result.events
                ]
                atomic_write_bytes(
                    paths["events"],
                    b"".join(canonical_json_bytes(event) + b"\n" for event in normalized_events),
                )
                state["provider_result"] = {
                    "success": result.success,
                    "output": _redact_persistence(thaw_json(result.output)),
                    "summary": redact_text(result.summary),
                    "next_action": result.next_action,
                    "events": normalized_events,
                }
                self._checkpoint(paths, state, "provider_completed")

            result_data = _mapping(state["provider_result"])
            if not bool(result_data.get("success")):
                raise _TerminalFailure(TerminalReason.PROVIDER_ERROR, "provider reported failure")
            self._verify_structured(constraints, result_data)
            self._checkpoint(paths, state, "structured_output_verified")

            evidence = self.repositories.capture_evidence(
                repo,
                artifact_references=(str(paths["events"]),),
            )
            state["git_evidence"] = _git_evidence_to_dict(evidence)
            self._checkpoint(paths, state, "evidence_captured")

            if request.acceptance_commands:
                state["verification_commands"] = self._run_acceptance_commands(request, repo)
                self._checkpoint(paths, state, "commands_verified")
            self._verify_predicates(governance.get("verification", ()), result_data, evidence, repo)
            self._checkpoint(paths, state, "verification_passed")
            self._verify_business(governance.get("business_completion", ()), result_data, evidence)
            self._checkpoint(paths, state, "business_verified")

            if "delivery" not in state:
                delivery_cfg = _mapping(governance.get("delivery", {}))
                delivery_enabled = request.constraints.delivery_enabled
                if delivery_enabled:
                    self._checkpoint(paths, state, "delivering")
                delivery = self.repositories.deliver(
                    repo,
                    enabled=delivery_enabled,
                    remote=request.constraints.delivery_remote
                    or _optional_str(delivery_cfg.get("remote")),
                    remote_branch=request.constraints.delivery_branch
                    or _optional_str(delivery_cfg.get("branch")),
                )
                state["delivery"] = _delivery_to_dict(delivery)
                self._checkpoint(paths, state, "delivery_verified")
            delivery_data = _mapping(state["delivery"])
            if delivery_data.get("state") == DeliveryState.FAILED.value:
                delivery_reason = str(delivery_data.get("failure_reason") or "delivery_failed")
                raise _TerminalFailure(
                    TerminalReason.DELIVERY_FAILED,
                    delivery_reason,
                    receipt_reason=f"delivery-{delivery_reason.replace('_', '-')}",
                )
            self._verify_required_evidence(request, state)

            return self._finalize_success(request, state, paths, seat)
        except _TerminalFailure as exc:
            return self._finalize_failure(
                request,
                state,
                paths,
                exc.receipt_reason,
                exc.detail,
                seat,
                cancelled=exc.reason is TerminalReason.ABORTED,
            )
        except Exception as exc:  # every admitted attempt receives one receipt
            failure_reason = _exception_reason(exc)
            return self._finalize_failure(
                request,
                state,
                paths,
                failure_reason,
                f"{type(exc).__name__}: {exc}",
                seat,
            )
        finally:
            repo = self._repository_from_state(state)
            if repo is not None:
                try:
                    self.repositories.release(repo)
                except Exception:
                    pass

    def cancel(self, execution_id: ExecutionId | str) -> bool:
        eid = execution_id if isinstance(execution_id, ExecutionId) else ExecutionId(execution_id)
        paths = self._paths(eid)
        state = self._read_state(paths["state"])
        if state is None or state.get("phase") in _TERMINAL_PHASES:
            return False
        atomic_write_bytes(
            paths["cancel"],
            canonical_json_bytes(
                {
                    "execution_id": str(eid),
                    "requested_at": self._now().isoformat(),
                }
            ),
        )
        state["cancellation_requested"] = True
        self._checkpoint(paths, state, "cancellation_requested")
        self.lifecycle.cancel(eid)
        task = self._active_tasks.get(eid)
        if task is not None and task.done():
            self._active_tasks.pop(eid, None)
        return True

    async def _run_lifecycle_with_cancellation(
        self,
        backend: WorkerBackend,
        request: WorkerRequest,
        marker: Path,
    ) -> LifecycleResult:
        running = asyncio.create_task(self.lifecycle.run(backend, request))
        while not running.done():
            if marker.exists():
                self.lifecycle.cancel(request.execution_id)
            try:
                return await asyncio.wait_for(asyncio.shield(running), timeout=0.05)
            except TimeoutError:
                continue
        return await running

    def status(self, execution_id: ExecutionId | str) -> ExecutionStatus:
        eid = execution_id if isinstance(execution_id, ExecutionId) else ExecutionId(execution_id)
        paths = self._paths(eid)
        receipt = self._read_receipt(paths["receipt"])
        if receipt is not None:
            return ExecutionStatus(
                str(eid),
                "finalized",
                True,
                receipt.evidence_sha256,
                receipt.status is ReceiptStatus.CANCELLED,
            )
        state = self._read_state(paths["state"])
        if state is None:
            rejection = self._read_state(paths["rejection"])
            if rejection is None:
                raise ExecutionNotFound(str(eid))
            return ExecutionStatus(str(eid), "rejected", True)
        return ExecutionStatus(
            str(eid),
            str(state["phase"]),
            False,
            cancellation_requested=bool(state.get("cancellation_requested")),
        )

    def receipt(self, execution_id: ExecutionId | str) -> ExecutionReceipt | None:
        eid = execution_id if isinstance(execution_id, ExecutionId) else ExecutionId(execution_id)
        return self._read_receipt(self._paths(eid)["receipt"])

    def _admit(self, request: GovernedExecutionRequest) -> dict[str, Any]:
        governance = _mapping(request.governance)
        authority = governance.get("authority")
        if authority is not None and (not isinstance(authority, Mapping) or not authority):
            raise AdmissionRejected(
                "invalid-authority", "governance.authority must be a non-empty object"
            )
        legacy_constraints = governance.get("constraints", {})
        if not isinstance(legacy_constraints, Mapping):
            raise AdmissionRejected(
                "invalid-constraints", "governance.constraints must be an object"
            )
        constraints = request.constraints.to_dict()
        required_unknown = sorted(
            name
            for name, value in request.constraints.unknown_fields.items()
            if name not in _SUPPORTED_CONSTRAINTS and _constraint_required(value)
        )
        if required_unknown:
            raise AdmissionRejected(
                "unsupported-required-constraint",
                f"unsupported required constraints: {', '.join(required_unknown)}",
            )
        self._validate_governance_structure(governance, constraints)
        try:
            seat = self.seats.get(request.seat_instance_id)
        except Exception as exc:
            raise AdmissionRejected("seat-not-registered", str(exc)) from exc
        expected_address = governance.get("seat_address")
        if expected_address is not None and str(seat.address) != expected_address:
            raise AdmissionRejected(
                "seat-address-mismatch", "declared seat address does not match registry"
            )
        if seat.seat_id != request.seat_type:
            raise AdmissionRejected(
                "seat-type-mismatch", "request seat_type does not match registered seat"
            )
        if (
            seat.sovereign_session_id is not None
            and seat.sovereign_session_id != request.sovereign_session_id
        ):
            raise AdmissionRejected(
                "session-mismatch",
                "request sovereign_session_id does not match the registered binding",
            )
        if request.constraints.max_invocations != 1:
            raise AdmissionRejected(
                "unsupported-required-constraint",
                "this engine supports exactly one provider invocation per execution",
            )
        if governance.get("provider") not in (None, seat.provider):
            raise AdmissionRejected(
                "provider-mismatch", "declared provider does not match registered seat"
            )
        if governance.get("backend") not in (None, seat.backend):
            raise AdmissionRejected(
                "backend-mismatch", "declared backend does not match registered seat"
            )
        provider = self._provider(seat.provider)
        if provider is None:
            raise AdmissionRejected("provider-unavailable", seat.provider)
        backend = self.backends.get(seat.backend)
        if backend is None:
            raise AdmissionRejected("backend-unavailable", seat.backend)
        backend_available = backend.capabilities().get("available")
        if backend_available is not None and not backend_available.is_available():
            raise AdmissionRejected(
                "backend-unavailable",
                f"{seat.backend} reports unavailable with "
                f"{backend_available.evidence_level.to_wire()} evidence",
            )
        try:
            self.repositories.resolve(request.repository_id)
        except Exception as exc:
            raise AdmissionRejected("repository-not-governed", str(exc)) from exc
        if constraints.get("structured_output") and not provider.capabilities.structured_result:
            raise AdmissionRejected(
                "capability-mismatch", "structured_output requires provider support"
            )
        if (
            "structured_result" in request.required_evidence
            and not provider.capabilities.structured_result
        ):
            raise AdmissionRejected(
                "capability-mismatch",
                "required structured_result evidence is unavailable",
            )
        if "verification_commands" in request.required_evidence and not request.acceptance_commands:
            raise AdmissionRejected(
                "missing-required-evidence",
                "verification_commands evidence requires acceptance_commands",
            )
        if (
            "remote_containment" in request.required_evidence
            and not request.constraints.delivery_enabled
        ):
            raise AdmissionRejected(
                "missing-required-evidence",
                "remote_containment evidence requires requested delivery",
            )
        backend_manifest = backend.capabilities()
        sandbox_minimum = request.constraints.sandbox_minimum.value
        if sandbox_minimum == "process" and not backend_manifest.is_available("process_isolation"):
            raise AdmissionRejected("capability-mismatch", "process sandbox minimum is unavailable")
        require_filesystem = bool(constraints.get("filesystem_isolation")) or (
            sandbox_minimum in {"filesystem-isolated", "network-restricted"}
        )
        require_network = bool(constraints.get("network_isolation")) or (
            sandbox_minimum == "network-restricted"
            or request.constraints.network.value in {"restricted", "denied"}
        )
        if sandbox_minimum != "none" and not isinstance(provider, CliProvider):
            raise AdmissionRejected(
                "capability-mismatch",
                "in-process providers cannot satisfy an external process or OS sandbox boundary",
            )
        for constraint_name, capability_name in (
            ("filesystem_isolation", "filesystem_isolation"),
            ("network_isolation", "network_isolation"),
        ):
            required = (
                require_filesystem if constraint_name == "filesystem_isolation" else require_network
            )
            if required and not (
                backend_manifest.is_available(capability_name)
                and backend_manifest.has_evidence(capability_name, EvidenceLevel.ENFORCED)
            ):
                raise AdmissionRejected(
                    "capability-mismatch",
                    f"{constraint_name} requires enforced backend evidence",
                )
        if isinstance(provider, CliProvider):
            provider_backend_manifest = provider.backend.capabilities()
            required_provider_capabilities = (
                ("process_isolation", sandbox_minimum != "none"),
                ("filesystem_isolation", require_filesystem),
                ("network_isolation", require_network),
            )
            for capability_name, required in required_provider_capabilities:
                if required and not (
                    provider_backend_manifest.is_available(capability_name)
                    and provider_backend_manifest.has_evidence(
                        capability_name,
                        EvidenceLevel.ENFORCED
                        if capability_name != "process_isolation"
                        else EvidenceLevel.PROBED,
                    )
                ):
                    raise AdmissionRejected(
                        "capability-mismatch",
                        f"provider invocation backend cannot prove {capability_name}",
                    )
        self._check_capabilities(request, seat, provider, backend)
        return {"seat": seat, "provider": provider, "backend": backend}

    @staticmethod
    def _validate_governance_structure(
        governance: Mapping[str, Any], constraints: Mapping[str, Any]
    ) -> None:
        for name in (
            "filesystem_isolation",
            "network_isolation",
            "preserve_on_failure",
        ):
            if name in constraints and not isinstance(constraints[name], bool):
                raise AdmissionRejected(
                    "invalid-constraints", f"constraints.{name} must be boolean"
                )
        if "dirty_worktree" in constraints and constraints["dirty_worktree"] not in {
            "fail",
            "allow",
        }:
            raise AdmissionRejected(
                "invalid-constraints", "constraints.dirty_worktree must be fail or allow"
            )
        if "base_ref" in constraints and not isinstance(constraints["base_ref"], str):
            raise AdmissionRejected("invalid-constraints", "constraints.base_ref must be a string")
        if "timeouts" in constraints and not isinstance(constraints["timeouts"], Mapping):
            raise AdmissionRejected("invalid-constraints", "constraints.timeouts must be an object")
        if isinstance(constraints.get("timeouts"), Mapping):
            timeout_names = {
                "prepare_s",
                "execute_s",
                "close_s",
                "lifecycle_s",
                "idle_s",
                "completion_s",
                "force_teardown_s",
            }
            unknown_timeouts = sorted(set(constraints["timeouts"]) - timeout_names)
            if unknown_timeouts:
                raise AdmissionRejected(
                    "invalid-constraints",
                    f"unknown timeout fields: {', '.join(unknown_timeouts)}",
                )
            if any(
                value is not None
                and (not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0)
                for value in constraints["timeouts"].values()
            ):
                raise AdmissionRejected(
                    "invalid-constraints", "timeout values must be positive numbers or null"
                )
        structured = constraints.get("structured_output")
        if structured is not None and not isinstance(structured, (bool, Mapping)):
            raise AdmissionRejected(
                "invalid-constraints",
                "constraints.structured_output must be boolean or object",
            )
        _validate_predicate_declarations(
            governance.get("verification", ()),
            {
                "provider_success",
                "changed_paths_nonempty",
                "head_changed",
                "clean_worktree",
                "file_exists",
                "output_field_equals",
            },
            "verification",
        )
        _validate_predicate_declarations(
            governance.get("business_completion", ()),
            {
                "process_complete",
                "provider_success",
                "output_field_equals",
                "changed_paths_nonempty",
            },
            "business_completion",
        )
        delivery = governance.get("delivery", {})
        if not isinstance(delivery, Mapping):
            raise AdmissionRejected("invalid-delivery", "delivery must be an object")
        if "enabled" in delivery and not isinstance(delivery["enabled"], bool):
            raise AdmissionRejected("invalid-delivery", "delivery.enabled must be boolean")
        for name in ("remote", "branch"):
            if (
                name in delivery
                and delivery[name] is not None
                and not isinstance(delivery[name], str)
            ):
                raise AdmissionRejected(
                    "invalid-delivery", f"delivery.{name} must be a string or null"
                )

    def _check_capabilities(
        self,
        request: GovernedExecutionRequest,
        seat: SeatInstance,
        provider: AgentProvider,
        backend: WorkerBackend,
    ) -> None:
        provider_manifest = provider.capabilities.to_manifest()
        backend_manifest = backend.capabilities()
        for name, requirement in request.capability_manifest.capabilities.items():
            if not getattr(requirement, "available", False):
                continue
            minimum = requirement.evidence_level
            supplied = provider_manifest.get(name) or backend_manifest.get(name)
            if supplied is None and name in seat.capabilities:
                if minimum <= EvidenceLevel.DECLARED:
                    continue
            if (
                supplied is None
                or not supplied.is_available()
                or not supplied.has_evidence(minimum)
            ):
                raise AdmissionRejected(
                    "capability-mismatch",
                    f"{name} requires {minimum.to_wire()} availability evidence",
                )
        if not provider.capabilities.available:
            raise AdmissionRejected("provider-unavailable", provider.name)

    def _verify_structured(self, constraints: Mapping[str, Any], result: Mapping[str, Any]) -> None:
        spec = constraints.get("structured_output", False)
        if not spec:
            return
        events = result.get("events", ())
        structured = [
            item.get("result")
            for item in events
            if isinstance(item, Mapping) and item.get("type") == StructuredResultEvent.EVENT_TYPE
        ]
        if not structured:
            raise _TerminalFailure(
                TerminalReason.INVALID_STRUCTURED_OUTPUT,
                "structured output was required but no structured_result event was emitted",
            )
        if isinstance(spec, Mapping):
            fields = spec.get("required_fields", ())
            if not isinstance(fields, Sequence) or isinstance(fields, str):
                raise _TerminalFailure(
                    TerminalReason.INVALID_STRUCTURED_OUTPUT,
                    "required_fields must be an array",
                )
            missing = [name for name in fields if name not in _mapping(structured[-1])]
            if missing:
                raise _TerminalFailure(
                    TerminalReason.INVALID_STRUCTURED_OUTPUT,
                    f"missing structured fields: {', '.join(map(str, missing))}",
                )

    def _verify_predicates(
        self,
        specs: Any,
        result: Mapping[str, Any],
        evidence: GitEvidence,
        repo: RepositoryExecution,
    ) -> None:
        for spec in _predicate_list(specs):
            kind = str(spec.get("type", ""))
            passed = False
            if kind == "provider_success":
                passed = bool(result.get("success"))
            elif kind == "changed_paths_nonempty":
                passed = bool(evidence.changed_paths)
            elif kind == "head_changed":
                passed = evidence.head_sha != evidence.base_sha
            elif kind == "clean_worktree":
                passed = not evidence.status_porcelain
            elif kind == "file_exists":
                path = self.repositories.resolve_relative_path(repo, str(spec.get("path", "")))
                passed = path.is_file()
            elif kind == "output_field_equals":
                passed = _mapping(result.get("output", {})).get(str(spec.get("field"))) == spec.get(
                    "value"
                )
            else:
                raise _TerminalFailure(
                    TerminalReason.VERIFICATION_FAILED,
                    f"unsupported verification predicate: {kind}",
                )
            if not passed:
                raise _TerminalFailure(
                    TerminalReason.VERIFICATION_FAILED, f"predicate failed: {kind}"
                )

    def _verify_business(
        self, specs: Any, result: Mapping[str, Any], evidence: GitEvidence
    ) -> None:
        for spec in _predicate_list(specs):
            kind = str(spec.get("type", ""))
            if kind == "process_complete":
                passed = True
            elif kind == "provider_success":
                passed = bool(result.get("success"))
            elif kind == "output_field_equals":
                passed = _mapping(result.get("output", {})).get(str(spec.get("field"))) == spec.get(
                    "value"
                )
            elif kind == "changed_paths_nonempty":
                passed = bool(evidence.changed_paths)
            else:
                raise _TerminalFailure(
                    TerminalReason.BUSINESS_VERIFICATION_FAILED,
                    f"unsupported business predicate: {kind}",
                )
            if not passed:
                raise _TerminalFailure(
                    TerminalReason.BUSINESS_VERIFICATION_FAILED,
                    f"business predicate failed: {kind}",
                )

    def _run_acceptance_commands(
        self,
        request: GovernedExecutionRequest,
        repo: RepositoryExecution,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        timeout = request.constraints.timeouts.get("completion_s")
        if timeout is None:
            timeout = request.constraints.idle_timeout_seconds
        for command in request.acceptance_commands:
            try:
                completed = subprocess.run(
                    command,
                    cwd=repo.worktree_path,
                    env={
                        name: os.environ[name]
                        for name in ("PATH", "LANG", "LC_ALL", "TMPDIR")
                        if name in os.environ
                    }
                    | {"GIT_TERMINAL_PROMPT": "0"},
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    check=False,
                    shell=False,
                    timeout=float(timeout) if timeout is not None else None,
                    text=True,
                )
            except subprocess.TimeoutExpired as exc:
                raise _TerminalFailure(
                    TerminalReason.VERIFICATION_FAILED,
                    f"acceptance command timed out: {command[0]}",
                ) from exc
            record = {
                "argv": list(command),
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
            results.append(_redact_persistence(record))
            if completed.returncode != 0:
                raise _TerminalFailure(
                    TerminalReason.VERIFICATION_FAILED,
                    f"acceptance command failed ({completed.returncode}): {command[0]}",
                )
        return results

    @staticmethod
    def _verify_required_evidence(
        request: GovernedExecutionRequest, state: Mapping[str, Any]
    ) -> None:
        for required in request.required_evidence:
            if required == "structured_result":
                events = _mapping(state.get("provider_result", {})).get("events", ())
                present = any(
                    isinstance(event, Mapping)
                    and event.get("type") == StructuredResultEvent.EVENT_TYPE
                    for event in events
                )
            elif required == "verification_commands":
                present = bool(state.get("verification_commands"))
            elif required == "commit_sha":
                present = bool(_mapping(state.get("git_evidence", {})).get("head_sha"))
            elif required == "remote_containment":
                present = (
                    _mapping(state.get("delivery", {})).get("state") == DeliveryState.VERIFIED.value
                )
            else:
                present = False
            if not present:
                raise _TerminalFailure(
                    TerminalReason.VERIFICATION_FAILED,
                    f"required evidence missing: {required}",
                )

    def _finalize_success(
        self,
        request: GovernedExecutionRequest,
        state: dict[str, Any],
        paths: dict[str, Path],
        seat: SeatInstance,
    ) -> ExecutionReceipt:
        return self._finalize(
            request,
            state,
            paths,
            ReceiptStatus.SUCCEEDED,
            result=_mapping(state["provider_result"]).get("output", {}),
            error=None,
            seat=seat,
        )

    def _finalize_failure(
        self,
        request: GovernedExecutionRequest,
        state: dict[str, Any],
        paths: dict[str, Path],
        reason: str,
        detail: str,
        seat: SeatInstance,
        *,
        cancelled: bool = False,
    ) -> ExecutionReceipt:
        return self._finalize(
            request,
            state,
            paths,
            ReceiptStatus.CANCELLED if cancelled else ReceiptStatus.FAILED,
            result=None,
            error={"reason": reason, "detail": redact_text(detail)},
            seat=seat,
        )

    def _finalize(
        self,
        request: GovernedExecutionRequest,
        state: dict[str, Any],
        paths: dict[str, Path],
        status: ReceiptStatus,
        *,
        result: Any,
        error: Mapping[str, Any] | None,
        seat: SeatInstance | None,
    ) -> ExecutionReceipt:
        existing = self._read_receipt(paths["receipt"])
        if existing is not None:
            return existing
        evidence = {
            "phase": state.get("phase"),
            "provider": state.get("provider"),
            "backend": state.get("backend"),
            "request_sha256": state.get("request_sha256"),
            "authority_refs": list(request.authority_refs),
            "work_artifact_refs": list(request.work_artifact_refs),
            "worker_lifecycle": state.get("worker_lifecycle"),
            "git": state.get("git_evidence"),
            "delivery": state.get("delivery"),
            "journal_sha256": _file_sha256(paths["journal"]),
        }
        git = _mapping(state.get("git_evidence", {}))
        delivery = _mapping(state.get("delivery", {}))
        remote_verified = delivery.get("state") == DeliveryState.VERIFIED.value
        commits = tuple(
            CommitEvidence(
                sha=str(sha),
                remote_contains=(remote_verified and str(sha) == delivery.get("verified_sha"))
                if request.constraints.delivery_enabled
                else None,
            )
            for sha in git.get("commits", ())
        )
        repository_receipt = (
            RepositoryReceipt(
                remote=_optional_str(delivery.get("remote")),
                branch=_optional_str(git.get("execution_branch")),
                base_commit=_optional_str(git.get("base_sha")),
                commits=commits,
            )
            if git
            else None
        )
        verification_records = tuple(
            VerificationCommand(
                command=tuple(str(item) for item in record.get("argv", ())),
                exit_code=record.get("returncode"),
            )
            for record in state.get("verification_commands", ())
            if isinstance(record, Mapping)
        )
        termination = _receipt_termination(status, error)
        receipt = ExecutionReceipt(
            execution_id=request.execution_id,
            invocation_id=request.invocation_id,
            status=status,
            started_at=datetime.fromisoformat(str(state["started_at"])),
            completed_at=self._now(),
            result=_redact_persistence(result) if result is not None else None,
            error=_redact_persistence(error) if error is not None else None,
            evidence=_redact_persistence(evidence),
            termination=termination,
            predecessor_execution_id=request.predecessor_execution_id,
            seat_type=request.seat_type,
            seat_instance=request.seat_instance_id,
            sovereign_session=request.sovereign_session_id,
            provider=str(state.get("provider") or "") or None,
            provider_session=request.provider_session_id,
            worker_backend=str(state.get("backend") or "") or None,
            capability_manifest_ref=hashlib.sha256(
                canonical_json_bytes(request.capability_manifest.to_dict())
            ).hexdigest(),
            completion_signal_seen="provider_result" in state,
            structured_result_valid=state.get("phase")
            not in {"provider_completed", "provider_invoking"}
            if "provider_result" in state
            else False,
            technical_verification_valid=(
                status is ReceiptStatus.SUCCEEDED
                or state.get("phase")
                in {"verification_passed", "business_verified", "delivery_verified"}
            ),
            dataflow_integrity_valid=(
                status is ReceiptStatus.SUCCEEDED
                or state.get("phase") in {"business_verified", "delivery_verified"}
            ),
            repository=repository_receipt,
            verification=verification_records,
            artifact_refs=tuple(request.work_artifact_refs) + (str(paths["events"]),),
            warnings=(
                (str(state.get("backend")),) if state.get("backend") in {"bare", "none"} else ()
            ),
        ).finalize()
        atomic_write_bytes(paths["receipt"], canonical_json_bytes(receipt.to_dict()))
        state["receipt_sha256"] = receipt.evidence_sha256
        self._checkpoint(paths, state, "finalized")
        if seat is not None:
            self._emit(
                request,
                seat,
                "execution.receipt",
                {
                    "status": receipt.status.value,
                    "reason": error.get("reason") if error else None,
                    "evidence_sha256": receipt.evidence_sha256,
                },
                "execution.started",
            )
        persisted = self._read_receipt(paths["receipt"])
        assert persisted is not None
        return persisted

    def _persist_rejection(
        self,
        request: GovernedExecutionRequest,
        rejection: AdmissionRejected,
        paths: dict[str, Path],
    ) -> ExecutionReceipt:
        existing = self._read_receipt(paths["receipt"])
        if existing is not None:
            return existing
        now = self._now()
        record = {
            "schema_version": 1,
            "execution_id": str(request.execution_id),
            "invocation_id": str(request.invocation_id),
            "phase": "rejected",
            "rejected_at": now.isoformat(),
            "reason": rejection.reason,
            "detail": rejection.detail,
            "request": _redact_persistence(request.to_dict()),
        }
        atomic_write_bytes(paths["rejection"], canonical_json_bytes(record))
        state = {
            "schema_version": 1,
            "execution_id": str(request.execution_id),
            "invocation_id": str(request.invocation_id),
            "phase": "rejected",
            "started_at": now.isoformat(),
            "request": record["request"],
        }
        return self._finalize(
            request,
            state,
            paths,
            ReceiptStatus.FAILED,
            result=None,
            error={"reason": rejection.reason, "detail": rejection.detail},
            seat=None,
        )

    def _checkpoint(self, paths: Mapping[str, Path], state: dict[str, Any], phase: str) -> None:
        state["phase"] = phase
        event = {
            "schema_version": 1,
            "sequence": _journal_length(paths["journal"]),
            "phase": phase,
            "timestamp": self._now().isoformat(),
        }
        atomic_append_jsonl(paths["journal"], event)
        atomic_write_bytes(paths["state"], canonical_json_bytes(_redact_persistence(state)))

    def _emit(
        self,
        request: GovernedExecutionRequest,
        seat: SeatInstance,
        kind: str,
        payload: Mapping[str, Any],
        causation_kind: str | None,
    ) -> None:
        if self.relay is None:
            return
        recipient = self.relay_recipient or seat.address
        message_id = _relay_id(request.execution_id, kind)
        causation = (
            _relay_id(request.execution_id, causation_kind) if causation_kind is not None else None
        )
        self.relay.enqueue(
            RelayMessage(
                message_id=message_id,
                sender=seat.address,
                recipient=recipient,
                kind=kind,
                payload=FrozenDict(tuple(_mapping(_redact_persistence(payload)).items())),
                created_at=self._now(),
                conversation_id=str(request.execution_id),
                reply_to=causation,
            )
        )

    def _session(self, request: GovernedExecutionRequest) -> Session:
        session_id = (
            f"sess_{hashlib.sha256(str(request.sovereign_session_id).encode()).hexdigest()[:12]}"
        )
        try:
            return load_session(session_id, runtime_root=self.runtime)
        except Exception:
            return create_session(
                scenario="governed-execution",
                task=redact_text(str(_mapping(request.input).get("task", request.operation))),
                session_id=session_id,
                runtime_root=self.runtime,
            )

    def _provider(self, name: str) -> AgentProvider | None:
        if isinstance(self.providers, ProviderRegistry):
            return self.providers.get_or_none(name)
        return self.providers.get(name)

    def _paths(self, execution_id: ExecutionId) -> dict[str, Path]:
        digest = hashlib.sha256(str(execution_id).encode()).hexdigest()
        directory = self.runtime.executions_dir / digest
        return {
            "directory": directory,
            "state": directory / "state.json",
            "journal": directory / "journal.jsonl",
            "events": directory / "events.jsonl",
            "cancel": directory / "cancel.json",
            "rejection": directory / "rejection.json",
            "receipt": self.runtime.receipts_dir / f"{digest}.json",
            "lock": self.runtime.locks_dir / f"execution-{digest}.lock",
        }

    @staticmethod
    def _read_state(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"invalid execution state: {path}")
        return value

    @staticmethod
    def _read_receipt(path: Path) -> ExecutionReceipt | None:
        if not path.exists():
            return None
        return ExecutionReceipt.from_dict(json.loads(path.read_text(encoding="utf-8")))

    @staticmethod
    def _validate_resume_identity(
        request: GovernedExecutionRequest, state: Mapping[str, Any]
    ) -> None:
        if state.get("execution_id") != str(request.execution_id):
            raise ValueError("execution state identity mismatch")
        if state.get("invocation_id") != str(request.invocation_id):
            raise ValueError("execution ID cannot be reused with a different invocation ID")

    @staticmethod
    def _repository_from_state(state: Mapping[str, Any]) -> RepositoryExecution | None:
        value = state.get("repository")
        if not isinstance(value, Mapping):
            return None
        return RepositoryExecution(
            repository_id=request_id(value["repository_id"]),
            execution_id=ExecutionId(str(value["execution_id"])),
            source_checkout=Path(str(value["source_checkout"])),
            worktree_path=Path(str(value["worktree_path"])),
            base_ref=str(value["base_ref"]),
            base_sha=str(value["base_sha"]),
            branch=str(value["branch"]),
            lock_token=str(value["lock_token"]),
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)


class _TerminalFailure(Exception):
    def __init__(
        self,
        reason: TerminalReason,
        detail: str,
        *,
        receipt_reason: str | None = None,
    ) -> None:
        self.reason = reason
        self.receipt_reason = receipt_reason or reason.value
        self.detail = redact_text(detail)
        super().__init__(self.detail)


class _ProviderInvocationError(RuntimeError):
    terminal_reason = TerminalReason.PROVIDER_ERROR


def request_id(value: object) -> Any:
    from sovereign_agent.contracts import RepositoryId

    return RepositoryId(str(value))


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, FrozenDict):
        thawed = thaw_json(value)
        assert isinstance(thawed, dict)
        return thawed
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _redact_persistence(value: Any) -> Any:
    """Redact sensitive keys and inline credentials in every persisted string."""
    redacted = redact_json(value)

    def visit(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: visit(child) for key, child in item.items()}
        if isinstance(item, list):
            return [visit(child) for child in item]
        if isinstance(item, str):
            return redact_text(item)
        return item

    return visit(redacted)


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _constraint_required(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value.get("required", True))
    return bool(value)


def _predicate_list(value: Any) -> list[dict[str, Any]]:
    if value in (None, (), []):
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise _TerminalFailure(TerminalReason.VERIFICATION_FAILED, "predicates must be an array")
    if any(not isinstance(item, Mapping) for item in value):
        raise _TerminalFailure(
            TerminalReason.VERIFICATION_FAILED, "each predicate must be an object"
        )
    return [dict(item) for item in value]


def _validate_predicate_declarations(value: Any, supported: set[str], label: str) -> None:
    if value in (None, (), []):
        return
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise AdmissionRejected("invalid-predicate", f"{label} must be an array")
    for item in value:
        if not isinstance(item, Mapping):
            raise AdmissionRejected("invalid-predicate", f"{label} entries must be objects")
        kind = item.get("type")
        if not isinstance(kind, str) or kind not in supported:
            raise AdmissionRejected(
                "unsupported-predicate", f"unsupported {label} predicate: {kind}"
            )


def _timeouts_from_request(request: GovernedExecutionRequest) -> LifecycleTimeouts:
    data = _mapping(request.constraints.timeouts)
    if request.constraints.idle_timeout_seconds is not None and "idle_s" not in data:
        data["idle_s"] = request.constraints.idle_timeout_seconds
    return _timeouts(data)


def _timeouts(value: Any) -> LifecycleTimeouts:
    data = _mapping(value)
    allowed = {
        "prepare_s",
        "execute_s",
        "close_s",
        "lifecycle_s",
        "idle_s",
        "completion_s",
        "force_teardown_s",
    }
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise _TerminalFailure(
            TerminalReason.WORKER_ERROR, f"unknown timeout fields: {', '.join(unknown)}"
        )
    return LifecycleTimeouts(**data)


def _repository_to_dict(value: RepositoryExecution) -> dict[str, Any]:
    return {
        "repository_id": str(value.repository_id),
        "execution_id": str(value.execution_id),
        "source_checkout": str(value.source_checkout),
        "worktree_path": str(value.worktree_path),
        "base_ref": value.base_ref,
        "base_sha": value.base_sha,
        "branch": value.branch,
        "lock_token": value.lock_token,
    }


def _git_evidence_to_dict(value: GitEvidence) -> dict[str, Any]:
    return {
        "identity": {
            "repository_id": str(value.identity.repository_id),
            "checkout": value.identity.checkout,
            "remote_name": value.identity.remote_name,
            "remote_url": value.identity.remote_url,
        },
        "base_ref": value.base_ref,
        "base_sha": value.base_sha,
        "execution_branch": value.execution_branch,
        "head_sha": value.head_sha,
        "status_porcelain": value.status_porcelain.decode("utf-8", errors="replace"),
        "changed_paths": list(value.changed_paths),
        "diff_stat": value.diff_stat.decode("utf-8", errors="replace"),
        "patch_sha256": value.patch_sha256,
        "commits": list(value.commits),
        "worktree_path": value.worktree_path,
        "artifact_references": list(value.artifact_references),
    }


def _delivery_to_dict(value: DeliveryResult) -> dict[str, Any]:
    return {
        "local_complete": value.local_complete,
        "state": value.state.value,
        "local_sha": value.local_sha,
        "remote": value.remote,
        "remote_ref": value.remote_ref,
        "verified_sha": value.verified_sha,
        "failure_reason": value.failure_reason.value if value.failure_reason else None,
        "detail": redact_text(value.detail or "") or None,
    }


def _exception_reason(exc: Exception) -> str:
    name = type(exc).__name__.casefold()
    if "dirty" in name:
        return "repository-dirty"
    if "isolation" in name:
        return TerminalReason.ISOLATION_UNAVAILABLE.value
    if "timeout" in name:
        return TerminalReason.WORKER_TIMEOUT.value
    if "provider" in name:
        return TerminalReason.PROVIDER_ERROR.value
    if "repository" in name:
        return "repository-error"
    return TerminalReason.WORKER_ERROR.value


def _receipt_termination(
    status: ReceiptStatus, error: Mapping[str, Any] | None
) -> ReceiptTermination:
    if status is ReceiptStatus.SUCCEEDED:
        return ReceiptTermination.COMPLETED
    if status is ReceiptStatus.CANCELLED:
        return ReceiptTermination.ABORTED
    reason = str(error.get("reason", "")) if error else ""
    refuse = {
        "invalid-authority",
        "invalid-constraints",
        "invalid-delivery",
        "invalid-predicate",
        "unsupported-required-constraint",
        "unsupported-predicate",
        "seat-not-registered",
        "seat-type-mismatch",
        "seat-address-mismatch",
        "session-mismatch",
        "provider-unavailable",
        "backend-unavailable",
        "provider-mismatch",
        "backend-mismatch",
        "repository-not-governed",
        "capability-mismatch",
        "missing-required-evidence",
    }
    if reason in refuse:
        return ReceiptTermination.REFUSED
    if reason.startswith("delivery-"):
        return ReceiptTermination.DELIVERY_FAILED
    try:
        return ReceiptTermination(reason)
    except ValueError:
        return ReceiptTermination.WORKER_ERROR


def _relay_id(execution_id: ExecutionId, kind: str) -> RelayMessageId:
    digest = hashlib.sha256(f"{execution_id}\0{kind}".encode()).hexdigest()[:24]
    return RelayMessageId(f"exec-{digest}")


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _journal_length(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_bytes().splitlines() if line)


@asynccontextmanager
async def _async_file_lock(path: Path) -> Any:
    """Acquire the process-safe Unit 6 lock without blocking the event loop."""
    manager = exclusive_file_lock(path)
    await asyncio.to_thread(manager.__enter__)
    try:
        yield
    finally:
        await asyncio.to_thread(manager.__exit__, None, None, None)


__all__ = [
    "AdmissionRejected",
    "ExecutionNotFound",
    "ExecutionStatus",
    "GovernedExecutionEngine",
]
