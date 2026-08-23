"""sovereign-agent: a framework for building always-on AI agents that you actually own.

Alpha. The declared version is 0.5.0.

The 152 names in the v0.4 public API remain; v0.5 adds capability-adapter symbols.
All 67 symbols published in v0.2.0 remain covered by the compatibility contract. Anything not
in __all__ is internal and may change between any two releases -- including
names that happen to be importable from this module, such as the channel adapter
types and LivenessMonitor.

Not implemented, despite having a name or a config value: DockerWorker (no
container code path exists anywhere in this repository), the Evidently and
OTel observability backends, the voice pipeline, and the memory
retrieval/consolidation behaviours.

See docs/API.md for the semver contract, docs/v0.3-non-goals.md for what is
deliberately out of scope, docs/architecture.md for the architecture, and
README.md for the quickstart.
"""

from __future__ import annotations

# Capabilities (v0.5 ZeoCore adapter)
from sovereign_agent.capabilities import (
    ApprovalDisposition,
    CallableSurface,
    CapabilityContextFactory,
    CapabilityExecutor,
    RuntimeCommandRegistry,
    make_session_callable_surface,
)

# Channels (v0.3 Module 1)
from sovereign_agent.channels import CHANNEL_REGISTRY as CHANNEL_REGISTRY
from sovereign_agent.channels import ChannelAdapter as ChannelAdapter
from sovereign_agent.channels import ChannelRegistry as ChannelRegistry
from sovereign_agent.channels import CliChannelAdapter as CliChannelAdapter
from sovereign_agent.channels import InboundEvent as InboundEvent
from sovereign_agent.channels import InboundRouter as InboundRouter
from sovereign_agent.channels import OutboundMessage as OutboundMessage

# Config
from sovereign_agent.config import Config
from sovereign_agent.contracts import (
    ExecutionConstraints,
    ExecutionReceipt,
    GovernedExecutionRequest,
    ReceiptStatus,
    ReceiptTermination,
    RuntimeCapabilityAssertion,
    RuntimeCapabilityManifest,
)

# Discovery (Pattern A)
from sovereign_agent.discovery import Discoverable, DiscoverySchema, discoverable

# Errors (Pattern C)
from sovereign_agent.errors import (
    ErrorCategory,
    ExternalError,
    IOError,
    SovereignError,
    SystemError,
    ToolError,
    ValidationError,
)

# Governed end-to-end execution (v0.3 Unit 7)
from sovereign_agent.execution import (
    AdmissionRejected,
    ExecutionNotFound,
    ExecutionStatus,
    GovernedExecutionEngine,
)
from sovereign_agent.executor import DefaultExecutor, Executor, ExecutorResult

# Halves
from sovereign_agent.halves import Half, HalfResult
from sovereign_agent.halves.loop import LoopHalf
from sovereign_agent.halves.structured import Rule, StructuredHalf

# Handoff
from sovereign_agent.handoff import Handoff, read_handoff, write_handoff

# IPC (Decisions 3, 4)
from sovereign_agent.ipc import IpcWatcher, send_input, write_ipc_message

# Memory (skeleton; API stable)
from sovereign_agent.memory import (
    MemoryConsolidation,
    MemoryEntry,
    MemoryRetrieval,
    MemoryStore,
    MemoryType,
)

# Observability
from sovereign_agent.observability import (
    ExecutorTrajectoryJudge,
    Judge,
    JudgeResult,
    MemoryUsageJudge,
    PlannerQualityJudge,
    TraceEvent,
    TraceReader,
    generate_session_report,
)

# Orchestrator
from sovereign_agent.orchestrator import Orchestrator, TaskResult, run_task
from sovereign_agent.orchestrator.lifecycle import (
    CloseResult,
    ExecResult,
    ExecutionLifecycle,
    InvocationSpec,
    LifecycleResult,
    LifecycleState,
    LifecycleTimeouts,
    RuntimeHandle,
    TerminalReason,
    WorkerRequest,
)

# Liveness monitor (v0.3 Module 4b)
from sovereign_agent.orchestrator.liveness import (
    LivenessMonitor as LivenessMonitor,
)

