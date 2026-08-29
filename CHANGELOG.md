# Changelog

All notable changes to sovereign-agent.

Repository: [`zeroemployeeorg/sovereign-agent`](https://github.com/zeroemployeeorg/sovereign-agent).

## Unreleased

### Curriculum completion, Chapters 0-7 (Unit 10)

Completes the promised curriculum range: four new chapters, each teaching
one already-ACCEPTED production concept from Units 7-9, instructor-note
machinery covering the whole completed range, a chapter-scoped (not
removed) Pulse-claim guard, and a genuine post-Unit-9 Andrea evaluation
task. **Zero new production behavior** -- every chapter exercise imports and
runs existing, already-ACCEPTED code; nothing was added to
`src/sovereign_agent/` or `src/reference_organizations/`.

- **Four new chapters**, each with a `solution.py` that imports and runs
  real production code (no teaching fork) and a `README.md` with real,
  executed command output:
  - `ch04_work_stays_inside_its_boundary` -- `safe_join`,
    `snapshot_boundary`/`diff_boundary`, `reclaim_workspace` and
    `workspace_policy` branching (Unit 7).
  - `ch05_authority_needs_a_fence` -- `acquire_actor_lease`,
    `acquire_execution_attempt`, and the stale-worker refusal path through
    the real `run_assignment` path with two genuinely separate
    `Organization` instances (Unit 8).
  - `ch06_the_organization_recovers` -- a REAL child process, REAL
    `SIGKILL` (the same fixture and polling discipline
    `tests/test_supervisor.py`'s own proof matrix uses), then
    `supervisor.tick` recovery -- never a guessed success (Unit 8).
  - `ch07_the_organization_wakes_itself` -- `run_pulse_once` end to end, no
    manual `create_sow`/`ready_sow`/`assign` call anywhere in the
    exercise, with the resulting `pulse.work_created` event and
    `pulse_origins`/`pulse_wake_decisions` rows read back from the ledger
    (Unit 9). The only chapter permitted to claim the organization woke
    itself, and only because its own run earns that claim.
- **Instructor-note machinery**, wholly new: `book/INSTRUCTOR.md` indexes
  every chapter's own `INSTRUCTOR.md` (all eight, including retroactively
  for Chapters 0-3), each carrying seven required sections -- teaching
  intent, prerequisite knowledge, likely misconceptions, observation
  checkpoints, discussion prompts, facilitation timing, exercise debrief
  and assessment guidance.
- **The Pulse guard becomes chapter-scoped, not removed.**
  `scripts/verify_curriculum.py`'s prior guard applied identically to
  every chapter regardless of number. Chapters 0-6 keep the exact
  unconditional prohibition. Chapter 7 may claim Pulse fired ONLY when its
  own already-executed exercise leaves durable, structured evidence in
  that run's own database: a real `pulse.*` event AND a traceable
  `pulse_origins` -> `pulse_wake_decisions` chain naming a real source
  signal -- re-derived by the gate itself from a fresh `sqlite3`
  connection, never trusted from the exercise's own printed summary. A
  claim with no such chain fails identically whether Pulse was never
  invoked or its evidence was fabricated by a direct `append_event` call.
- **New mechanical checks**: `REQUIRED_CHAPTERS` extended to 8; every
  chapter's `INSTRUCTOR.md` structurally checked for its seven sections;
  chapter forward/backward links and `book/README.md`'s own index checked
  for one coherent sequence (the prior gate only checked individual link
  resolution); no `book/**/*.md` file may begin with a site frontmatter
  block. Additive-only editing of Chapters 0-3 is explicitly left as a
  review-discipline requirement, not a mechanical check -- no heuristic
  here would actually prove the property it claims to.
- **Andrea evaluation extended.** `docs/andrea-alpha-evaluation.md` is
  preserved exactly as the historical Units 0-6.5 record (title, Task 7,
  and scoring key untouched), plus one additive link to the new document.
  `docs/andrea-chapters-0-7-evaluation.md` is new, with its own complete,
  replacement Task 7 assessing whether Andrea can explain and
  *independently verify* genuine proactive Pulse behaviour --
  mechanically validated by the new
  `scripts/evaluate_andrea_chapters_0_7.py`. Does not authorize or perform
  the Unit 12 Andrea soak.

Every new mechanical guarantee mutation-checked before this unit was
reported complete (a fabricated Pulse event; a Pulse claim in an early
chapter; a missing `INSTRUCTOR.md` section; a wrong-pointing forward link;
injected frontmatter -- each reproduced, confirmed caught, confirmed
landed via diff, restored byte-identical, reconfirmed green) -- see
[docs/v1-unit10-curriculum-completion.md](docs/v1-unit10-curriculum-completion.md)
for the full contract and proof matrix.

**Not claimed:** Chapters 8-12, any Unit 11 Store expansion or 30-day
pilot, any Unit 12 release work or the Andrea soak itself, credentialed
provider evidence, a mechanical check for additive-only Chapters 0-3
editing, any new runtime dependency, or any change to
`src/sovereign_agent/`'s own budget (unchanged: 27/40 modules, 6139/6250
lines, 7/30 exports).

