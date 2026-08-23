"""Thin runtime adapter around ZeoCore. Does not define another capability schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from zeo_core.contracts import generate_invocation_id
from zeo_core.contracts.capabilities.invocation import CapabilityInvocationRecord
from zeo_core.tools import BoundCapability, CapabilityRegistry, invocation_record

from sovereign_agent._internal.llm_client import ToolCall
from sovereign_agent.capabilities.admission import AdmissionRefused, admit_capability
from sovereign_agent.capabilities.approval import ApprovalDisposition, ApprovalPolicy
from sovereign_agent.capabilities.catalog import FrozenExecutionCatalog, resolve_projected_name
from sovereign_agent.capabilities.context import CapabilityContextFactory, ExecutionScope
from sovereign_agent.capabilities.invoke import invoke_cancellable
from sovereign_agent.capabilities.locks import ConcurrencyGate
from sovereign_agent.capabilities.mapping import capability_result_to_tool_dict


@dataclass
class RuntimeInvocationResult:
    provider_response: dict[str, Any]
    record: CapabilityInvocationRecord | None = None
    approval: ApprovalDisposition = ApprovalDisposition.NOT_REQUIRED
    paused_for_approval: bool = False
    lock_evidence: str | None = None


class CapabilityExecutor:
    def __init__(
        self,
        registry: CapabilityRegistry,
        context_factory: CapabilityContextFactory | None = None,
        approval_policy: ApprovalPolicy | None = None,
        catalog: FrozenExecutionCatalog | None = None,
        gate: ConcurrencyGate | None = None,
    ) -> None:
        self.registry = registry
        self.context_factory = context_factory or CapabilityContextFactory()
        self.approval_policy = approval_policy or ApprovalPolicy()
        self.catalog = catalog
        self.gate = gate or ConcurrencyGate()
        self.records: list[CapabilityInvocationRecord] = []

    async def invoke(
        self,
        *,
        execution: ExecutionScope,
        provider_call: ToolCall,
        cancellation: Any | None = None,
    ) -> RuntimeInvocationResult:
        name = provider_call.name
        if self.catalog is not None:
            canonical = resolve_projected_name(self.catalog, name)
        else:
            canonical = name
        bound: BoundCapability = self.registry.get(canonical)
        try:
            admit_capability(capability=bound, execution=execution)
        except AdmissionRefused as exc:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": exc.message,
                    "code": exc.code,
                    "requires_human_approval": False,
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
                }
            )

        disposition = self.approval_policy.evaluate(bound, execution)
        if disposition is ApprovalDisposition.DENIED:
            return RuntimeInvocationResult(
                provider_response={
                    "success": False,
                    "output": {},
                    "summary": "capability denied by approval policy",
                    "requires_human_approval": False,
                },
                approval=disposition,
            )
        if disposition is ApprovalDisposition.REQUIRED:
            return RuntimeInvocationResult(
                provider_response={
                    "success": True,
                    "output": {"approval_reason": "capability requires operator approval"},
                    "summary": f"approval required for {canonical}",
                    "requires_human_approval": True,
                },
                approval=disposition,
                paused_for_approval=True,
            )

        ctx = self.context_factory.build(execution, bound, cancellation)
        started = datetime.now(UTC)
        async with self.gate.hold(bound, request) as lock_evidence:
            result = await invoke_cancellable(bound, request, ctx)
        ended = datetime.now(UTC)
        record = invocation_record(
            capability=bound,
            request=request,
            result=result,
            ctx=ctx,
            invocation_id=generate_invocation_id(),
            started_at=started,
            ended_at=ended,
        )
        self.records.append(record)
        payload = capability_result_to_tool_dict(result)
        payload["invocation_id"] = record.invocation_id
        payload["capability_id"] = canonical
        payload["request_digest"] = record.request_digest
        payload["result_digest"] = record.result_digest
        return RuntimeInvocationResult(
            provider_response=payload,
            record=record,
            approval=disposition,
            lock_evidence=lock_evidence,
        )
