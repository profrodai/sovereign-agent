# Unit 9: Pulse and proactive governed work

- **status:** PROPOSED (this status flips to `ACCEPTED` only in a separate,
  Sparring-reviewed change — not by this stream, and not by this commit)
- **authority:** principal (SOW authorization); acceptance is granted
  separately, after independent review
- **base:** `main = 95ceb8d66b0734a3942d71d3510660c0f4109eb5` (the exact
  commit the Unit 9 SOW was reviewed and merged at; Units 0-8 ACCEPTED)
- **governing SOW:**
  [`docs/sows/sovereign-agent-v1-unit9-pulse-proactive-work.md`](sows/sovereign-agent-v1-unit9-pulse-proactive-work.md)
- **governing ruling:**
  [`docs/rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md`](rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md)
- **applies_to:** Sovereign Agent 1.x, Unit 9
- **review history:** PR #35, first head `690e8ddd`. Sparring's independent
  review found F-U9-1: `Organization.create_pulse_work` was five separate
  SQLite commits, not the one atomic transaction the governing SOW
  explicitly requires — an ordinary exception between any two of them left
  a wake decision durably stranded, with `source_signal_id`'s own `UNIQUE`
  constraint then permanently refusing every retry. The Principal
  independently reproduced the defect before routing it back. Corrected at
  this head by composing the wake decision, the SOW's creation and
  transitions, the assignment, the event, and the origin row into one
  `db.immediate()` transaction, plus in-transaction revalidation — see
  Property 3 below for the full account, and the mutation-checking section
  for the falsification. The correction also raised the source-line budget
  from 6000 to 6250 (module and export ceilings unchanged) — see Budget
  impact below.

This document follows `docs/v1-unit8-supervisor-fencing-recovery.md` and
`docs/v1-unit7-workspace-lifecycle.md`'s own shape: a contract stated as
testable properties, then how to check each one against the repository. It
is **additive** — nothing in the Units 0-8 acceptance record is touched or
revised here.

## The separate-Pulse ruling, and why this document exists to prove it held

`docs/rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md` decided
two open questions ahead of this unit's implementation:

1. **Pulse is a separate mechanism.** `Supervisor.tick()` is not extended
   with a fourth step. Pulse lives under the reserved `pulse` CLI surface,
   as its own component, calling `Organization.run_assignment()` the same
   way every other caller does — never disguised as supervisor
   reconciliation.
2. **Pulse origin is structured and durable.** "Created without a human
   prompt" must be provable in the ledger after the fact — a column read,
   never an inference from the absence of a CLI invocation or the absence
   of a manual-origin row.

This unit's whole job is proving both holdings true in code, not merely in
prose. The mutation-checking section below is where that proof is made
falsifiable rather than asserted.

## The pipeline this unit closes

```text
sale
→ durable inventory signal (append-only, per occurrence — fixed this unit)
→ deterministic wake gate (Store-specific, outside sovereign_agent's budget)
→ genuine durable pulse.work_created event
→ governed replenishment work created without a human prompt
→ Scripted Operator, through the existing production run_assignment path
→ deterministic effect boundary (apply_restock, unchanged)
→ evidence, independent review, acceptance (unchanged)
```

Every stage after "deterministic wake gate" reuses production code that
existed before this unit. Unit 9 built exactly four new things: signal
stability, the canonical creation transaction, the Pulse component itself,
and the Store's own wake gate.

## The contract

### Property 1 — Pulse is a distinct mechanism; `supervisor.tick()` is unchanged

`src/sovereign_agent/pulse.py` never imports `sovereign_agent.supervisor`,
proven both statically (an AST walk over its own imports) and behaviourally:
running `supervisor.tick()` against an organization carrying a genuinely
qualifying, uncommitted sale creates no SOW, no assignment, and no
`pulse.*` event. `Supervisor.tick()`'s own four steps (Unit 8, unchanged)
still run in the same order, and its accepted claim — "never reads a Pulse
signal, never fires a wake gate" — remains literally true, unedited, in both
`supervisor.py`'s own docstring and
`docs/v1-unit8-supervisor-fencing-recovery.md`.

### Property 2 — Signal stability: a committed sale signal is never replaced