# Worker backends (v0.3 Module 4a)
from sovereign_agent.orchestrator.worker import (
    BareWorker as BareWorker,
)
from sovereign_agent.orchestrator.worker import (
    DockerWorker as DockerWorker,
)
from sovereign_agent.orchestrator.worker import (
    OSIsolatedWorker as OSIsolatedWorker,
)
from sovereign_agent.orchestrator.worker import (
    SubprocessWorker as SubprocessWorker,
)
from sovereign_agent.orchestrator.worker import (
    WorkerBackend as WorkerBackend,
)
from sovereign_agent.orchestrator.worker import (
    WorkerOutcome as WorkerOutcome,
)
from sovereign_agent.orchestrator.worker_factory import (
    make_worker_backend as make_worker_backend,
)

# Planner / Executor
from sovereign_agent.planner import DefaultPlanner, Planner, Subgoal

# Providers (v0.3 Unit 2)
from sovereign_agent.providers import (
    PROVIDER_REGISTRY,
    AgentProvider,
    ClaudeCodeProvider,
    CliProvider,
    CodexCliProvider,
    InvocationRequest,
    InvocationResult,
    NativeProvider,
    ProbeEvidence,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRegistry,
    ProviderToolResultEvent,
    ProviderUnavailable,
)

# Plugin registries (v0.3 Module 3)
from sovereign_agent.registries import Plugin as Plugin
from sovereign_agent.registries import Registry as Registry

# Seat registry (v0.3 Unit 6)
from sovereign_agent.registry import (
    RegistrationConflict,
    RegistryCorruptionError,
    RegistryError,
    RegistryValidationError,
    RuntimeAddress,
    Seat,
    SeatInstance,
    SeatInstanceNotFound,
    SeatLifecycle,
    SeatRegistry,
)

# Durable relay (v0.3 Unit 6)
from sovereign_agent.relay import (
    Acknowledgement,
    ClaimedMessage,
    DeliveryRecord,
    DeliveryStatus,
    DuplicateMessageConflict,
    DurableRelay,
    LeaseLost,
    MessageNotFound,
    Relay,
    RelayAuthenticationError,
    RelayCorruptionError,
    RelayError,
    RelayMessage,
    RelayValidationError,
)

# Repository execution (v0.3 Unit 5)
from sovereign_agent.repository import (
    DeliveryFailureReason,
    DeliveryResult,
    DeliveryState,
    DirtyWorktreePolicy,
    GitEvidence,
    RepositoryCommandError,
    RepositoryConfig,
    RepositoryConfigurationError,
    RepositoryDeliveryError,
    RepositoryDirtyError,
    RepositoryError,
    RepositoryExecution,
    RepositoryIdentity,
    RepositoryLease,
    RepositoryLockLost,
    RepositoryLockManager,
    RepositoryLockTimeout,
    RepositoryManager,
    RepositoryValidationError,
)

# Scheduler (Decision 6)
from sovereign_agent.scheduler import DriftCorrectedScheduler, ScheduledTask

# Session (Decision 1)
from sovereign_agent.session import (
    Session,
    SessionState,
    archive_session,
    create_session,
    list_sessions,
    load_session,
)

# SessionQueue (Decisions 2, 4, 8)
from sovereign_agent.session.queue import SessionQueue, TaskPriority

# Tickets (Decision 9 + Pattern D)
from sovereign_agent.tickets import (
    Manifest,
    OutputRecord,
    Ticket,
    TicketResult,
    TicketState,
    create_ticket,
    list_tickets,
)

# Tools
from sovereign_agent.tools import (
    ToolRegistry,
    ToolResult,
    global_registry,
    make_builtin_registry,
    register_tool,
)

__version__ = "0.5.0"