### Pulse and proactive governed work (Unit 9)

Closes the gap between the manually dispatched Unit 5 Store pipeline and
sequencing amendment 5's proactive milestone: "sale → inventory signal →
deterministic wake gate → pulse → replenishment work created without a
human prompt." Pulse is a **distinct mechanism from the supervisor**, per
[the governing ruling](docs/rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md):
`supervisor.tick()` is unchanged, still never reads a Pulse signal or fires
a wake gate.

- **Signal stability.** A committed sale signal was previously replaced,
  not appended, when a later sale happened to leave inventory at the same
  level (`INSERT OR REPLACE`, keyed implicitly on a `dedupe_key` with no
  per-occurrence component) -- a source row Pulse origin could not safely
  reference durably. Now a plain, append-only `INSERT`, with a genuinely
  unique key per occurrence.
- **The canonical creation transaction, genuinely atomic.**
  `Organization.create_pulse_work` composes the wake-decision claim
  (`UNIQUE(source_signal_id)` at the SQLite boundary, not a preflight scan),
  the SOW's creation and transitions, the assignment, the genuine
  `pulse.work_created` event, and the origin row inside ONE `db.immediate()`
  transaction -- corrected from an original five-separate-commit shape
  (Sparring's finding F-U9-1 on PR #35, confirmed by independent Principal
  reproduction) that could durably strand a wake decision with no recovery
  path if an ordinary exception landed between any two commits. `create_sow`,
  `ready_sow`, and `assign` reuse connection-taking `_on` helpers shared with
  their own unchanged public, single-call form -- manual dispatch calls the
  exact same production methods it always did, never a copied or Pulse-only
  fork. In-transaction revalidation (re-asking the wake gate under the
  write lock, not merely before it) prevents stale work from a condition
  that resolved between the caller's read and the lock being acquired. A
  concurrent loser still returns the same SOW and assignment identifiers,
  never a second, competing pair, re-proven under the atomic design with a
  REAL two-connection `threading.Barrier` race.
- **The Pulse component and the Store's own wake gate.**
  `sovereign-agent pulse --once --root PATH` reads durable signals, asks a
  caller-supplied wake gate, and invokes the existing production
  `run_assignment()` path for qualifying work -- never bypassing Unit 8's
  actor-lease or execution-attempt fencing. The Store's own gate (a genuine
  sale-origin signal, still below reorder when re-checked live, mapped to
  exactly one active outcome) lives outside `sovereign_agent`'s own module
  budget, in `reference_organizations/store`.
- **Structured, durable origin.** Every SOW -- manual or Pulse-created, new
  or migrated -- carries an explicit `pulse_origins` row (`origin_kind`,
  `wake_decision_id`, `pulse_event_id`, `sow_id`, `assignment_id`). Absence
  of a row is never the definition of manual: `create_sow` inserts one for
  every SOW at creation time, and migration 15 backfills one for every
  pre-existing SOW.
- Migration 15: `pulse_wake_decisions`, `pulse_origins`, both append-only.

Tests grow from 281 to 332 (33 new in `tests/test_pulse.py` from the
initial implementation, 8 new migration tests in `tests/test_persistence.py`,
10 more in `tests/test_pulse.py` from the F-U9-1 correction below),
including a mutation-checked proof for every decisive property this unit
exists to protect (the fix reverted, the specific test confirmed red,
restored byte-identical, re-confirmed green) -- see
[docs/v1-unit9-pulse-proactive-work.md](docs/v1-unit9-pulse-proactive-work.md)
for the full contract and proof matrix.

