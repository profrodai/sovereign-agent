# SOW: Sovereign Agent 1.x — Unit 9 Pulse and proactive governed work

```yaml
sow: sovereign-agent-v1-unit9-pulse-proactive-work
project: sovereign-agent
unit: 9
status: AUTHORIZED_ON_MERGE
authority: principal
base_commit: 9fbc8f7e2c55c6949ec1c36238bc46faa35f4f7e
governing_ruling: docs/rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md
work_branch: unit-9/pulse-proactive-work
runtime: Python 3.14
runtime_dependencies:
  - pydantic
```

## Authorization

This SOW is the Principal's implementation direction for Unit 9.

Before implementation begins, file this SOW in the repository, route it through Sparring review, and merge the reviewed text into `main`. Implementation begins from that resulting exact merged commit—not from the drafting branch and not from `9fbc8f7e` if `main` has advanced.

A changed SOW head invalidates an earlier co-sign. Branch reconciliation must use an allowed, auditable PR-based mechanism; do not substitute a local history rewrite for the denied `git rebase`, `git merge`, or force-push mechanisms.

## Mission

Close the gap between the manually dispatched Unit 5 Store pipeline and the proactive milestone ratified by sequencing amendment 5:

```text
sale
→ durable inventory signal
→ deterministic wake gate
→ genuine durable Pulse event
→ governed replenishment work created without a human prompt
→ Scripted Operator
→ deterministic effect boundary
→ evidence
→ independent review
→ acceptance
```

Unit 9 builds the first four previously missing links and connects them to the existing governed-work path. It does not replace that path and does not create a second teaching implementation.

## Binding interpretation

### Pulse is separate from the supervisor

Create a distinct Pulse mechanism under the reserved `pulse` CLI surface.

Do not add Pulse imports, wake-gate reads, work creation, or Pulse event writes to `Supervisor.tick()`. After Unit 9 lands, these accepted Unit 8 statements must remain literally true:

> The supervisor never creates work, never reads a Pulse signal, never fires a wake gate.

A future foreground runtime may call the supervisor and Pulse as two distinct operations. It may not disguise Pulse as a fourth supervisor reconciliation step.

### Pulse origin is an indexed ledger fact

The canonical ledger must answer, with structured columns and enforced relationships:

* Was this SOW manually planned or Pulse-created?
* Was this assignment manually dispatched or Pulse-created?
* Which source signal and committed source event caused the wake decision?
* Which deterministic decision fired?
* Which genuine `pulse.*` event records that firing?
* Which SOW and assignment were created?

Absence of a CLI invocation, process logs, JSON payload inspection, and absence of a manual-origin row are not proof.

Use explicit equivalents of:

```text
origin_kind
source_signal_id
source_event_id
wake_decision_id
pulse_event_id
sow_id
assignment_id
```

Existing manual work must migrate to an explicit `manual` origin. "No Pulse-origin row exists" must never be the definition of manual.

## Required implementation

### 1. Pulse component

Add one production Pulse mechanism, separate from `supervisor.py`.

Its deterministic one-pass operation must be available through:

```bash
sovereign-agent pulse --once --root ORGANIZATION_ROOT
```

Exact supporting flags may be added only when needed for durable configuration or unambiguous actor selection. The command must not ask the user to author or dispatch a SOW.

A pass must:

1. Read durable signals and current authoritative Store state.
2. Select qualifying signals deterministically.
3. Evaluate the Store wake gate.
4. Atomically claim the canonical decision and create its SOW, assignment, Pulse event, and origin links.
5. Invoke the existing production `Organization.run_assignment()` path for a newly created or safely resumable `CREATED` assignment.
6. Return a structured report identifying created, replayed, skipped, refused, or already-running work.

The Scripted provider remains the offline proof provider. Do not introduce a provider-specific execution fork.

### 2. Store wake gate

For this unit, a qualifying trigger is a genuine sale-origin `inventory.changed` signal whose subject is currently below its reorder point and can be mapped unambiguously to an active governed outcome.

The gate must fail closed when:

* no qualifying signal exists;
* the subject is no longer below reorder;
* the source signal or source event is missing or inconsistent;
* no active outcome matches;
* more than one outcome matches and no durable rule disambiguates them;
* the configured planner or operator lacks the required authority.

A non-qualifying pass creates no SOW, assignment, origin row, or `pulse.*` event.

The existing `below_reorder()` behavior is inherited. Do not create a second reorder calculation that can drift from it.

### 3. Canonical creation transaction

The wake decision, Pulse event, SOW, assignment, and origin links must become durable atomically.

Refactor existing Organization construction/state-transition helpers if necessary so manual and Pulse creation share production logic. Do not copy `create_sow()`, `ready_sow()`, or `assign()` into a teaching or Pulse-only fork.

The transaction must enforce at least:

* one canonical wake decision per source signal;
* one Pulse event per fired decision;
* one initial SOW and assignment per fired decision;
* foreign-key-valid links to the source signal, source event, outcome, SOW, assignment, and Pulse event;
* explicit `pulse` origin on the created SOW and assignment;
* uniqueness at the SQLite boundary, not through a preflight scan.

Concurrent contenders must either return the same canonical identifiers or report that the canonical work is already running. They must not create parallel work.

### 4. Signal stability

Pulse origin cannot safely reference a source row that later disappears through `INSERT OR REPLACE`.

Make committed sale signals stable enough to be referenced durably. A later sale that reaches the same inventory level must not replace or rewrite the earlier signal that already caused work. Preserve existing Unit 2–6 transaction guarantees: the sale, cash movement, inventory mutation, signal, and `sale.committed` event remain one atomic transaction.

Any migration of existing signal data must preserve all valid rows and fail closed—without stamping the migration—if a required relationship cannot be reconstructed honestly.

### 5. Replay, restart, and recovery

The same qualifying signal must resolve to the same canonical work under:

* repeated evaluation in one process;
* closing and reopening the organization;
* two independent processes evaluating concurrently;
* a crash after canonical creation but before provider invocation;
* a retry while the canonical assignment is already `RUNNING`;
* replay after the canonical assignment is terminal.

Required behavior:

| Canonical assignment state | Pulse replay behavior                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------- |
| `CREATED`                  | May invoke that same assignment; never create another                                 |
| `RUNNING`                  | Report existing work; do not bypass Unit 8 fencing                                    |
| `COMPLETED`                | Return the existing result; do not invoke again                                       |
| `BLOCKED` / `FAILED`       | Preserve the canonical failure; do not guess success or silently create a replacement |

Recovery or reassignment after a failed execution continues through the existing governed state machine. Pulse does not invent an automatic retry policy.

### 6. Genuine Pulse events only

Unit 9 may introduce genuine `pulse.*` event kinds, emitted only by the production Pulse mechanism after the wake gate fires.

Tests must not manufacture Pulse success by calling `append_event("pulse.…")`, inserting a Pulse event directly, or preloading a classified Pulse result. They must cause the real sale, real signal, real gate, and real creation transaction to run.

Outside that mechanism, the source tree remains Pulse-clean.

### 7. Reference Store proof

Add an offline reference scenario proving the complete proactive slice:

1. Initialize and seed the Store.
2. Create and activate the stocked-inventory outcome.
3. Commit a real sale that crosses the reorder point.
4. Run the production Pulse command or component.
5. Observe a Pulse-origin SOW and assignment created without a manual `plan` or `run` command.
6. Run the real Scripted provider through `Organization.run_assignment()`.
7. Parse its real report through the existing trusted parser.
8. Apply the proposal through the existing deterministic `apply_restock()` boundary.
9. Run verification, independent review, and acceptance through existing production methods.
10. Prove the outcome is `ACCEPTED` and the attribution chain remains queryable afterward.

Pulse must not itself impersonate Sparring or the Principal. The reference scenario may drive the already-existing simulated teaching actors, as the current Store demo does.

## Persistence and migration requirements

Ship a new forward-only migration after migration 14.

The exact table names may differ, but the resulting schema must expose equivalent indexed facts:

