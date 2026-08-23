# API reference

The public API of `sovereign_agent`. Anything not listed here is internal and may change between patch releases.

Full docstrings are on the classes themselves; this page is an overview. For the definitive reference, read the source — every public class has a docstring that explains its purpose, parameters, and behaviour.

The authoritative v0.7.0 contract is [API Stability](API.md) and its
machine-checked 165-symbol manifest. All listed top-level exports are stable
within the v0.7 series. Prefer ZeoCore `@capability` for new reusable actions;
`@register_tool` remains exported and deprecated until 2027-02-23.

## Errors (Pattern C)

```python
from sovereign_agent import (
    SovereignError,      # base class
    SystemError,         # SA_SYS_*
    ValidationError,     # SA_VAL_*
    IOError,             # SA_IO_*
    ExternalError,       # SA_EXT_*  (retriable=True by default)
    ToolError,           # SA_TOOL_*
    ErrorCategory,
)
```

Agents branch on `error.category`, not on exception class. See `sovereign_agent/errors.py` for the canonical code list.

## Discovery (Pattern A)

```python
from sovereign_agent import Discoverable, DiscoverySchema, discoverable
```

## Session (Decision 1)

```python
from sovereign_agent import (
    Session,
    SessionState,
    create_session,
    load_session,
    list_sessions,
    archive_session,
)
```

## Queue (Decisions 2, 4, 8)

```python
from sovereign_agent import SessionQueue, TaskPriority
```

## Tickets (Decision 9 + Pattern D)

```python
from sovereign_agent import (
    Ticket,
    TicketState,
    TicketResult,
    Manifest,
    OutputRecord,
    create_ticket,
    list_tickets,
)
```

`Manifest.verify()` is idempotent and safe to call repeatedly — e.g. by a grader after the fact.

## IPC (Decisions 3, 4)

```python
from sovereign_agent import IpcWatcher, write_ipc_message, send_input
```

## Scheduler (Decision 6)

```python
from sovereign_agent import DriftCorrectedScheduler, ScheduledTask
```

## Capabilities (v0.5)

Reusable actions are ZeoCore `@capability` definitions executed by
`CapabilityExecutor`. Session filesystem operations project as `read_file`,
`write_file`, and `list_files`. `complete_task` and `handoff_to_structured`
are runtime commands. `CallableSurface` is the merged provider tools list.

```python
from sovereign_agent import (
    CallableSurface,
    CapabilityContextFactory,
    CapabilityExecutor,
    RuntimeCommandRegistry,
    make_session_callable_surface,
)
```

Runtime/provider evidence uses `RuntimeCapabilityAssertion` and
`RuntimeCapabilityManifest` (wire key still `capability_manifest`).

## Tools (compatibility window)

```python
from sovereign_agent import (
    ToolRegistry,
    ToolResult,
    register_tool,          # decorator; deprecated
    global_registry,
    make_builtin_registry,  # session-scoped registry with read/write/handoff/complete
)
```

`@register_tool` auto-generates the discovery schema from the function's signature and docstring. Type hints (`str`, `int`, `float`, `bool`, `list`, `dict`) become JSON Schema. Prefer `@capability` for new reusable actions.

## Planner and Executor

```python
from sovereign_agent import (
    Planner, DefaultPlanner, Subgoal,
    Executor, DefaultExecutor, ExecutorResult,
)
```

## Halves

```python
from sovereign_agent import Half, HalfResult, LoopHalf, StructuredHalf, Rule
```

## Handoff

```python
from sovereign_agent import Handoff, write_handoff, read_handoff
```

## Orchestrator

```python
from sovereign_agent import Orchestrator, TaskResult, run_task
```

`run_task` is the simple sync entry point: create a session, run one task to completion, return a result. For long-running or multi-task deployments, instantiate `Orchestrator` directly and drive its `run()` coroutine.

## Config