__all__ = [
    # errors
    "SovereignError",
    "SystemError",
    "ValidationError",
    "IOError",
    "ExternalError",
    "ToolError",
    "ErrorCategory",
    # discovery
    "Discoverable",
    "DiscoverySchema",
    "discoverable",
    # session
    "Session",
    "SessionState",
    "create_session",
    "load_session",
    "list_sessions",
    "archive_session",
    # queue
    "SessionQueue",
    "TaskPriority",
    # tickets
    "Ticket",
    "TicketState",
    "TicketResult",
    "Manifest",
    "OutputRecord",
    "create_ticket",
    "list_tickets",
    # ipc
    "IpcWatcher",
    "write_ipc_message",
    "send_input",
    # scheduler
    "DriftCorrectedScheduler",
    "ScheduledTask",
    # tools
    "ToolRegistry",
    "ToolResult",
    "register_tool",
    "global_registry",
    "make_builtin_registry",
    # capabilities (v0.5 ZeoCore adapter)
    "ApprovalDisposition",
    "CallableSurface",
    "CapabilityContextFactory",
    "CapabilityExecutor",
    "RuntimeCapabilityAssertion",
    "RuntimeCapabilityManifest",
    "RuntimeCommandRegistry",
    "make_session_callable_surface",
    # planner / executor
    "Planner",
    "Subgoal",
    "DefaultPlanner",
    # providers (v0.3 Unit 2)
    "AgentProvider",
    "ClaudeCodeProvider",
    "CliProvider",
    "CodexCliProvider",
    "InvocationRequest",
    "InvocationResult",
    "NativeProvider",
    "ProviderCapabilities",
    "ProviderEvent",
    "ProviderRegistry",
    "ProviderToolResultEvent",
    "ProviderUnavailable",
    "ProbeEvidence",
    "PROVIDER_REGISTRY",
    # governed execution (v0.3 Unit 7)
    "AdmissionRejected",
    "ExecutionNotFound",
    "ExecutionStatus",
    "GovernedExecutionEngine",
    "GovernedExecutionRequest",
    "ExecutionConstraints",
    "ExecutionReceipt",
    "ReceiptStatus",
    "ReceiptTermination",
    # repository execution (v0.3 Unit 5)
    "DeliveryFailureReason",
    "DeliveryResult",
    "DeliveryState",
    "DirtyWorktreePolicy",
    "GitEvidence",
    "RepositoryCommandError",
    "RepositoryConfig",
    "RepositoryConfigurationError",
    "RepositoryDeliveryError",
    "RepositoryDirtyError",
    "RepositoryError",
    "RepositoryExecution",
    "RepositoryIdentity",
    "RepositoryLease",
    "RepositoryLockLost",
    "RepositoryLockManager",
    "RepositoryLockTimeout",
    "RepositoryManager",
    "RepositoryValidationError",
    # registry and relay (v0.3 Unit 6)
    "RegistrationConflict",
    "RegistryCorruptionError",
    "RegistryError",
    "RegistryValidationError",
    "RuntimeAddress",
    "Seat",
    "SeatInstance",
    "SeatInstanceNotFound",
    "SeatLifecycle",
    "SeatRegistry",
    "Acknowledgement",
    "ClaimedMessage",
    "DeliveryRecord",
    "DeliveryStatus",
    "DuplicateMessageConflict",
    "DurableRelay",
    "LeaseLost",
    "MessageNotFound",
    "Relay",
    "RelayAuthenticationError",
    "RelayCorruptionError",
    "RelayError",
    "RelayMessage",
    "RelayValidationError",
    "Executor",
    "ExecutorResult",
    "DefaultExecutor",
    # halves
    "Half",
    "HalfResult",
    "LoopHalf",
    "StructuredHalf",
    "Rule",
    # handoff
    "Handoff",
    "write_handoff",
    "read_handoff",
    # orchestrator
    "Orchestrator",
    "TaskResult",
    "run_task",
    # config
    "Config",
    # observability
    "TraceEvent",
    "TraceReader",
    "Judge",
    "JudgeResult",
    "PlannerQualityJudge",
    "ExecutorTrajectoryJudge",
    "MemoryUsageJudge",
    "generate_session_report",
    # memory
    "MemoryType",
    "MemoryEntry",
    "MemoryStore",
    "MemoryRetrieval",
    "MemoryConsolidation",
    # plugin registries (v0.3 Module 3)
    "Plugin",
    "Registry",
    "CHANNEL_REGISTRY",
    # worker backends (v0.3 Module 4a)
    "WorkerBackend",
    "BareWorker",
    "SubprocessWorker",
    "DockerWorker",
    "OSIsolatedWorker",
    "WorkerOutcome",
    "make_worker_backend",
    "WorkerRequest",
    "RuntimeHandle",
    "InvocationSpec",
    "ExecResult",
    "CloseResult",
    "ExecutionLifecycle",
    "LifecycleResult",
    "LifecycleState",
    "LifecycleTimeouts",
    "TerminalReason",
    "__version__",
]
