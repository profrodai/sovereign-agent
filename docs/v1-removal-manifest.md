# v1 removal manifest (from v0.7)

Maps every v0.7 top-level subsystem to **retain as a 1.x concept**, **rewrite
into a smaller module**, or **remove** from Sovereign Agent 1.x. This is not a
compatibility table. 1.0 may drop every v0.7 public symbol.

Public names at v0.7 are listed in [public-api-v0.7.txt](public-api-v0.7.txt)
(165 lines including `__version__`).

## Top-level packages and modules

| v0.7 path | 1.x action | Reason |
| --- | --- | --- |
| `session/` | Rewrite | Keep inspectable run artifacts around outcome/run terminology; SQLite is the operational ledger |
| `tickets/` | Rewrite | Smaller evidence/receipt/manifest models |
| `approvals/` | Rewrite | Digest-bound approvals remain central |
| `providers/` | Rewrite | Smaller `IntelligenceProvider` contract; keep Claude/Codex probe knowledge; add Cursor |
| `relay/` | Rewrite | Actor mailbox with claims, leases, dead letters |
| `registry/` / `registries/` | Rewrite | Actor registry and role bindings, not seat-fleet supervision |
| `repository/` | Rewrite (subset) | Local git worktrees and ownership checks only |
| `_internal/atomic.py` and file writes | Rewrite | stdlib atomic projections and artifacts |
| `cli/` | Replace | argparse; no Typer |
| `config.py` | Replace | committed `sovereign.toml`; no secrets in governance |
| `errors.py` | Replace | typed refusals that teach the invariant |
| `contracts/` | Remove as ZeoCore-shaped package | 1.x owns its Pydantic models; optional later JSON fixtures without importing ZeoCore |
| `capabilities/` | Remove | No second capability framework; no ZeoCore runtime dependency |
| `executor/` / `planner/` / `halves/` / `handoff/` | Remove | v0.2 substrate is not the 1.x teaching core |
| `ipc/` | Remove | Not needed for local educational outcomes |
| `tools/` / `discovery.py` | Remove | `@register_tool` compatibility window ends with 0.x |
| `orchestrator/` / `workers/` / `fleet/` | Remove | No Docker, Podman, SSH, or fleet scheduling in 1.x |
| `api/` | Remove | No HTTP or Unix-socket control plane |
| `channels/` | Remove | No Slack, email, webhooks in core |
| `connectors/` | Remove from core | Store uses a command-connector boundary in `reference_organizations/store/` |
| `voice/` / `memory/` / `observability/` | Remove | Unimplemented or non-teaching surface |
| `plugins/` | Remove | No plugin marketplace |
| `admission/` | Remove as standalone product | Authority lives in 1.x `policy.py` / governance |
| `secrets/` | Remove | No general-purpose secrets product |
| `artifacts/` | Rewrite (subset) | SHA-256 manifests for promoted evidence |
| `execution/` | Rewrite | Bounded subprocess argv arrays; fail-closed receipts |
| `scheduler/` | Replace | `Every`, `DailyAt`, `OnEvent` only; no croniter |
| `service/` | Replace | Explicit per-user `service install\|status\|uninstall`; runtime loop is `supervisor` |
| `runtime/` / `operations/` | Remove or absorb | 1.x uses `.sovereign/` + SQLite, not v0.4 runtime-root fencing as the teaching model |
| `_internal/llm_client.py` | Remove | No OpenAI-compatible SDK client |
| `_internal/isolation.py` / landlock | Remove from 1.0 core | Governance is not sandboxing; record requested provider sandbox, do not claim to strengthen it |

## v0.7 public concepts (grouped)

| Concept | 1.x action |
| --- | --- |
| Session directory as inspectable state | Retain as file artifacts around outcome/run; not the operational database |
| Atomic file writes and JSONL traces | Retain for projections, evidence, and export |
| Tickets, receipts, manifests, approvals | Retain as smaller models |
| Claude and Codex CLI adapters | Rewrite into the smaller provider contract |
| Cursor | Add as first-class adapter (absent in v0.7) |
| Seat registry and relay | Retain as actor registry and mailbox |
| Git repository/worktree execution | Retain local subset |
| ZeoCore runtime dependency | Remove |
| Direct OpenAI-compatible LLM client | Remove |
| Typer | Replace with argparse |
| croniter / python-dateutil | Remove |
| Fleet, Docker, Podman, SSH | Remove from 1.x core |
| API server and channels | Remove |
| Voice, memory, observability skeletons | Remove |
| 161-name root API | Replace with ≤30 deliberate names |

## Pin path

`pip install "sovereign-agent<1"` remains the documented old-line path.
