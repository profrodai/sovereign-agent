"""Map ZeoCore capability outcomes onto provider-visible results and Sovereign errors."""

from __future__ import annotations

from typing import Any

from zeo_core.contracts import CapabilityOutcome, CapabilityResult

from sovereign_agent.errors import SovereignError, SystemError, ToolError


def capability_result_to_tool_dict(result: CapabilityResult) -> dict[str, Any]:
    data = result.data
    dump = getattr(data, "model_dump", None)
    if callable(dump):
        output = dump()
    elif isinstance(data, dict):
        output = data
    elif data is None:
        output = {}
    else:
        output = {"value": data}
    success = result.outcome is CapabilityOutcome.success or (
        result.outcome is None and result.status.value == "success"
    )
    payload = {
        "success": success,
        "output": output,
        "summary": result.human_message or result.machine_message or "",
        "requires_human_approval": bool((result.metadata or {}).get("requires_human_approval")),
        "outcome": None if result.outcome is None else result.outcome.value,
        "code": result.machine_message,
    }
    if not success:
        payload["error"] = {
            "code": result.machine_message or "ZEO_CAP_UNEXPECTED",
            "message": result.human_message or "",
        }
    return payload


def should_abort_execution(result: CapabilityResult) -> bool:
    """Guard/unavailable failures are provider-visible; they do not abort the loop."""
    if result.outcome in {
        CapabilityOutcome.guard_rejected,
        CapabilityOutcome.unavailable,
        CapabilityOutcome.success,
        CapabilityOutcome.policy_skipped,
    }:
        return False
    return False


def timeout_to_sovereign_error(message: str) -> SovereignError:
    return SystemError(code="SA_SYS_UNEXPECTED", message=message)


def unexpected_to_tool_error(result: CapabilityResult) -> ToolError:
    return ToolError(
        code="SA_TOOL_EXECUTION_FAILED",
        message=result.human_message or "capability failed unexpectedly",
        context={"zeo_code": result.machine_message},
    )