| Fact                   | Required enforcement                             |
| ---------------------- | ------------------------------------------------ |
| Manual or Pulse origin | Non-null structured value                        |
| Source signal          | Foreign key or equally strong enforced reference |
| Source committed event | Foreign key to `events`                          |
| Wake decision          | Stable unique identifier                         |
| Pulse event            | Unique reference to a genuine `pulse.*` event    |
| Created SOW            | Unique foreign key                               |
| Created assignment     | Unique foreign key                               |
| Replay key             | Unique at the database boundary                  |

Pulse attribution is proof-bearing. Its canonical relation must be append-only and receive update, delete, and replace guards in the migration that introduces it. Do not edit a previously applied migration.

Add migration tests for:

* fresh database installation;
* populated Unit 8 database upgrade;
* preservation and explicit manual-origin backfill;
* migration rollback on malformed or unattributable legacy data;
* frozen migration bytes;
* foreign-key, uniqueness, and append-only enforcement;
* indexed record and serialized model agreement.

## Required proof matrix

At minimum, tests must establish all neighboring cases below.

| Property                 | Required cases                                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| Separate mechanism       | `pulse --once` works; `Supervisor.tick()` still creates no work and emits no Pulse event                                |
| No creation from nothing | Empty organization; seeded Store with no sale; sale remaining above reorder                                             |
| Qualification             | Real sale crossing the threshold creates canonical proactive work                                                       |
| Current-state check      | A formerly qualifying signal does not create work after the condition is already resolved                               |
| Attribution               | Structured query walks source event → signal → decision → Pulse event → SOW → assignment                                |
| Manual attribution        | Existing and newly created manual work says `manual` explicitly                                                         |
| Replay                    | Same-process replay returns the same identifiers and counts remain one                                                  |
| Restart                   | Reopen the database and replay; counts and identifiers remain one                                                       |
| Concurrency                | Two real processes evaluate the same signal; one canonical creation, at most one provider invocation                    |
| Crash window              | Canonical `CREATED` work survives restart and resumes without duplication                                               |
| Existing RUNNING work     | Pulse does not bypass actor leases or execution-attempt fencing                                                         |
| Terminal work             | Completed, blocked, and failed canonical assignments are not rerun or replaced                                          |
| Source integrity          | Missing, mismatched, or fabricated source relationships fail closed                                                     |
| Ledger integrity          | FK, unique, append-only, and record/column disagreement tests                                                           |
| Recurrence                | A later genuine sale reaching a previously seen inventory level retains the old signal and can create distinct new work |
| Real mechanism            | No test fabricates a `pulse.*` event or injects a pre-classified wake result                                            |
| Full teaching slice       | Real Pulse-created Scripted work reaches verified, reviewed, truthful acceptance                                        |
| CLI artifact               | Built wheel runs `pulse --once` outside the repository                                                                  |

For every central property, falsify the implementation deliberately and assert that the named test becomes red. Confirm the mutation actually changed the intended bytes before interpreting the result. Restore byte-identically and rerun.

The concurrency proof must use separate database connections and real processes. A pair of mocks calling the same helper does not prove the SQLite uniqueness boundary.

## Documentation deliverables

Add:

```text
docs/v1-unit9-pulse-proactive-work.md
```

It begins as `PROPOSED` and must state:

* the exact accepted implementation commit only after post-merge audit;
* the separate-Pulse ruling;
* the source-to-work attribution graph;
* the idempotency boundary;
* how to run the foreground one-pass command;
* how to query attribution without reading JSON;
* the proof matrix and falsifications;
* budget before and after;
* explicit non-claims.

Update:

* `CHANGELOG.md`;
* CLI help, removing "Unit 9, unimplemented" only from the now-real Pulse surface;
* any Store demo prose that still says Pulse does not exist, using additive historical wording where the text describes an earlier unit.

Do not perform Unit 10's editorial completion of Chapters 0–7. If a learner-facing exercise is added, it must import and execute the production Pulse mechanism rather than contain a teaching fork.

## Explicit non-scope

Do not:

* add Pulse behavior to `Supervisor.tick()`;
* change Unit 8's accepted "never fires a wake gate" statements;
* install or configure an OS service;
* add distributed scheduling, network queues, webhooks, cron integration, or external triggers;
* add a general-purpose workflow language;
* create automatic retry policy for failed governed work;
* weaken actor leases, execution fencing, mailbox fencing, workspace confinement, review, or acceptance;
* run or claim credentialed Claude, Codex, or Cursor smokes;
* begin Unit 10 curriculum completion;
* change the runtime dependency surface beyond Pydantic plus stdlib.

The nine credentialed provider tests remain deselected and explicitly deferred to Unit 12.

## Budgets

The accepted Unit 8 baseline is:

```text
26 / 40 modules
5473 / 6000 nonblank source lines
7 / 30 root exports
runtime dependencies: exactly pydantic
```

Those gates remain binding. Unit 9 has only 527 nonblank production lines of headroom. Prefer a small Pulse component, a shared transactional helper, and a Store-specific gate over parallel abstractions.

If the truthful implementation cannot fit, stop and request a budget ruling. Do not compress correctness into opaque code merely to pass the number, and do not silently raise the budget.

## Gate

Run at the exact implementation head:

```bash
uv lock --check
make verify
python scripts/verify_curriculum.py
git diff --check
```

Also build and install the wheel into a clean Python 3.14 environment outside the source tree, then run:

```bash
sovereign-agent --help
sovereign-agent doctor
sovereign-agent pulse --once --root /tmp/sovereign-agent-unit9
```

The full default test suite must pass twice consecutively. Live-provider tests remain deselected and must be reported as unrun.

## Review and merge ritual

1. Stream implements on `unit-9/pulse-proactive-work`; it does not open or merge its own PR.
2. Master independently reads the implementation and reproduces the decisive properties.
3. Master independently mutation-checks at least:

   * removal of the database uniqueness boundary;
   * removal of the no-qualifying-signal guard;
   * replacement of structured origin with inference;
   * insertion of Pulse behavior into `Supervisor.tick()`.
4. Master opens the PR and names its exact head.
5. Sparring reviews that exact head against this SOW and the active ruling.
6. No merge over `CHANGES_REQUESTED`.
7. Principal acceptance is requested explicitly after Sparring co-signs.
8. Merge only through the allowed GitHub PR mechanism.
9. Gate merged `main` from a clean clone.
10. Audit `docs/v1-unit9-pulse-proactive-work.md` against merged behavior.
11. Flip its status to `ACCEPTED` only in a separate, reviewed change.
12. Unit 10 remains unstarted until that closure lands.

If `main` advances, reconcile through an auditable PR-based path and rerun gates and review on the resulting exact head. A prior co-sign does not survive a head change.

## Acceptance conditions

Unit 9 is accepted only when the Principal can inspect the merged ledger and prove:

* the supervisor still never fires a wake gate;
* a real sale produced a real durable signal;
* the genuine Pulse mechanism made one deterministic wake decision;
* one genuine Pulse event exists;
* one canonical Pulse-origin SOW and assignment exist;
* their origin is structured and queryable;
* replay, restart, and concurrency produce no duplicate work;
* no qualifying signal produces no work;
* the Scripted Operator ran through the production path;
* the deterministic Store effect, evidence, review, and acceptance chain remains truthful;
* no live-provider evidence is claimed.

Proceed first by filing and reviewing this SOW. Do not begin implementation before it is merged unchanged or a subsequent Principal ruling amends it.

## Related documents

- [Sovereign Agent 1.0 — executable textbook (design memo)](sovereign-agent-v1-educational-control-plane.md)
- [Ruling: Unit 9 Pulse is a separate mechanism from the supervisor; attribution is structured and durable](../rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md)
- [Unit 8: supervisor, fencing, and hard-kill recovery](../v1-unit8-supervisor-fencing-recovery.md)
- [Units 0-6 contract](../units-0-6-contract.md)
- [Unit 7: workspace lifecycle](../v1-unit7-workspace-lifecycle.md)