Before this unit, `record_sale`'s own signal insert was `INSERT OR REPLACE`,
keyed implicitly on `dedupe_key`'s `UNIQUE` constraint (migration 1).
`dedupe_key` was exactly `f"inventory:{sku}:{on_hand}"` — no per-occurrence
component — so a second, later sale that happened to leave inventory at the
same `on_hand` level silently deleted the first sale's own signal row and
replaced it with a new one carrying a different id. A Pulse origin
referencing a source signal by durable id cannot safely point at a row that
can later disappear under an unrelated, later sale.

Fixed in `src/reference_organizations/store/__init__.py`: `dedupe_key` is
now suffixed with the signal's own id, and the write is a plain `INSERT`,
not `INSERT OR REPLACE` — signals are now append-only, exactly like every
other proof-bearing table in this database. `record_sale`'s existing
atomicity is untouched: the signal insert is still inside the same
`db.immediate()` transaction as the inventory `UPDATE`, the cash `INSERT`,
and the `sale.committed` event.

### Property 3 — The canonical creation transaction

`Organization.create_pulse_work` (`src/sovereign_agent/organization.py`) is
the single production path from a fired wake decision to durable, governed
work. It composes, inside **one** `db.immediate()` transaction:

1. Revalidation, when the caller supplies one, run INSIDE the open
   transaction, immediately before anything is written — the qualifying
   condition could have changed between the caller's own read and this
   transaction actually acquiring its write lock.
2. An `INSERT` into `pulse_wake_decisions`, whose `UNIQUE(source_signal_id)`
   constraint (migration 15) **is** the "one canonical wake decision per
   source signal" enforcement — at the SQLite boundary, not a preflight
   `SELECT`. Two concurrent callers racing the same signal both attempt this
   insert on the same connection-level lock; `db.immediate()`'s own
   `BEGIN IMMEDIATE` means one blocks until the other's ENTIRE transaction
   — not just this one insert — has committed or rolled back.
3. The SOW's creation and its `READY`/`ASSIGNED` transitions, and the
   assignment's creation.
4. A genuine `pulse.work_created` event.
5. One `pulse_origins` row tying the wake decision, the event, the SOW, and
   the assignment together.

