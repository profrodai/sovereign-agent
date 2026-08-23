"""Cancellable invocation that does not swallow CancelledError.

ZeoCore 0.5.0 ``invoke_async`` catches ``BaseException``. Until 0.5.1,
Sovereign Agent invokes the bound function through this helper.
"""

from __future__ import annotations

import inspect

from pydantic import BaseModel, ValidationError
from zeo_core.contracts import CapabilityOutcome, CapabilityResult, GuardResult
from zeo_core.tools import BoundCapability, ToolContext
from zeo_core.tools.invoke import (
    context_cancellation,
    missing_requirements,
    requirements_available,
)


def _run_guards(capability: BoundCapability, request: BaseModel) -> GuardResult:
    for guard in capability.guards:
        result = guard.check(request)
        if not result.ok:
            return result
    return GuardResult.accept()


def _normalize_return(value: object, *, cancelled: bool) -> CapabilityResult:
    if cancelled:
        if isinstance(value, CapabilityResult) and value.outcome == CapabilityOutcome.cancelled:
            return value
        return CapabilityResult.fail(
            msg="Caller cancellation observed",
            code="ZEO_CAP_CANCELLED",
            outcome=CapabilityOutcome.cancelled,
        )
    if isinstance(value, CapabilityResult):
        return value
    return CapabilityResult.fail(
        msg="Capability must return CapabilityResult",
        code="ZEO_CAP_INVALID_RETURN",
        outcome=CapabilityOutcome.invalid_return,
        metadata={"returned_type": type(value).__name__},
    )


def _exception_result(exc: Exception) -> CapabilityResult:
    if isinstance(exc, ValidationError):
        return CapabilityResult.fail(
            msg="Request failed validation",
            code="ZEO_CAP_GUARD_REJECTED",
            exception=exc,
            outcome=CapabilityOutcome.guard_rejected,
        )
    return CapabilityResult.fail(
        msg=f"Unexpected {type(exc).__name__}: {exc}",
        code="ZEO_CAP_UNEXPECTED",
        exception=exc,
        outcome=CapabilityOutcome.unexpected_exception,
    )


async def invoke_cancellable(
    capability: BoundCapability,
    request: BaseModel,
    ctx: ToolContext,
) -> CapabilityResult:
    if context_cancellation(ctx).is_cancelled():
        return CapabilityResult.fail(
            msg="Caller cancellation observed",
            code="ZEO_CAP_CANCELLED",
            outcome=CapabilityOutcome.cancelled,
        )
    if not isinstance(request, capability.request_model):
        try:
            request = capability.request_model.model_validate(request)
        except ValidationError as exc:
            return _exception_result(exc)

    guard = _run_guards(capability, request)
    if not guard.ok:
        return CapabilityResult.fail(
            msg=guard.message or "Request rejected by guard",
            code=guard.code or "ZEO_CAP_GUARD_REJECTED",
            outcome=CapabilityOutcome.guard_rejected,
            metadata={"issues": [i.model_dump() for i in guard.issues]},
        )

    if not requirements_available(capability.definition, ctx) or not capability.is_available(ctx):
        missing = missing_requirements(capability.definition, ctx)
        return CapabilityResult.unavailable(
            reason="Capability unavailable; missing: " + (", ".join(missing) or "unknown"),
        )

    try:
        raw = capability._fn(request, ctx)
        if inspect.isawaitable(raw):
            raw = await raw
        return _normalize_return(raw, cancelled=context_cancellation(ctx).is_cancelled())
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:
        if context_cancellation(ctx).is_cancelled():
            return CapabilityResult.fail(
                msg="Caller cancellation observed",
                code="ZEO_CAP_CANCELLED",
                exception=exc,
                outcome=CapabilityOutcome.cancelled,
            )
        return _exception_result(exc)
