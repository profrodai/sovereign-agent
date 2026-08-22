# API stability and semver contract

**Applies from:** v0.2.0 onwards.
**Contract version:** 1.

!!! warning "The tree is ahead of the last release"
    The only published release is **0.2.0**, whose semver surface was **67**
    symbols. The working tree exports **100**. The 33 extra symbols are unreleased
    v0.3 work and carry **no** stability promise until v0.3.0 is tagged. Both
    sets are listed below, separately, so you can tell which is which.

This document specifies which parts of sovereign-agent are covered by the
[semver](https://semver.org/) contract, what "breaking change" means in this
codebase, and what guarantees users of `pip install sovereign-agent` can
rely on.

---

## The contract in one sentence

**Everything in `sovereign_agent.__all__` is stable within a minor version.
Everything else is internal and may change between any two releases,
including patch releases.**

---

## What "stable" means

For a symbol `X` that appears in `sovereign_agent.__all__` at version `0.2.0`:

- `X` will continue to exist in every `0.2.*` release.
- The **public signature** of `X` will not change in a breaking way within
  the `0.2.*` series. "Breaking" means:
    - A required parameter is added.
    - A parameter is removed.
    - A parameter's type is narrowed (e.g. from `Path | str` to `Path`).
    - A return type is narrowed.
    - A method or attribute is removed from a class.
    - An exception type previously raised is changed to a different type,
      unless the new type is a subclass of the old.
- The **documented semantic behavior** will not change in a way that would
  make existing correct user code start failing.

Non-breaking changes that may happen in patch releases:

- A new optional parameter with a backward-compatible default.
- A new method or attribute.
- A new class that extends a stable base.
- Bug fixes that restore documented behavior.
- Performance improvements.
- Docstring improvements.

---

## What "internal" means

Any module, class, function, or attribute **not** in
`sovereign_agent.__all__` is internal. That includes:

- Everything under `sovereign_agent._internal/`
- Private methods (`_leading_underscore`)
- Submodule contents not re-exported from the top-level package

Internal symbols may be renamed, removed, moved, or have their semantics
changed in any release — including patch releases.

If you find yourself importing from internal paths, either:

1. Open an issue requesting the symbol be made public, or
2. Vendor the code into your project, or
3. Accept that your integration will break and pin to an exact version.

---

## The 67 stable symbols (published v0.2.0)

These are covered by the contract above for every `0.2.*` release.

Category | Symbols
---|---
**Config** | `Config`
**Discovery** | `Discoverable`, `DiscoverySchema`, `discoverable`
**Errors** | `SovereignError`, `ErrorCategory`, `ExternalError`, `IOError`, `SystemError`, `ToolError`, `ValidationError`
**Executor** | `Executor`, `DefaultExecutor`, `ExecutorResult`
**Halves** | `Half`, `HalfResult`, `LoopHalf`, `StructuredHalf`, `Rule`
**Handoff** | `Handoff`, `read_handoff`, `write_handoff`
**IPC** | `IpcWatcher`, `send_input`, `write_ipc_message`
**Memory** | `MemoryStore`, `MemoryEntry`, `MemoryType`, `MemoryRetrieval`, `MemoryConsolidation`
**Observability** | `Judge`, `JudgeResult`, `PlannerQualityJudge`, `ExecutorTrajectoryJudge`, `MemoryUsageJudge`, `TraceEvent`, `TraceReader`, `generate_session_report`
**Orchestrator** | `Orchestrator`, `TaskResult`, `run_task`
**Planner** | `Planner`, `DefaultPlanner`, `Subgoal`
**Scheduler** | `DriftCorrectedScheduler`, `ScheduledTask`
**Session** | `Session`, `SessionState`, `create_session`, `load_session`, `list_sessions`, `archive_session`
**Tickets** | `Ticket`, `TicketResult`, `TicketState`, `Manifest`, `OutputRecord`, `create_ticket`, `list_tickets`
**Tools** | `ToolRegistry`, `ToolResult`, `register_tool`, `global_registry`, `make_builtin_registry`
**Queue** | `SessionQueue`, `TaskPriority`
**Meta** | `__version__`

---

## The 33 unreleased additions (in-tree, not covered)

These are in `sovereign_agent.__all__` on `main` but were not in the published
0.2.0 surface. They may be renamed, resignatured, or removed before v0.3.0 is
tagged. Do not pin production code to them.

Category | Symbols
---|---
**Channels** (v0.3 M1) | `CHANNEL_REGISTRY`
**Plugin registries** (v0.3 M3) | `Plugin`, `Registry`
**Worker lifecycle** (v0.3 Unit 3) | `WorkerBackend`, `WorkerOutcome`, `BareWorker`, `SubprocessWorker`, `OSIsolatedWorker`, `DockerWorker`, `make_worker_backend`, `WorkerRequest`, `RuntimeHandle`, `InvocationSpec`, `ExecResult`, `CloseResult`, `ExecutionLifecycle`, `LifecycleResult`, `LifecycleState`, `LifecycleTimeouts`, `TerminalReason`
**Agent providers** (v0.3 Units 2 and 4) | `AgentProvider`, `InvocationRequest`, `InvocationResult`, `NativeProvider`, `ProviderCapabilities`, `ProviderEvent`, `ProviderRegistry`, `PROVIDER_REGISTRY`, `CliProvider`, `CodexCliProvider`, `ClaudeCodeProvider`, `ProbeEvidence`, `ProviderUnavailable`

`DockerWorker` is an unavailable placeholder. It remains discoverable, but
refuses during lifecycle preparation and its legacy `run_session()` raises
`NotImplementedError`. See
[v0.3 non-goals](v0.3-non-goals.md).

### Imported but not exported

A few v0.3 names are importable from the top-level package yet are **not** in
`__all__`: `ChannelAdapter`, `ChannelRegistry`, `CliChannelAdapter`,
`InboundEvent`, `InboundRouter`, `OutboundMessage`, and `LivenessMonitor`. By the
rule stated at the top of this document, absence from `__all__` means internal.
Being importable is not a promise.

---

If you need to use a symbol not listed here, it is internal. See "What
'internal' means" above.

---

## What triggers a minor vs major bump

Per semver, while the major version is 0 (`0.y.z`), the minor acts as the
major. Translated to this codebase:

**Breaking change in public API → bump minor (0.2.0 → 0.3.0).**

Examples of what would bump the minor:

- Removing a function from `__all__`
- Changing the signature of a public function incompatibly
- Renaming a public class
- Changing a public class's MRO such that `isinstance()` checks break
- Removing a public attribute from a dataclass
- Narrowing an exception type raised by a public function

**Bug fix, doc change, new additive feature → bump patch (0.2.0 → 0.2.1).**

Examples of what would stay on the minor:

- Fixing a bug where a public function raised the wrong exception
- Adding a new method to a public class
- Adding a new optional parameter
- Adding a new public symbol to `__all__`
- Performance improvements
- Documentation updates

---

## What this means for dependent projects

If you `pip install sovereign-agent ~= 0.2.0` (the recommended pin for
downstream projects and homework), you will:

- Receive every `0.2.x` bug-fix release automatically
- Never receive `0.3.0` or later (which may have breaking changes)
- Be safe to run your CI against the latest `0.2.x`

If you pin `sovereign-agent == 0.2.0` exactly, you will:

- Receive no updates
- Manually opt into bug fixes by bumping

Most users should use `~= 0.2.0`.

---

## Deprecation policy

When a public symbol is to be removed in the next minor release:

1. A `DeprecationWarning` is added in the last patch release of the
   current minor, pointing to the replacement.
2. The symbol is documented as deprecated in `CHANGELOG.md`.
3. The symbol is kept functional for at least one full minor cycle (so
   users have time to migrate).
4. On the next minor bump, the symbol is removed and its removal is
   documented in the release notes.

Example timeline:

- `0.2.5` — `old_function()` emits `DeprecationWarning`, docs point to `new_function()`
- `0.3.0` — `old_function()` removed; release notes link the migration

---

## Questions

Open an issue at
[github.com/zeroemployeeorg/sovereign-agent/issues](https://github.com/zeroemployeeorg/sovereign-agent/issues)
with the `api-stability` label.