```python
from sovereign_agent import Config

config = Config.from_env()             # reads SOVEREIGN_AGENT_* env vars
config = Config.from_toml(Path("x.toml"))
issues = config.validate()             # list[str], empty if OK
```

## Observability

```python
from sovereign_agent import (
    TraceEvent, TraceReader,
    Judge, JudgeResult,
    PlannerQualityJudge, ExecutorTrajectoryJudge, MemoryUsageJudge,
    generate_session_report,
)
```

## Memory (skeleton — API stable, behaviors TODO)

```python
from sovereign_agent import (
    MemoryType, MemoryEntry, MemoryStore,
    MemoryRetrieval, MemoryConsolidation,
)
```

These classes exist and can be instantiated. They do not yet retrieve or
consolidate anything useful. Vector-DB backends are a
[v0.3 non-goal](v0.3-non-goals.md).

## Worker backends

```python
from sovereign_agent import (
    WorkerBackend, WorkerOutcome,
    BareWorker, SubprocessWorker, DockerWorker,
    make_worker_backend,
)
```

`make_worker_backend(config, advance_fn=...)` selects a backend from
`Config.worker_backend`, which accepts `"bare"`, `"subprocess"`, `"docker"`,
`"podman"`, and `"ssh"`:

| Value | Status |
|---|---|
| `"bare"` (default) | Works. Runs the step in-process — no isolation, by choice. |
| `"subprocess"` | Works. Separate Python process, optionally confined by Landlock (Linux ≥ 5.13) or `sandbox-exec` (macOS). Raises at construction time if you ask for it on a host with neither. |
| `"docker"` | Digest-pinned container worker. Refuses without an engine or image digest. |
| `"podman"` | Rootless Podman sharing the Docker contract. |
| `"ssh"` | Identity-pinned remote worker. Disconnect is unknown until reconcile. |

## Fleet execution (v0.7)

```python
from sovereign_agent import (
    FleetCoordinator,
    PodmanWorker,
    SecretBroker,
    SshWorker,
)
```

`FleetCoordinator` owns worker registration, admission, placement,
reservations, dispatch, and reconciliation. `PodmanWorker` follows the
digest-pinned container contract. `SshWorker` requires pinned host identity and
refuses trust-on-first-use. `SecretBroker` resolves short-lived secret leases
at spawn time; secret values must never be persisted in requests, tickets, or
receipts.

These are operator-facing primitives. Begin with the
[v0.7 operator guide](v0.7-operator.md), not raw construction.

## Governed execution

```python
from sovereign_agent import (
    AdmissionRejected,
    ExecutionReceipt,
    ExecutionStatus,
    GovernedExecutionEngine,
    GovernedExecutionRequest,
    ReceiptStatus,
)
```

`GovernedExecutionEngine.run(request)` admits and executes one versioned request.
Admission refusals and every later terminal class produce a finalized receipt.
Zero Employee, not this engine, decides whether the receipt satisfies a governed
obligation. `status`, `cancel`, and `receipt` expose durable execution control.
An execution ID is an idempotency key: finalized retries return the existing
immutable receipt.

## Plugin registries

```python
from sovereign_agent import Plugin, Registry
```

## Channels

```python
from sovereign_agent import CHANNEL_REGISTRY
```

`CHANNEL_REGISTRY` is the only channel symbol in `__all__`. The adapter types
(`ChannelAdapter`, `CliChannelAdapter`, `InboundEvent`, `InboundRouter`,
`OutboundMessage`, `ChannelRegistry`) are importable but internal — see
[API Stability](API.md).

## LLM client (internal)

The `LLMClient` protocol and its two implementations (`OpenAICompatibleClient` and `FakeLLMClient`) live under `sovereign_agent._internal.llm_client`. Marked internal because the protocol may change as we add streaming and richer tool-call support. Use via the `DefaultPlanner` / `DefaultExecutor` wrappers rather than directly.

For signatures and source docstrings, use the
[generated Python API](reference/index.md). The authoritative compatibility
list remains [API Stability](API.md).
