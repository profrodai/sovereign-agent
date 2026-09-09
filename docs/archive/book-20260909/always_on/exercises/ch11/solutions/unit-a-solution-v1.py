"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r"""
def invoke(self, call: ToolCall) -> dict[str, Any]:
    tool = self.tools.get(call.name)
    if tool is None or call.name not in self.allowed:
        return {"ok": False, "error": "tool_not_allowed"}
    try:
        arguments = tool.arguments.model_validate(call.arguments, strict=True)
    except ValidationError:
        # ValidationError strings can contain raw arguments and secrets.
        return {"ok": False, "error": "invalid_arguments"}
    if tool.consequential and self.before_write is None:
        return {"ok": False, "error": "write_authority_required"}
    try:
        if tool.consequential:
            assert self.before_write is not None
            self.before_write(call)
        value = tool.handler(arguments)
        encoded = json.dumps(value, allow_nan=False)
        if len(encoded.encode()) > self.max_result_bytes:
            return {"ok": False, "error": "result_too_large"}
        return {"ok": True, "value": value}
    except ValueError, TypeError, KeyError, PermissionError, TimeoutError, OSError:
        return {"ok": False, "error": "tool_failed"}
"""
assert connect_build(implementation_source)["status"] == "PASS"
