# Migration from v0.5 to v0.6

v0.6 does not remove the v0.5 public API. It makes the ZeoCore callable
surface the default execution path.

## What you should do

- Author reusable actions with `@capability` and pass
  `extra_capabilities=[bound_capability_of(fn)]` into `run_task`.
- Keep `complete_task`, `handoff_to_structured`, `abort_execution`, and
  `session_status` as runtime commands. Do not re-author them as capabilities.
- Expect catalog mismatch errors after a package upgrade that changes a
  frozen execution's capability definitions. Start a new session or restore
  the original catalog.

## What still works

`@register_tool`, `ToolRegistry`, and `ToolResult` remain exported. They
emit `DeprecationWarning` at authoring time. `verify_args` and runtime-command
names cannot be adapted into ZeoCore and are refused.

## Compatibility

Python 3.13+, `zeocore>=0.5,<0.6`. v0.4 wire/session/receipt tests remain
green. Fleet placement begins in v0.7.
