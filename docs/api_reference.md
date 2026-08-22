# API reference

The public API of `sovereign_agent`. Anything not listed here is internal and may change between patch releases.

Full docstrings are on the classes themselves; this page is an overview. For the definitive reference, read the source — every public class has a docstring that explains its purpose, parameters, and behaviour.

The authoritative list of what is *stable* versus merely *present* is
[API Stability](API.md). Sections below marked **(unreleased v0.3)** are in the
tree but carry no compatibility promise.

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

## Tools

```python
from sovereign_agent import (
    ToolRegistry,
    ToolResult,
    register_tool,          # decorator
    global_registry,
    make_builtin_registry,  # session-scoped registry with read/write/handoff/complete
)
```

`@register_tool` auto-generates the discovery schema from the function's signature and docstring. Type hints (`str`, `int`, `float`, `bool`, `list`, `dict`) become JSON Schema.

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

## Worker backends (unreleased v0.3)

```python
from sovereign_agent import (
    WorkerBackend, WorkerOutcome,
    BareWorker, SubprocessWorker, DockerWorker,
    make_worker_backend,
)
```

`make_worker_backend(config, advance_fn=...)` selects a backend from
`Config.worker_backend`, which accepts `"bare"`, `"subprocess"`, or `"docker"`:

| Value | Status |
|---|---|
| `"bare"` (default) | Works. Runs the step in-process — no isolation, by choice. |
| `"subprocess"` | Works. Separate Python process, optionally confined by Landlock (Linux ≥ 5.13) or `sandbox-exec` (macOS). Raises at construction time if you ask for it on a host with neither. |
| `"docker"` | **Stub.** Constructs and logs a warning; `run_session()` raises `NotImplementedError`. |

Use `"subprocess"` where you would have reached for `"docker"`.

## Governed execution (unreleased v0.3 Unit 7)

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

## Plugin registries (unreleased v0.3)

```python
from sovereign_agent import Plugin, Registry
```

## Channels (unreleased v0.3)

```python
from sovereign_agent import CHANNEL_REGISTRY
```

`CHANNEL_REGISTRY` is the only channel symbol in `__all__`. The adapter types
(`ChannelAdapter`, `CliChannelAdapter`, `InboundEvent`, `InboundRouter`,
`OutboundMessage`, `ChannelRegistry`) are importable but internal — see
[API Stability](API.md).

## LLM client (internal)

The `LLMClient` protocol and its two implementations (`OpenAICompatibleClient` and `FakeLLMClient`) live under `sovereign_agent._internal.llm_client`. Marked internal because the protocol may change as we add streaming and richer tool-call support. Use via the `DefaultPlanner` / `DefaultExecutor` wrappers rather than directly.