**F-U9-1, corrected.** The original implementation split this across FIVE
separate commits: the `pulse_wake_decisions` insert in its own
`db.immediate()`, then `create_sow`'s, `ready_sow`'s, and `assign`'s own
individually-transactional calls in sequence, then a final `db.transaction()`
for the origin row — despite this same section, at the time, claiming "the
INSERT above committed synchronously as its own transaction" as though that
were a safe, deliberate design rather than the defect it was. Sparring found,
and the Principal independently reproduced (PR #35), that an ordinary
exception between any two of those five commits — no crash required, any
`Refusal` or bug anywhere in the sequence — left the wake decision durably
stranded: `pulse_wake_decisions` had a row, `pulse_origins`/`sows`/
`assignments` had none. Because `source_signal_id` is `UNIQUE`, no retry
could ever re-claim that signal afterward — `_wait_for_pulse_origin` found
no origin row to resolve to and raised `wake_decision_contended` instead of
recovering. The signal was orphaned permanently, with no automatic or manual
recovery short of direct database surgery. (This was never the SOW's own
named "crash after canonical creation but before provider invocation" case —
`pulse.py`'s `_resumable_signals` already handled that one correctly; F-U9-1
was a narrower, unnamed window strictly inside canonical creation itself.)

Fixed by extracting `_create_sow_on`/`_ready_sow_on`/`_assign_on` — the same
writes `create_sow`/`ready_sow`/`assign` perform, taking an already-open
connection instead of opening their own — and composing all five steps above
on one connection, inside one `db.immediate()`. `create_sow`, `ready_sow`,
and `assign` themselves are unchanged as public, single-call entry points:
each is now a thin wrapper that opens its own transaction, delegates to its
`_on` helper, commits, and projects — manual dispatch calls the exact same
production methods it always did, and nothing here forks a Pulse-only path.
Projection happens only after `create_pulse_work`'s transaction commits,
never folded into it, matching every other write path in this class.

A concurrent loser — genuinely arriving after the winner's full transaction
has committed, not merely after its first statement — polls briefly
(bounded, local SQLite reads only) for the winner's own `pulse_origins` row
to land, then returns the **same** SOW and assignment identifiers, never a
second, competing pair. This concurrency behavior is unchanged in substance
from before the fix and re-verified as its own named property under the new
atomic design (see the proof matrix below) — `db.immediate()`'s reserved
lock, taken up front, is what always made two callers unable to interleave
their writes for one signal; composing more work inside that same lock does
not weaken it.

`create_sow` itself was changed to insert an explicit origin row — `manual`
by default — for **every** SOW at creation time, deferred to the Pulse
transaction's own `pulse` row only when called from
`create_pulse_work` (via a private `_pulse_origin_pending` flag). This is
what makes Property 5 below true: absence of a row is never the definition
of manual, because no SOW is ever created without one.

### Property 4 — The Pulse component and the Store's own wake gate

`sovereign_agent.pulse.run_pulse_once` is one deterministic pass:

1. Resume every already-fired signal whose canonical assignment is still
   `CREATED` — the crash-window case: canonical creation committed, but no
   process ever reached `run_assignment` for it.
2. Read every signal with no wake decision yet, oldest first.
3. Ask the caller-supplied `WakeGate` callback whether each one fires.
4. For each that fires, call `create_pulse_work`, then invoke
   `Organization.run_assignment()` for a `CREATED` assignment through the
   exact same path the `run` CLI command and the supervisor's own recovery
   path use — never bypassing Unit 8's actor-lease or execution-attempt
   fencing. A `RUNNING` assignment is reported, not re-invoked; `COMPLETED`,
   `BLOCKED`, and `FAILED` are terminal and never rerun or replaced.
5. Return a structured `PulseReport` naming what was created, replayed,
   skipped, refused, or already running.

The wake gate itself is intentionally **not** in `sovereign_agent.pulse`:
`store_wake_gate` (`src/reference_organizations/store/pulse_gate.py`) lives
outside `sovereign_agent`'s own module budget, exactly as the governing SOW
asks ("a Store-specific gate over parallel abstractions"). It fails closed
on every ambiguity the SOW names: a non-sale-origin or non-`inventory.changed`
signal, a subject no longer below reorder (re-checked live, never trusted
from the signal's own stale `severity`), and zero or more than one matching
`ACTIVE` outcome.

### Property 5 — Pulse attribution is a column, never an inference

`src/sovereign_agent/models.py`'s `PulseOrigin` and
`Organization.pulse_origin_for_sow` expose, for any SOW: `origin_kind`
(`"manual"` or `"pulse"`), `sow_id`, `assignment_id`, `wake_decision_id`,
`pulse_event_id`. Every SOW — created before this unit (backfilled by
migration 15) or after (via `create_sow`'s own insert) — has exactly one
`pulse_origins` row, enforced by `UNIQUE(sow_id)`. "No Pulse-origin row
exists" is not a state this schema can represent: it never happens.

## Persistence and migration

Migration 15 (`src/sovereign_agent/database.py`) adds two tables, both
append-only (the same three guards migration 12's pattern established,
applied here and folded into `APPEND_ONLY_TABLES`):

| Table | Enforces |
| --- | --- |
| `pulse_wake_decisions` | `UNIQUE(source_signal_id)` — one canonical decision per signal; `FOREIGN KEY` to `signals(id)` |
| `pulse_origins` | `UNIQUE(sow_id)`, `UNIQUE(assignment_id)`, `UNIQUE(wake_decision_id)`, `UNIQUE(pulse_event_id)`; `FOREIGN KEY`s to `sows`, `assignments`, `pulse_wake_decisions`; a `CHECK` constraint tying `origin_kind` to which of `wake_decision_id`/`pulse_event_id` may be non-null |

Every SOW that existed before migration 15 is backfilled an explicit
`'manual'` origin row at migration time, keyed off the SOW's own
`created_at`. A SOW with zero or more than one assignment gets `NULL`
`assignment_id` rather than a guessed binding — `origin_kind` stays
`'manual'` regardless. Malformed pre-existing SOW data (unparseable JSON)
rolls the whole migration back, unstamped, per this project's forward-only,
fail-closed discipline — proven directly by
`test_migration_15_rolls_back_on_malformed_unattributable_sow_data`.

## How to run the foreground one-pass command

```bash
sovereign-agent init --root /tmp/pulse-check
# ... seed a Store, activate an outcome, commit a sale that crosses reorder ...
sovereign-agent pulse --once --root /tmp/pulse-check
```

`--once` is required; no other shape exists. The command prints one line per
signal evaluated (its status: `created`, `replayed`, `skipped`, `refused`,
or `already_running`) and a one-line summary.

## How to query attribution without reading JSON

```bash
sqlite3 /tmp/pulse-check/.sovereign/organization.db <<'SQL'
SELECT po.origin_kind, po.sow_id, po.assignment_id,
       wd.source_signal_id, wd.source_event_id
FROM pulse_origins po
LEFT JOIN pulse_wake_decisions wd ON wd.id = po.wake_decision_id
ORDER BY po.created_at;
SQL
```

Or, from Python, `Organization.pulse_origin_for_sow(sow_id)` returns a
typed `PulseOrigin`.

## Required proof matrix — how to check this document against the repository

```bash
# Baseline, still green after Unit 9 lands
python -m pytest -q
python scripts/verify_source_budget.py
python scripts/verify_curriculum.py
python scripts/verify_runtime_dependencies.py

# Property 1 -- separate mechanism: pulse --once works; supervisor.tick()
# still creates no work and emits no Pulse event even with a qualifying
# sale already committed; pulse.py never imports supervisor, statically
python -m pytest -q tests/test_pulse.py -k \
  "test_pulse_once_works or test_supervisor_tick_still_creates_no_work_and_emits_no_pulse_event or test_pulse_never_imports_supervisor"

# No creation from nothing: empty organization, seeded with no sale, and a
# sale that stays above reorder all create no work
python -m pytest -q tests/test_pulse.py -k "creates_no_work"

# Qualification and current-state check: a real crossing sale creates
# canonical work; a formerly-qualifying signal does not fire once resolved
python -m pytest -q tests/test_pulse.py -k \
  "crossing_the_threshold or does_not_fire_after"

# Attribution: the full source event -> signal -> decision -> pulse event ->
# SOW -> assignment walk, and manual attribution (fresh and migrated)
python -m pytest -q tests/test_pulse.py -k "attribution or manual"

# Replay and restart: same-process replay and a reopened database both
# return the same identifiers, counts stay at one
python -m pytest -q tests/test_pulse.py -k "replay or reopening"

# Concurrency and crash window: a REAL two-connection threading.Barrier race
# for the same signal creates exactly one canonical SOW; a CREATED
# assignment left by a simulated crash resumes without duplication
python -m pytest -q tests/test_pulse.py -k \
  "two_real_processes or survives_restart"

# Existing RUNNING work and terminal work: Pulse never bypasses Unit 8
# fencing; COMPLETED/BLOCKED/FAILED canonical assignments are never rerun
python -m pytest -q tests/test_pulse.py -k \
  "does_not_bypass or is_not_rerun"

# Source integrity and ledger integrity: missing source event, fabricated
# signal id, no/ambiguous matching outcome, FK/uniqueness/append-only
python -m pytest -q tests/test_pulse.py -k \
  "fails_closed or refused_by_the_foreign_key or cannot_name_the_same_sow or append_only"

# Recurrence: THE decisive signal-stability property -- a later genuine sale
# reaching a previously-seen inventory level retains the earlier signal and
# creates distinct new work of its own
python -m pytest -q tests/test_pulse.py -k "recurrence or retains_the_old_signal"

# Real mechanism, full teaching slice, CLI artifact
python -m pytest -q tests/test_pulse.py -k \
  "real_signal_object or full_teaching_slice or cli"

# Migration 15: fresh install, populated upgrade, manual backfill (including
# the null-assignment case), rollback on malformed data, rollback on a
# simulated SQL failure, FK/uniqueness/append-only, idempotent re-open
python -m pytest -q tests/test_persistence.py -k "migration_15"

# F-U9-1: the canonical creation transaction is genuinely atomic. A fault at
# EVERY remaining write boundary (SOW creation, the READY transition,
# assignment creation, the pulse.work_created event) rolls back the ENTIRE
# chain, not just the wake decision; a signal orphaned by such a fault
# remains eligible and a retry creates exactly one canonical chain, driven
# both directly and through the real run_pulse_once entry point; two real
# processes still converge on one canonical creation and the loser still
# reads the winner's committed identifiers, both re-verified under the new
# atomic design; in-transaction revalidation prevents stale work; and the
# provider is never invoked against an incomplete origin chain
python -m pytest -q tests/test_pulse.py -k   "fault_at_every or remains_eligible_after or recovers_a_signal_orphaned or converge_on_one_canonical_creation_under_the_atomic or losing_contender_reads_the_winners or revalidation_inside or provider_invocation_never_sees"

# Credential absence confirmed -- must be empty, same as every prior unit
env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API" || true

# CLI artifact, from a built wheel outside the source tree
python -m build --wheel -o /tmp/sovereign-agent-unit9-dist
python -m venv /tmp/sovereign-agent-unit9-venv
/tmp/sovereign-agent-unit9-venv/bin/pip install \
  /tmp/sovereign-agent-unit9-dist/sovereign_agent-*.whl
/tmp/sovereign-agent-unit9-venv/bin/sovereign-agent --help
/tmp/sovereign-agent-unit9-venv/bin/sovereign-agent doctor
/tmp/sovereign-agent-unit9-venv/bin/sovereign-agent pulse --once \
  --root /tmp/sovereign-agent-unit9
```

## Mutation checking

Every decisive property above was falsified before being reported as done:
the fix was reverted, the specific test that names the property was
confirmed to go red, the mutated file was confirmed byte-identical to its
pristine state (`diff`) before restoring, and green was re-confirmed.

1. **The database uniqueness boundary** (`UNIQUE(source_signal_id)` on
   `pulse_wake_decisions`, migration 15) — removed;
   `tests/test_pulse.py::test_two_real_processes_evaluating_the_same_signal_create_one_canonical_sow`
   and `test_create_pulse_work_called_twice_for_the_same_signal_returns_the_same_identifiers`
   both went red (a second, competing SOW was created). Restored.
2. **The no-qualifying-signal guard** (`store_wake_gate`'s live
   `below_reorder` re-check) — removed;
   `test_a_formerly_qualifying_signal_does_not_fire_after_the_condition_resolves`
   and `test_sale_remaining_above_reorder_creates_no_work` both went red
   (work was created for a signal whose condition had already resolved).
   Restored.
3. **Structured origin, replaced with inference** (`create_sow`'s own
   explicit `'manual'` origin insert) — removed;
   `test_manually_created_work_says_manual_explicitly` went red
   (`pulse_origin_for_sow` returned `None` for a freshly created manual
   SOW — the exact "absence of a row means manual" shape the governing
   ruling forbids). Restored.
4. **Pulse behaviour inserted into `Supervisor.tick()`** — a call to
   `run_pulse_once` was added inside `tick()`. Unit 8's own existing test
   (`test_tick_never_creates_a_new_outcome_sow_or_assignment`) stayed
   green, because it runs against a completely empty organization with no
   qualifying signal for Pulse to act on — a real gap the mutation exposed
   rather than a false negative. This unit's own
   `test_supervisor_tick_still_creates_no_work_and_emits_no_pulse_event`
   (which runs `tick()` against an organization carrying a genuinely
   qualifying, already-committed sale) went red under the same mutation.
   Restored.

A fifth round followed Sparring's own independent finding on PR #35,
F-U9-1, confirmed by the Principal's own direct reproduction before routing
to this stream:

5. **The atomic transaction, re-split into two** — `create_pulse_work`'s
   single `db.immediate()` block was deliberately re-divided into the
   wake-decision `INSERT`'s own separately-committing transaction followed
   by a second transaction for the SOW/assignment/event/origin writes,
   reproducing F-U9-1's original defect shape exactly.
   `test_a_fault_at_every_creation_boundary_rolls_back_the_entire_chain`
   (parametrized across all four remaining write boundaries),
   `test_the_signal_remains_eligible_after_a_full_rollback_and_a_retry_creates_exactly_one_chain`,
   and `test_run_pulse_once_recovers_a_signal_orphaned_by_a_mid_transaction_fault`
   all went red — each reproducing the exact stranded shape the original
   report named (`pulse_wake_decisions: 1`, every other table `0`).
   Restored, confirmed byte-identical via `diff` before re-confirming green.

## Budget impact

Reproduced by `scripts/verify_source_budget.py`, before and after this
unit's change, both figures read from the script's own printed output.

| | modules | nonblank lines | root exports |
| --- | --- | --- | --- |
| Before (Unit 8 accepted, `95ceb8d6`) | 26/40 | 5473/6000 | 7/30 |
| After (initial implementation, PR #35 first head) | 27/40 | 5991/6000 | 7/30 |
| After (F-U9-1 correction; ceiling raised to 6250) | 27/40 | 6139/6250 | 7/30 |

One new module in the budgeted package: `src/sovereign_agent/pulse.py`. No
new root export — `pulse` is called internally by `cli.py`; nothing from it
is re-exported from the package root. `src/reference_organizations/store/`
(the Store's own wake gate and the Pulse reference demo) is **not** counted
by this budget, per the script's own scope
(`PACKAGE = ROOT / "src" / "sovereign_agent"`), matching the governing SOW's
own preference for a Store-specific gate living outside the budgeted
package rather than a parallel abstraction inside it.

**The ceiling itself changed.** Principal ruling on PR #35 (F-U9-1, see
Property 3 above): the initial implementation's canonical creation
transaction was five separate SQLite commits, not one atomic transaction,
despite the governing SOW's explicit requirement — a defect that could
durably strand a wake decision with no recovery path. Closing it honestly
required composing `create_sow`/`ready_sow`/`assign`'s own writes into
connection-taking `_on` helpers `create_pulse_work` could share inside one
`db.immediate()` block, plus the in-transaction revalidation the same
ruling required. That composition did not fit the original 6000-line
ceiling without cramping the code to force it, so the Principal raised
`scripts/verify_source_budget.py`'s own `MAX_NONBLANK_LINES` from 6000 to
6250 — module (40) and root-export (30) ceilings are unchanged — recorded
in that script's own comment above the constant, not only here.

Headroom remaining: 13 modules, 111 nonblank lines, 23 root exports. Both
the original 9-line margin and this correction's own margin were watched
continuously during implementation, not discovered at the end — no code was
compressed to fit either ceiling.

## What this unit did not do

- **No OS service, no scheduling, no cron, no webhooks.** `pulse --once` is
  the only shape; there is no looping mode, unlike `supervisor` (which has
  both `--once` and a foreground loop). A future foreground runtime that
  wants to run both `supervisor` and `pulse` on an interval composes them
  as two distinct external invocations; nothing in this unit builds that
  composition.
- **No automatic retry policy.** A `BLOCKED` or `FAILED` canonical
  assignment is reported as terminal and left alone. Recovery or
  reassignment continues through the existing governed
  `assign`/`run_assignment` path, exactly as Unit 8 already established for
  supervisor-recovered work.
- **No weakening of any existing fencing, confinement, review, or
  acceptance boundary.** `create_pulse_work` reuses `create_sow`,
  `ready_sow`, and `assign` unchanged; `run_pulse_once` invokes
  `run_assignment` unchanged. Unit 8's actor-lease and execution-attempt
  fencing apply to a Pulse-created assignment exactly as they apply to a
  manually created one — proven directly by
  `test_pulse_does_not_bypass_actor_leases_or_execution_attempt_fencing`.
- **No credentialed provider evidence.** Every test in this unit's proof
  matrix uses the Scripted provider. The 9 deselected `live`-marked tests
  are unchanged, unrun, and remain deferred to Unit 12.
- **No Unit 10 curriculum work.** Chapters 0-3 are updated only with
  additive historical notes (see below); no new chapter, no new exercise,
  no editorial pass over existing chapter prose beyond naming that Pulse
  now exists as a separate, real command.
- **No change to the runtime dependency surface.** Still exactly `pydantic`
  plus the standard library — `scripts/verify_runtime_dependencies.py`
  reports `pydantic` before and after.
- **`sovereign-agent demo`'s own CLI surface was not extended** with a
  `--mode pulse` flag. The reference Store Pulse scenario
  (`run_pulse_simulated`, `src/reference_organizations/store/demo.py`) is
  reachable directly (as this unit's own tests do) and proven by
  `test_full_teaching_slice_reaches_verified_reviewed_truthful_acceptance`,
  but is not wired to a new CLI flag — not required by the governing SOW's
  "add an offline reference scenario," and budget headroom did not permit
  it without risk of overshooting the 6000-line ceiling.

## Related documents

- [SOW: Sovereign Agent 1.x — Unit 9 Pulse and proactive governed work](sows/sovereign-agent-v1-unit9-pulse-proactive-work.md)
- [Ruling: Unit 9 Pulse is a separate mechanism from the supervisor; attribution is structured and durable](rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md)
- [Unit 8: supervisor, fencing, and hard-kill recovery](v1-unit8-supervisor-fencing-recovery.md)
- [Unit 7: workspace lifecycle](v1-unit7-workspace-lifecycle.md)
- [Units 0-6 contract](units-0-6-contract.md)