**Review correction (PR #35, F-U9-1).** Sparring found, and the Principal
independently reproduced, that the canonical creation transaction was not
actually atomic: a fault between any two of its five original separate
commits durably stranded the wake decision, and `source_signal_id`'s own
`UNIQUE` constraint then made every retry impossible -- the signal was
orphaned permanently. Closed by composing all five writes into one
`db.immediate()` transaction (see above); the source-line budget was raised
from 6000 to 6250 to accommodate the honest cost of that composition
(`scripts/verify_source_budget.py`'s own comment records the ruling; module
and export ceilings are unchanged).

**Not claimed:** credentialed Claude/Codex/Cursor provider tests remain
deselected and unrun. No OS service, scheduling, cron, or webhooks. No
automatic retry policy for failed governed work.

### Supervisor, fencing, and hard-kill recovery (Unit 8)

A worker that no longer holds the current lease could still commit
completion, mutate canonical execution state, acknowledge mailbox work, or
reclaim the active workspace -- Unit 4's mailbox proved actor-level
idempotency, never process-level exclusivity, and named the gap rather than
build a supervisor to close it
([deferral ruling](docs/rulings/2026-08-26-deferral-unit4-fencing.md),
[one-process-per-actor ruling](docs/rulings/2026-08-26-one-process-per-actor.md)).
A hard-killed worker also left its assignment stuck `RUNNING` forever, since
"a process cannot record its own death" (Unit 5). This unit closes both.

- **Process identity and actor-hosting leases.** A fresh, random process
  identity (never a PID -- PIDs are reused by the operating system) and an
  exclusive, renewable lease per actor, both compare-and-set against SQLite
  with the same discipline `relay.claim()` already used. `organization.
  run_assignment` acquires (or renews) the actor's lease as the FIRST thing
  it does, before the workspace_policy check, before any symlink check,
  before the SOW or assignment state is touched -- the same validate-
  before-anything-touched slot Unit 7 established. A competing live process
  for the same actor is refused there, before workspace allocation, before
  the provider is ever invoked, proven with a REAL two-process test: two
  genuinely separate `Organization` instances, two different assignments
  for the same actor, the second process's provider invocation spied on
  with a counter and shown to fire zero times.
- **Execution-attempt fencing bound to the `RUNNING` transition, and bound
  to the actor lease.** A distinct fencing token per invocation, checked
  atomically inside the same SQLite transaction that commits
  `COMPLETED`/`BLOCKED`/`FAILED`, so a stale worker's subprocess -- fencing
  is not an OS sandbox, so it can still run to completion -- cannot make its
  result canonical. The execution attempt now records and re-verifies the
  actor lease's own fencing token at acquisition time, connecting the two
  CAS mechanisms rather than leaving them independent.
- **F-U4-1 closed.** `relay.claim()`'s same-owner short-circuit used to fire
  even when that owner's own lease had expired, so the CAS's expired-lease
  branch was unreachable by the owner. Now it only short-circuits when
  unexpired; an expired same-owner reclaim wins the CAS and mints a fresh
  token. `complete()`/`dead_letter()` verify that token atomically.
- **Hard-kill recovery, by the supervisor, never the dead process.** A new
  reconciliation loop (`sovereign-agent supervisor --root PATH [--once]`)
  detects a `RUNNING` assignment whose execution attempt expired with no
  valid current worker and recovers it: a durable `FAILED` receipt naming
  the expired attempt and `failure_category="worker_lost"` -- never a
  guessed success, however far the orphaned subprocess actually got --
  idempotent, and workspace reclaim applied only after the terminal write
  is durable. No new assignment or SOW state. Proven against a REAL child
  process and a real `SIGKILL`, never a preclassified refusal injection.
  Clean `SIGINT` handling in the long-running loop; no hidden
  daemonization. Distinct from `service` (future OS hosting, not
  implemented) and `pulse` (Unit 9's proactive wake, not implemented).
- Migration 13: `lease_tokens`, `actor_leases`, `execution_attempts`,
  `assignments.current_execution_attempt`, `messages.fencing_token`.

Tests grow from 230 to 274, including a mutation-checked proof for every
decisive property (the fix reverted, the specific test confirmed red,
restored byte-identical, re-confirmed green) -- see
[docs/v1-unit8-supervisor-fencing-recovery.md](docs/v1-unit8-supervisor-fencing-recovery.md)
for the full contract and proof matrix.

**Not claimed:** credentialed Claude/Codex/Cursor provider tests remain
deselected and unrun -- no live-provider evidence exists anywhere in this
unit. Fencing is a ledger guarantee, not a filesystem one: a worker that has
lost its lease can still write bytes to disk if its subprocess is still
running; only the ledger commit is refused.

### Cumulative conformance (Unit 6.5)

The simulated store now performs a **real** replenishment. Previously the demo
printed `ACCEPTED` while `SKU-TEA` sat at `on_hand=2` against a
`reorder_point=3`, with no purchase and no replenishment event: the governance
records were complete and the business claim was false.

- The store gains a validated `apply_restock` effect. Inventory increase,
  purchasing cash entry, signal resolution, and the `replenishment.committed`
  event commit in one SQLite transaction, and are idempotent per assignment.
  A provider may *propose* a bounded quantity; deterministic Python validates
  it and reads the unit cost from the product record, never from the provider.
- `verify_outcome` executes every declared acceptance check instead of only
  advancing a status field. Unknown, malformed, and erroring checks fail closed.
- Acceptance re-derives its own authority. It **re-executes** the declared
  checks against current state, requires successful evidence for every declared
  check bound to this outcome and execution, and refuses stale evidence. The
  caller-supplied `performer_id` argument is **removed**: performers are derived
  from assignments in the ledger, so separation cannot be satisfied by naming a
  convenient stranger.
- A small explicit check registry replaces the previous single evidence record
  whose name (`inventory_non_negative`) described inventory while its value was
  computed from cash. `cash_reconciles` now reconciles the purchase against the
  replenishment event rather than testing solvency.
- Events are append-only **at the database boundary, from any connection**:
  triggers refuse `UPDATE`, `DELETE`, and an `INSERT` whose id already exists.
  The first attempt closed the `INSERT OR REPLACE` bypass with
  `PRAGMA recursive_triggers`, which is per-connection — so a plain `sqlite3`
  shell, the tool Chapter 1 teaches, still silently overwrote events while the
  verifier reported "ACCEPTED and true". Migration 3 replaces that with a
  `BEFORE INSERT` guard needing no pragma, and a test that opens its own
  connection proves it. Evidence gains a foreign key, so a fabricated evidence
  id cannot be inserted at all.
- Named limits rather than silent ones: `docs/persistence-boundary.md` records
  that `outcomes` has no triggers, so an attacker with raw database write access
  can retarget `outcome.subject` and make all three checks pass coherently. The
  durable fix (binding subject into the evidence digest) is identified as the
  next step, not claimed as done.
- Migrations become forward-only and numbered. Migration 1 is unchanged;
  migration 2 adds the guards and evidence binding. Fresh-database and
  upgrade-from-v1 paths are both tested.
- Chapters 1 and 2 are written, Chapters 0 and 3 gain the required structure,
  and `scripts/verify_curriculum.py` detects missing sections, broken solution
  imports, and references to scripts that do not exist.
- New verification: `scripts/verify_store_outcome.py`,
  `scripts/verify_projections.py`, `scripts/evaluate_andrea_alpha.py`.

Tests grow from 59 to 98, including a falsification suite that proves acceptance
is refused for missing, failed, unrelated, unbound, stale, and fabricated
evidence, and a fault-injection suite that proves rollback after a partial write.

**Not claimed:** the credentialed provider smokes for Claude, Codex, and Cursor
have **not** been run. They remain a Unit 12 release gate. Installed is not
authenticated.

### Branch policy correction

`main` became the 1.x educational integration line when Units 0–6 merged. The
earlier holding that "`main` remains the 0.7 line" is superseded. Tag `v0.7.0`
remains immutable at `be2a41bbee202c52a40b2e87c00215827be302a0`; pin
`sovereign-agent<1` for the 0.x framework. No claim is made that 1.0 has met its
release gates. See
[docs/rulings/2026-08-25-main-is-the-1x-line.md](docs/rulings/2026-08-25-main-is-the-1x-line.md)
and [docs/persistence-boundary.md](docs/persistence-boundary.md).

### Providers (Unit 6)

Claude, Codex, and Cursor adapters implement `probe` / `build_invocation` /
`parse_event`. One provider-neutral envelope supplies actor identity,
authority, SOW, workspace/output boundaries, and the exact report schema.
Capability claims retain probe evidence and fail closed. Terminal events,
sessions, usage, malformed streams, reports, canonical receipts, and receipt
digests are validated by fake-executable integration tests. Credentialed live
assignments remain explicitly opt-in and outside default CI. Chapter 3 lands
with a runnable provider-rebinding exercise. Codex receives an authority-bound
writable sandbox, Claude receives `acceptEdits`, and Cursor receives `--force`
for the mandatory report; refusals and timeouts finalize durable failed
receipts; provider credentials use explicit environment allowlists.

### 1.x educational reset (authorization only)

Principal ruling 2026-08-25 authorizes Sovereign Agent 1.x as an executable
textbook. The v0.7 public API promise ends at the 0.x line. Tag `v0.7.0` is
not moved. Pin `sovereign-agent<1` for the old framework.

The 0.x non-goal “no governance decisions in this package” remains true for
v0.7 and is superseded for 1.x: the package may include the minimum
governance needed to teach and run one outcome. See
[docs/rulings/2026-08-25-educational-reset.md](docs/rulings/2026-08-25-educational-reset.md),
[docs/migration-v0.7-to-v1.md](docs/migration-v0.7-to-v1.md), and
[docs/non-goals.md](docs/non-goals.md).

No runtime or public-API code changes in this entry.

## [0.7.0] — 2026-08-23

Bounded production execution fleet on the v0.6 coordinator. Docker and
rootless Podman workers, authenticated SSH workers, fail-closed placement,
reservations, secret leases, network enforcement with evidence,
content-addressed artifacts, and reconciliation that forbids last-write-wins.
`DockerWorker` is no longer a stub. ZeoCore remains the capability contract
layer, not a scheduler. A git tag is not a public release until
`make verify-pypi`.

## [0.6.0] — 2026-08-23

Capability-native single-node default. `run_task` projects ZeoCore capabilities
and Sovereign runtime commands through a frozen per-execution catalog.
Approvals, durable concurrency leases, and invocation evidence survive restart.
`@register_tool` remains compatibility-only through 2027-02-23. Fleet work
stays in v0.7. A git tag is not a public release until `make verify-pypi`.

## [0.5.1] — 2026-08-23

Packaging and documentation truth for the v0.5 capability migration. Python
3.13 floor, `zeocore>=0.5,<0.6`, capability-first README, contract fixtures in
the wheel, and a ZeoCore min/newest CI job. Git tag `v0.5.0` is not moved and
is not announced as the PyPI line.

## [0.5.0] — 2026-08-23

Capability migration toward ZeoCore. Python 3.13 floor. Runtime evidence
types renamed to `RuntimeCapabilityManifest`. Reusable actions go through
ZeoCore; runtime commands stay in Sovereign. Legacy `register_tool` remains
through the compatibility window.

The 152-symbol v0.4 `__all__` surface is preserved; v0.5 adds 9 capability
symbols for 161 total.

## [0.4.0] — 2026-08-22

Durable local execution service on top of the v0.3 harness. HMAC-authenticated
Unix-socket API, serialized Zero Employee connector, relay v2 directory states,
seat supervision, durable approvals, webhook/Slack/email-draft channels,
allowlisted plugins, coordinator fencing, backup/restore, and copy-on-write
migration from v0.3 runtime roots. No Sandcastle. No multi-host workers.

The 152-symbol v0.3 `__all__` surface is preserved.

## [0.3.0] — 2026-08-22

The package, documentation, API manifest, wheel, and sdist declare v0.3.0.
Publishing remains a separate tag-triggered action; `make ready-to-ship` never
publishes or uses live credentials.

### Added

Landed on `main` on 2026-08-22 via
[PR #1](https://github.com/zeroemployeeorg/sovereign-agent/pull/1) and
[PR #2](https://github.com/zeroemployeeorg/sovereign-agent/pull/2). See
`docs/branch-consolidation-2026-08-22.md` for branch tips, merge commits, and a
correction to the `archive/pre-v0.3-runtime-stack-20260822` tag, which points at
a feature-branch tip rather than the pre-v0.3 state of `main`.

- Channel adapters: `ChannelAdapter` protocol, CLI adapter, inbound router. Only
  `CHANNEL_REGISTRY` is exported in `__all__`.
- Generic `Plugin` protocol and `Registry[T]`.
- Orchestrator dispatch routed through `WorkerBackend` via
  `make_worker_backend()`.
- Unit 3 worker lifecycle: provider-independent prepare/execute/close contracts,
  forward-only states, cancellation and bounded teardown, timeout reasons,
  fail-closed native isolation, allowlisted subprocess environments, and
  redacted diagnostics. See `docs/v0.3-unit3-worker-lifecycle.md`.
- Unit 4 native CLI providers: Codex CLI JSONL and Claude Code stream-json
  adapters, evidence-bearing version/help probes, capability-gated fresh and
  resumed sessions, capability-gated Claude session fork, strict normalized
  event parsing, observer containment, and execution through the Unit 3 backend
  seam without Sandcastle or `shell=True`. Default tests use committed fixtures
  and fake backends; zero-token live help/version probes are opt in and do not
  run in CI. See `docs/v0.3-unit4-cli-providers.md`.
- Unit 5 governed repository execution: configured `RepositoryId` resolution,
  fail-closed dirty policies, isolated execution branches and worktrees,
  durable fenced repository leases, deterministic redacted Git evidence, and
  opt-in non-force delivery with exact remote-SHA verification. See
  `docs/v0.3-unit5-repository.md`.
- Unit 6 persistent seat registry and durable local relay: immutable
  registration identity (including sovereign-session and provider-session
  bindings), atomic heartbeats, liveness inspection, validated local
  addressing, conversation/reply envelopes, artifact references, expiry,
  idempotent enqueue, ordered fenced claims, ack/nack, bounded backoff,
  lease recovery, dead letters, acknowledgement records and explicit
  corruption quarantine. See `docs/v0.3-unit6-registry-relay.md`.
- Unit 7 governed execution handshake: typed `GovernedExecutionRequest` /
  `ExecutionReceipt` fields, admission that refuses before invocation,
  repository execution under lock, provider/worker composition, and CLI
  `seat`/`execute`/`execution`/`receipt`/`relay` commands (with `governed`
  aliases). See `docs/v0.3-unit7-governed-execution.md`.
- `LivenessMonitor` — stalled-session detection and heartbeat. Importable but not
  in `__all__`.
- Move to `src/` layout.

`sovereign_agent.__all__` now has 152 public symbols, up from the 67 that shipped
in 0.2.0. Every v0.2 symbol remains and the 85 additions enter the v0.3
compatibility contract.

### Release readiness

- Added machine-readable v0.2 and v0.3 API manifests and a gate comparing them
  with `__all__`.
- Added a v0.2 migration guide, threat model, explicit teaching-surface decision,
  release-note fragments, and a no-deprecations declaration.
- `make ready-to-ship` now runs deterministic CI, strict docs, distribution
  content checks, and a clean core-only wheel install. The smoke test validates
  packaged schemas and rejects import-time filesystem, network, and process side
  effects.

### Documentation and truth repair

- Repository identity updated to `zeroemployeeorg` across `README.md`,
  `pyproject.toml` URLs, `mkdocs.yml`, and the docs tree. Old
  `sovereignagents/...` links still resolve by GitHub redirect but are no longer
  canonical.
- Corrected test-count claims: the suite collects **500** tests (497 pass, 3
  opt-in/platform skips), including skipped-by-default live provider probes.
  Previous docs claimed 267, 220, and 120 in different places.
- Corrected public-API claims: **152** symbols in `__all__`, of which 67 are the
  stable 0.2.0 surface. `docs/API.md` now lists both sets separately, and names
  the v0.3 symbols that are importable but not in `__all__`.
- Removed links to files that do not exist: `docs/class-slides.md`,
  `CONTRIBUTING.md`, and a root `SOW.md`.
- Replaced the "authoritative SOW in the repo root" framing in
  `docs/architecture.md` with the work-repo/corpus boundary: this repository is
  `work_repo` and holds code; scoping and reporting live in a separate
  `sow_repo`. No corpus path is hard-coded here, by design.
- Docker is labelled unavailable everywhere it appears. `DockerWorker` docstrings
  now say "unimplemented stub" rather than "v0.4 stub", and the raised
  `NotImplementedError` states that no container code path exists.
- Corrected the install instructions: dev tooling is a PEP 735 dependency
  *group*, so `pip install "sovereign-agent[dev]"` was never a real extra.
- Added `docs/v0.3-non-goals.md` — normative scope boundaries for v0.3,
  including an explicit prohibition on introducing Sandcastle in any form.
- Added `docs/branch-consolidation-2026-08-22.md`.

### Packaging

- **`docker` removed from the `all` meta-extra.** `pip install
  "sovereign-agent[all]"` no longer pulls the Docker SDK, because there is no
  Docker code path for it to support. The `docker` extra itself is retained so
  the dependency stays declared in one place. Install it explicitly if you need
  the SDK for your own reasons: `pip install "sovereign-agent[docker]"`.

### Not implemented, despite having a name

Recorded here so the gap is documented rather than inferred:

- `DockerWorker` — stub; `run_session()` raises `NotImplementedError`.
- Evidently and OpenTelemetry observability backends — import-gated stubs.
- Voice pipeline — protocol only.
- `MemoryRetrieval` / `MemoryConsolidation` — class shells, no behaviour.
- `lessons/` — a template and a rationale README; no lesson has been written.

## [0.2.0] — 2026-04-24

Released to PyPI as the only published release. Tag `v0.2.0` →
`9d934cf53ff223175d01ebf07483fd608fae66a0`.

Contents are as described under `[0.2.0-alpha]` below; the alpha entry was the
working record and was never rewritten at tag time. Two claims in that entry were
accurate when written and are no longer accurate for the current tree — the test
count (220 then, 370 now) and the public-symbol count (67 then, 76 now).

## [0.2.0-alpha] — 2026-04-24

Historical record, kept as written. Counts and claims in this entry describe the
tree at 0.2.0 and are not a description of `main` today; see `[Unreleased]` above.

v0.2 focuses on five capabilities students asked about in the first-cohort
class: parallel tool calls, process isolation without Docker, session
resume, pluggable rule verifiers, and human-in-the-loop approval. All
five ship as additive features — every v0.1.0 scenario still works
unchanged.

### Module 1 — Parallelism

- `_RegisteredTool.parallel_safe: bool = True` declares whether a tool
  may run concurrently with other tools in the same ReAct turn.
- `DefaultExecutor(parallelism_policy=...)` accepts `"respect_tool_flags"`
  (default), `"never"`, or `"always"`.
- Execution groups contiguous `parallel_safe=True` calls into an
  `asyncio.gather`; unsafe calls (writes, handoffs, `complete_task`)
  break the batch and run alone.
- Output ordering is preserved regardless of completion order, so the
  LLM sees tool results in the order it requested them.
- `_RegisteredTool.verify_args` is a new optional hook that runs before
  the tool body and can reject bad arguments with a structured reason.

### Module 2 — Process isolation (no Docker)

- New `WorkerBackend` protocol (`sovereign_agent.orchestrator.worker`)
  decouples "how a step runs" from "where a step runs". `BareWorker`
  (in-process), `SubprocessWorker` (separate Python process), and any
  future backend share the same shape.
- `sovereign_agent.orchestrator.worker_entrypoint` — a small standalone
  module invoked as `python -m ...` — is the common target. It
  advances exactly one step and prints a JSON summary as its last line
  of stdout.
- **`LandlockPolicy`** (Linux ≥ 5.13) wraps the command in a shim that
  calls `landlock_create_ruleset` / `add_rule` / `restrict_self` via
  `ctypes` before `exec`ing the real payload. No pypi dependency on a
  Landlock library, no daemon, no container runtime. Kernel-enforced
  filesystem isolation.
- **`SandboxExecPolicy`** (macOS) generates a `.sb` profile and wraps
  the command in `sandbox-exec -f`. Uses Apple's own sandbox framework
  — the same one confining App Store apps.
- `detect_best_policy()` picks the strongest available primitive for
  the host and falls back to `NoOpPolicy` (with a loud warning) on
  unsupported platforms.
- Fail-closed by design: the Landlock shim exits non-zero if Landlock
  isn't available rather than running the child unprotected.

### Module 3 — Session resume

- `SessionState.resumed_from: str | None` records a pointer from child
  to parent session. Parent is untouched (forward-only rule).
- `resume_session(parent_id, task, ...)` creates a linked child
  session, refusing to resume from non-terminal parents unless
  `allow_unfinished_parent=True`.
- `Session.parent_session()` returns a handle for the parent or `None`
  if it has been archived/deleted.
- `find_ancestor_chain(session)` walks multi-level resume chains
  oldest-first and is defensive against cycles and missing ancestors.
- Parent context summary (trace tail, tickets, final result) is
  auto-inlined at the top of the child's `SESSION.md` so the planner
  sees it on first read.
- New CLI command: `sovereign-agent sessions resume <parent_id>`.

### Module 4 — Verifier protocol

- New `Verifier` protocol (`sovereign_agent.halves.verifiers`) with
  a single async `evaluate(data) -> VerifierResult` method.
- Three concrete implementations: `LambdaVerifier` (wraps any callable),
  `ClassifierVerifier` (sklearn `predict_proba` or transformers
  pipeline `__call__`), `LLMJudgeVerifier` (uses an LLM with defensive
  JSON parsing).
- `Rule.condition` and `Rule.escalate_if` now accept either a callable
  (legacy) or a `Verifier` (new). Backward-compatible.
- `VerifierResult` carries a `reason` and optional numeric `score` that
  surface in `HalfResult.output` — the structured audit trail for
  probabilistic rule decisions.

### Module 5 — Human-in-the-loop

- `ToolResult.requires_human_approval: bool = False` makes any tool
  able to pause the session.
- Executor writes `ipc/awaiting_approval/<request_id>.json` and exits
  cleanly when it sees the flag. No coroutine holds state across the
  wait — the session can idle for hours or days.
- `ApprovalRequest` includes a SHA-256 of the tool arguments so the
  approver is granting a specific invocation, not a general action.
- `ApprovalResponse.override_output` lets approvers modify the tool's
  proposed output instead of just accepting or denying it.
- Double audit trail: ephemeral IPC files plus permanent
  `logs/approvals/`.
- New CLI commands: `sovereign-agent approvals {list,grant,deny}`.
- `resume_from_approval(executor, subgoal, session, request_id)` runs a
  fresh ReAct turn whose opening user message includes the decision,
  letting the LLM adapt on denial or continue on grant.

### Tests

100 new unit tests across the five modules — 9 parallelism, 14
approval, 23 verifier, 23 resume, 11 worker, 20 isolation — bringing
the total to **220 tests**, all passing.

### Examples

One end-to-end example per module, each self-contained (no real LLM
credentials required by default) and wired into the Makefile:

- `examples/parallel_research/` — five arXiv lookups; 0.33s parallel
  vs 1.54s sequential (~4.7× speedup). `make example-parallel-research`.
- `examples/isolated_worker/` — subprocess worker under
  `detect_best_policy()`; probe shows session-dir writes succeed and
  `/etc/shadow` / `/etc/hosts` reads are denied on a working sandbox.
  `make example-isolated-worker`.
- `examples/session_resume_chain/` — three-generation parent →
  child → grandchild chain with auto-prepended parent context in
  SESSION.md and forward-only rule verification.
  `make example-session-resume-chain`.
- `examples/classifier_rule/` — StructuredHalf rule driven by a
  `ClassifierVerifier`; six manager-reply strings classified correctly;
  verifier score and reason surface in the audit trail.
  `make example-classifier-rule`.
- `examples/hitl_deposit/` — full grant-and-deny flow through the real
  CLI (`sovereign-agent approvals grant|deny`) with
  `resume_from_approval()` on the other side. `make example-hitl-deposit`.

### Sessions and artifacts

- Demos and `--real` examples now write session artifacts to the platform's
  user-data directory (`~/.local/share/sovereign-agent/...` on Linux,
  `~/Library/Application Support/sovereign-agent/...` on macOS,
  `%LOCALAPPDATA%\sovereign-agent\...` on Windows) instead of either the repo
  root or a tempdir. Override with `SOVEREIGN_AGENT_DATA_DIR=<path>`.
- New `sovereign_agent._internal.paths.example_sessions_dir(name, persist=)`
  context manager encapsulates the policy: `persist=True` yields a stable
  user-data path, `persist=False` yields a tempdir. Four built-in examples
  (`research_assistant`, `code_reviewer`, `pub_booking`, `parallel_research`)
  use it to route `--real` runs to persistent storage and offline runs to
  tempdirs.
- Offline examples continue to use tempdirs (no change).
- Production (`sovereign-agent run`, `sovereign-agent serve`) continues to
  honour `Config.sessions_dir` / `SOVEREIGN_AGENT_SESSIONS_DIR` (no change).
- README adds a "Where things live" section documenting this.

### Documentation

- `chapters/README.md` now explicitly frames the Raschka pattern (chapters
  in-tree, `solution.py` re-exports from `sovereign_agent/`, drift-checked by
  CI) versus the Howard pattern (separate course repo using the published
  library). Clarifies why chapters live here while homework lives elsewhere.
- `docs/API.md` clarifies the public-API contract: 67 symbols in
  `sovereign_agent.__all__`, semver applied to that surface, everything under
  `sovereign_agent._internal/` may change between patch releases.

### Packaging

- First pypi release of `sovereign-agent` (pypi package name matches repo name;
  import path `sovereign_agent`). Trusted publisher via GitHub Actions OIDC;
  no API tokens in the repo.
- `pip install sovereign-agent[all]` installs evidently, otel, voice, and
  docker extras. `[rasa]` is intentionally NOT in `all` because `rasa-pro`'s
  pin set conflicts with several other extras. (Superseded: `docker` was later
  removed from `all` too — see `[Unreleased]`.)
- Python 3.12+ required.

### Breaking changes

None. Every public API from v0.1.0 still works with the same signature.

---

## [0.1.0] — unreleased (alpha)

Initial scaffold. This is the first working implementation of the architecture specified in `docs/architecture.md`.

### Implemented

- **Session substrate** (`sovereign_agent.session`): atomic `session.json` writes, traversal-safe `path()`, trace-event append, subdirectory layout.
- **Session queue** (`sovereign_agent.session.queue`): per-session serialization, global concurrency cap, retry with exponential backoff, idle preemption via `_close` sentinel, graceful shutdown (detach, do not kill).
- **Tickets** (`sovereign_agent.tickets`): explicit state machine (pending/running/success/skipped/error), sha256 manifest verification ("no manifest, no success"), LLM-readable summaries.
- **IPC** (`sovereign_agent.ipc`): filesystem IPC with atomic rename, `IpcWatcher` polling loop, per-session error isolation, quarantine of malformed files.
- **Errors** (`sovereign_agent.errors`): structured taxonomy (SYS / VAL / IO / EXT / TOOL) with machine-readable codes.
- **Discovery** (`sovereign_agent.discovery`): Discoverable protocol with schema validation.
- **Scheduler** (`sovereign_agent.scheduler`): drift-corrected recurring tasks, interval and cron, skip-ahead on missed intervals.
- **Tools** (`sovereign_agent.tools`): `@register_tool` decorator with auto-discovery from signature, builtin read/write/list/search/write-memory/handoff/complete tools.
- **Planner and Executor** (`sovereign_agent.planner`, `sovereign_agent.executor`): two-stage ReAct with real OpenAI-compatible client, `FakeLLMClient` for tests.
- **Loop half** (`sovereign_agent.halves.loop`): planner + executor composition.
- **Handoff** (`sovereign_agent.handoff`): file-based protocol with fail-closed on duplicate files and archive to audit log.
- **Orchestrator** (`sovereign_agent.orchestrator`): state dispatch, resume-from-disk, SIGTERM handling.
- **CLI** (`sovereign_agent.cli`): `run`, `serve`, `doctor`, `report`, `sessions`, `version`.
- **Config** (`sovereign_agent.config`): env loading, TOML loading, validate().

### Skeletons (API stubbed, behavior TODO)

- **Memory subsystem** (`sovereign_agent.memory`): MemoryStore/Retrieval/Consolidation class shells.
- **Structured half** (`sovereign_agent.halves.structured`): minimal rule-list evaluator.
- **Observability** (`sovereign_agent.observability`): JSONL trace reader and session-report generator; Evidently and OTel backends are import-gated stubs.
- **Voice** (`sovereign_agent.voice`): protocol definition only; Speechmatics/ElevenLabs implementation is a stub.
- **Mount allowlist** (`sovereign_agent.orchestrator.mounts`): default patterns and validate() scaffold.
- **Credential gateway** (`sovereign_agent.orchestrator.credentials`): basic env loading; per-tool scoping TODO.

### Not yet started

- Full mkdocs site beyond the architecture copy (quickstart, deployment, API reference).
- Docker worker spawning in `orchestrator/main.py` (the containerized execution path mentioned in `bare_mode` config).
- Per-tool credential scoping in `orchestrator/credentials.py` (the gateway scaffolds the env-loading; the per-tool allowlist is the TODO).

### Verified working in this release

- `ruff check sovereign_agent/ tests/ chapters/ examples/` — clean.
- `pytest` — 148 tests pass in ~7 s.
- `python tools/verify_chapter_drift.py` — all 5 chapters match production.
- All 5 chapter demos (`python -m chapters.<N>_*.demo`) run end-to-end.
- All 3 example scenarios (`research_assistant`, `code_reviewer`, `pub_booking` with both default and `--oversize`) run end-to-end.
- `sovereign-agent doctor --skip-llm` passes with a fake API key.
