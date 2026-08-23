"""Thin runtime adapter around ZeoCore. Does not define another capability schema."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from zeo_core.contracts import generate_invocation_id
from zeo_core.contracts.capabilities.invocation import CapabilityInvocationRecord
from zeo_core.tools import BoundCapability, CapabilityRegistry, invocation_record

from sovereign_agent._internal.llm_client import ToolCall
from sovereign_agent.capabilities.admission import AdmissionRefused, admit_capability
from sovereign_agent.capabilities.approval import (
    ApprovalDisposition,
    ApprovalPolicy,
    load_approval_decision,
    mark_approval_resumed,
    persist_capability_approval,
)
from sovereign_agent.capabilities.catalog import (
    FrozenExecutionCatalog,
    definition_digest,
    entry_for_canonical,
    resolve_projected_name,
    schema_digest,
)
from sovereign_agent.capabilities.context import CapabilityContextFactory, ExecutionScope
from sovereign_agent.capabilities.evidence import (
    invocation_already_recorded,
    persist_invocation_evidence,
)
from sovereign_agent.capabilities.invoke import invoke_capability
from sovereign_agent.capabilities.locks import (
    ConcurrencyGate,
    LockContention,
    LockOwnership,
)
from sovereign_agent.capabilities.mapping import capability_result_to_tool_dict
from sovereign_agent.contracts._core import ContractValidationError


@dataclass
class RuntimeInvocationResult:
    provider_response: dict[str, Any]
    record: CapabilityInvocationRecord | None = None
    approval: ApprovalDisposition = ApprovalDisposition.NOT_REQUIRED
    paused_for_approval: bool = False
    lock_evidence: str | None = None
    approval_id: str | None = None
    evidence_ref: str | None = None


def _session_dir(execution: ExecutionScope) -> Path:
    if execution.session is not None:
        return execution.session.directory
    return Path(execution.output_dir)


class CapabilityExecutor:
    def __init__(
        self,
        registry: CapabilityRegistry,
        context_factory: CapabilityContextFactory | None = None,
        approval_policy: ApprovalPolicy | None = None,
        catalog: FrozenExecutionCatalog | None = None,
        gate: ConcurrencyGate | None = None,
        *,
        invoke_timeout: float = 30.0,
        complete_timeout: float = 5.0,
        teardown_timeout: float = 5.0,
    ) -> None:
        self.registry = registry
        self.context_factory = context_factory or CapabilityContextFactory()
        self.approval_policy = approval_policy or ApprovalPolicy()
        self.catalog = catalog
        self.gate = gate or ConcurrencyGate()
        self.invoke_timeout = invoke_timeout
        self.complete_timeout = complete_timeout
        self.teardown_timeout = teardown_timeout
        self.records: list[CapabilityInvocationRecord] = []

    def _canonical(self, provider_name: str) -> str:
        if self.catalog is None:
            raise ContractValidationError("capability calls require a frozen execution catalog")
        return resolve_projected_name(self.catalog, provider_name)

    def _verify_definition(self, bound: BoundCapability, canonical: str) -> None:
        if self.catalog is None:
            return
        entry = entry_for_canonical(self.catalog, canonical)
        live = definition_digest(bound)
        if live != entry.definition_digest:
            raise ContractValidationError(
                f"frozen definition digest {entry.definition_digest} does not match live {live}"
            )

    async def invoke(
        self,
        *,
        execution: ExecutionScope,
        provider_call: ToolCall,
        cancellation: Any | None = None,
        resume_approval_id: str | None = None,
    ) -> RuntimeInvocationResult:
        try:
            canonical = self._canonical(provider_call.name)
        except ContractValidationError as exc:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": str(exc),
                    "code": "SA_CATALOG_MISMATCH",
                    "requires_human_approval": False,
                    "outcome": "refused",
                }
            )
        bound: BoundCapability = self.registry.get(canonical)
        try:
            self._verify_definition(bound, canonical)
            admit_capability(capability=bound, execution=execution)
        except AdmissionRefused as exc:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": exc.message,
                    "code": exc.code,
                    "requires_human_approval": False,
                    "outcome": "refused",
                }
            )
        except ContractValidationError as exc:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": str(exc),
                    "code": "SA_CATALOG_MISMATCH",
                    "requires_human_approval": False,
                    "outcome": "refused",
                }
            )
        try:
            request = bound.request_model.model_validate(provider_call.arguments or {})
        except ValidationError as exc:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": f"invalid arguments: {exc}",
                    "code": "ZEO_CAP_GUARD_REJECTED",
                    "requires_human_approval": False,
                    "outcome": "refused",
                }
            )

        session_dir = _session_dir(execution)
        if resume_approval_id:
            return await self._resume_approved(
                execution=execution,
                bound=bound,
                canonical=canonical,
                request=request,
                cancellation=cancellation,
                approval_id=resume_approval_id,
            )

        disposition = self.approval_policy.evaluate(bound, execution, request)
        if disposition is ApprovalDisposition.DENIED:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "capability denied by approval policy",
                    "requires_human_approval": False,
                    "outcome": "refused",
                },
                approval=disposition,
            )
        if disposition is ApprovalDisposition.REQUIRED:
            assert self.catalog is not None
            pending = persist_capability_approval(
                session_dir,
                catalog=self.catalog,
                canonical_id=canonical,
                definition_digest=definition_digest(bound),
                arguments=provider_call.arguments or {},
                reason=f"approval required for {canonical}",
                execution_id=str(execution.id),
            )
            return RuntimeInvocationResult(
                provider_response={
                    "success": True,
                    "output": {
                        "approval_reason": "capability requires operator approval",
                        "approval_id": pending["approval_id"],
                    },
                    "summary": f"approval required for {canonical}",
                    "requires_human_approval": True,
                    "outcome": "approval_required",
                },
                approval=disposition,
                paused_for_approval=True,
                approval_id=pending["approval_id"],
            )

        return await self._run_bound(
            execution=execution,
            bound=bound,
            canonical=canonical,
            request=request,
            cancellation=cancellation,
            approval_id=None,
            disposition=disposition,
        )

    async def _resume_approved(
        self,
        *,
        execution: ExecutionScope,
        bound: BoundCapability,
        canonical: str,
        request: Any,
        cancellation: Any | None,
        approval_id: str,
    ) -> RuntimeInvocationResult:
        session_dir = _session_dir(execution)
        decision = load_approval_decision(session_dir, approval_id)
        if decision is None:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "no approval decision to resume",
                    "outcome": "refused",
                    "requires_human_approval": False,
                }
            )
        if decision.get("decision") != "approved":
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": f"approval {decision.get('decision')}",
                    "outcome": "refused",
                    "requires_human_approval": False,
                },
                approval_id=approval_id,
            )
        req = decision["request"]
        if req["canonical_id"] != canonical:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "approval canonical id mismatch",
                    "outcome": "refused",
                    "requires_human_approval": False,
                },
                approval_id=approval_id,
            )
        if self.catalog is not None and req["catalog_digest"] != self.catalog.digest:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "approval catalog digest mismatch",
                    "code": "SA_CATALOG_MISMATCH",
                    "outcome": "refused",
                    "requires_human_approval": False,
                },
                approval_id=approval_id,
            )
        if req["definition_digest"] != definition_digest(bound):
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "approval definition digest mismatch",
                    "code": "SA_CATALOG_MISMATCH",
                    "outcome": "refused",
                    "requires_human_approval": False,
                },
                approval_id=approval_id,
            )
        if invocation_already_recorded(session_dir, req["invocation_id"]):
            return RuntimeInvocationResult(
                provider_response={
                    "success": True,
                    "output": {"idempotent": True},
                    "summary": "invocation already recorded",
                    "requires_human_approval": False,
                    "outcome": "success",
                },
                approval_id=approval_id,
            )
        admit_capability(capability=bound, execution=execution)
        mark_approval_resumed(session_dir, approval_id)
        return await self._run_bound(
            execution=execution,
            bound=bound,
            canonical=canonical,
            request=request,
            cancellation=cancellation,
            approval_id=approval_id,
            disposition=ApprovalDisposition.PREAPPROVED,
            invocation_id=req["invocation_id"],
        )

    async def _run_bound(
        self,
        *,
        execution: ExecutionScope,
        bound: BoundCapability,
        canonical: str,
        request: Any,
        cancellation: Any | None,
        approval_id: str | None,
        disposition: ApprovalDisposition,
        invocation_id: str | None = None,
    ) -> RuntimeInvocationResult:
        ctx = self.context_factory.build(execution, bound, cancellation)
        started = datetime.now(UTC)
        ownership = LockOwnership(
            seat=execution.seat,
            session=str(execution.id),
            repository=execution.repository,
            channel=execution.channel,
        )
        lock_evidence: str | None = None
        try:
            async with self.gate.hold(bound, request, ownership=ownership) as lock_evidence:
                result = await asyncio.wait_for(
                    invoke_capability(bound, request, ctx),
                    timeout=execution.invoke_timeout or self.invoke_timeout,
                )
        except asyncio.CancelledError:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "invocation cancelled",
                    "code": "ZEO_CAP_CANCELLED",
                    "outcome": "cancelled",
                    "requires_human_approval": False,
                },
                lock_evidence=lock_evidence,
                approval=disposition,
            )
        except LockContention as exc:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": str(exc),
                    "code": "SA_LOCK_CONTENTION",
                    "outcome": "contention",
                    "requires_human_approval": False,
                },
                lock_evidence=exc.evidence,
                approval=disposition,
            )
        except TimeoutError:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "invocation timed out",
                    "code": "SA_SYS_TIMEOUT",
                    "outcome": "timeout",
                    "requires_human_approval": False,
                },
                lock_evidence=lock_evidence,
                approval=disposition,
            )
        ended = datetime.now(UTC)
        record = invocation_record(
            capability=bound,
            request=request,
            result=result,
            ctx=ctx,
            invocation_id=invocation_id or generate_invocation_id(),
            started_at=started,
            ended_at=ended,
        )
        self.records.append(record)
        evidence_ref = persist_invocation_evidence(
            _session_dir(execution),
            execution_id=str(execution.id),
            record=record,
            catalog_digest=execution.catalog_digest
            or (self.catalog.digest if self.catalog else ""),
            schema_digest=schema_digest(bound),
            definition_digest=definition_digest(bound),
            effects=bound.definition.effects.concurrency.value,
            requirements=bound.definition.requirements.model_dump(mode="json"),
            approval_id=approval_id,
            lock_evidence=lock_evidence,
            outcome=(result.outcome.value if result.outcome is not None else record.outcome.value),
        )
        payload = capability_result_to_tool_dict(result)
        payload["invocation_id"] = record.invocation_id
        payload["capability_id"] = canonical
        payload["request_digest"] = record.request_digest
        payload["result_digest"] = record.result_digest
        payload["evidence_ref"] = evidence_ref
        if lock_evidence:
            payload["lock_evidence"] = lock_evidence
        return RuntimeInvocationResult(
            provider_response=payload,
            record=record,
            approval=disposition,
            lock_evidence=lock_evidence,
            approval_id=approval_id,
            evidence_ref=evidence_ref,
        )
