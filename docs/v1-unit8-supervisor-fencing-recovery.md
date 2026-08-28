# Unit 8: supervisor, fencing, and hard-kill recovery

- **status:** PROPOSED, 2026-08-28 (this status is set by the authoring
  stream; the flip to ACCEPTED happens later, by Master/Sparring/Principal
  process, not by this document)
- **authority:** principal (ratifying prior rulings this unit closes);
  status flip to ACCEPTED is a separate later act
- **base:** `main = 5dbcabca640426a4510a9a82c78beff0889696f6` (Units 0-7
  ACCEPTED, clean tree; the exact commit this branch forked from)
- **governing rulings closed by this unit:**
  [`docs/rulings/2026-08-26-deferral-unit4-fencing.md`](rulings/2026-08-26-deferral-unit4-fencing.md)
  (F-U4-1, closed) and
  [`docs/rulings/2026-08-26-one-process-per-actor.md`](rulings/2026-08-26-one-process-per-actor.md)
  (lease fencing, landed) — both updated additively with a closure section;
  neither is rewritten
- **applies_to:** Sovereign Agent 1.x, Unit 8
- **requested_by:** `docs/sows/sovereign-agent-v1-educational-control-plane.md`
  (OQ-3: "teach supervisor as the control loop"), the Unit 7 handover's own
  "Unit 8 is authorized, not started" section, and the deferral rulings this
  unit closes

This document follows `docs/units-0-6-contract.md` and
`docs/v1-unit7-workspace-lifecycle.md`'s own shape: a contract stated as
testable properties, then how to check each one against the repository. It
is **additive** — nothing in the Units 0-7 acceptance record is touched or
revised here.

## The central guarantee, in one sentence

**A worker that no longer holds the current lease may not commit
completion, mutate canonical execution state, acknowledge mailbox work, or
reclaim the active workspace.**

## Process vs. actor — the distinction this unit is built on

An **actor** (`operator-course`, `sparring-course`, …) is a durable identity
declared in `sovereign.toml` — a role, a provider, an authority list. It has
no lifetime of its own; it exists as long as the organization's
configuration says it does. A **process** is one running instance of the
`sovereign-agent` program, or of a supervisor tick, with a lifetime bounded
by the operating system. Before this unit, the mailbox (Unit 4) and
execution (Units 5 and 7) both reasoned only about actors: "is this the
actor that holds the claim," "did this actor's assignment complete." Two
different *processes* claiming to be the same actor — the ordinary shape of
a crashed-and-restarted worker — were indistinguishable to that reasoning.
`docs/rulings/2026-08-26-one-process-per-actor.md` named the gap and
deferred its close to "the supervisor that owns process lifecycle." This
unit is that supervisor, and `fencing.py` is where the process/actor
distinction actually becomes machine-checkable: every lease and every
execution attempt is keyed to a `process_identity` (a fresh random id,
**never a PID** — PIDs are reused by the operating system, so a process
that resumes after losing its lease must not be able to look like a new one
by coincidence of PID reuse) and a monotonically increasing `fencing_token`
that a stale process can never again present successfully once superseded.

## Fencing is not an OS sandbox — read this before trusting anything below

Every guarantee in this document is a **ledger** guarantee, not a
filesystem one. A process that has lost its actor lease or its execution
attempt can still run; if it already started a provider subprocess, that
subprocess is not killed by anything in this unit and may run to
completion, write files, and produce a real receipt in memory. What
fencing guarantees is narrower and different: **those bytes never become
canonical.** The terminal transaction in `organization.run_assignment`
checks the caller's execution-attempt token atomically, in the same SQL
statement that would write COMPLETED/BLOCKED/FAILED to the ledger; if the
token no longer matches, the write is refused and the caller receives a
`Refusal` (category `execution_attempt_lost`) instead of a silently
accepted stale result. The same discipline applies to mailbox completion
(`fencing_token_stale`) and to workspace reclaim, which only runs after the
terminal write's own fence check has already succeeded. This is proven
directly by `tests/test_fencing.py::
test_a_stolen_fence_mid_invocation_refuses_the_terminal_write` — the single
most load-bearing test in this unit's proof matrix, mutation-checked (see
below).

## The contract

### Property 1 — process identity and actor leases

`fencing.new_process_identity()` returns a fresh, random id
(`proc_<uuid4 hex>`), generated once per `Organization` instance —
`Organization.__init__` sets `self.process_identity` at construction, so
every process opening the ledger gets exactly one identity for its
lifetime. `fencing.acquire_actor_lease(db, actor_id, process_identity, ttl,
clock)` is a compare-and-set against a new `actor_leases` table (migration
13): it succeeds when no row exists yet or the existing row's lease has
expired, minting a fresh `fencing_token` from a single shared monotonic
counter (`lease_tokens`) either way. Two racing acquirers each attempt this
inside `db.immediate()` (`BEGIN IMMEDIATE`, the same discipline
`relay.claim()` already used); exactly one wins, because SQLite's reserved
lock serializes them. `renew_actor_lease` extends an already-held lease
**without** reissuing its token — ownership is preserved, not reacquired —
and refuses (fail closed) if the presented token or process identity does
not match the durable row. A takeover after expiry always mints a strictly
greater token, so the original process's remembered token can never again
be renewed, even if that process resumes and tries. Corrupt or incomplete
lease state (an empty or malformed `expires_at`) is not silently treated as
either "always valid" or "always expired" — the same `WHERE expires_at <=
?` comparison SQLite would use for any other row governs it, refusing
acquisition rather than granting blindly on an ambiguous read.

### Property 2 — execution-attempt fencing bound to the RUNNING transition

`organization.run_assignment` calls `fencing.acquire_execution_attempt`
immediately before the `RUNNING` transition it already made — refusing
(fail closed) if the assignment already has a live, unexpired attempt, so
two concurrent invocations of the same `assignment_id` cannot both believe
they may run it. The returned attempt's id is held in a local variable for
the rest of the call. The terminal transaction (`with self.db.transaction()
as connection:`) that used to write `COMPLETED`/`BLOCKED`/`FAILED`
unconditionally now does so through one `UPDATE assignments SET record =
?, current_execution_attempt = NULL WHERE id = ? AND
current_execution_attempt = ?` — a single atomic statement that is both the
write and the fence check. `cursor.rowcount == 1` means this attempt won;
anything else raises `Refusal(category="execution_attempt_lost")` **inside**
the transaction, which rolls back the receipt write too (`db.transaction()`
rolls back on any exception). `reclaim_workspace` is called only after this
transaction succeeds, so a lost fence never reaches it either — the
"only the current fenced owner may reclaim" requirement is enforced
structurally by the `Refusal` propagating out of the method, not by a
second explicit ownership check at the reclaim call site.

### Property 3 — mailbox claims are fenced; F-U4-1 is closed

**The exact defect, as recorded:**
`docs/rulings/2026-08-26-deferral-unit4-fencing.md` named F-U4-1: `claim()`'s
same-owner short-circuit (`if message.state == MessageState.CLAIMED and
message.claim_owner == actor_id: return message`) fired unconditionally,
even when that owner's own lease had already expired — so the CAS's own
expired-lease clause (`WHERE ... state = 'CLAIMED' AND claim_expires_at <=
?`) was reachable only by a **different** actor. The owner reclaiming their
own lapsed lease got the stale, unrenewed `Message` back.

**The fix.** The short-circuit now fires only when the lease is *both*
same-owner *and* unexpired (`message.claim_expires_at > now`) — still
idempotent, so a retried worker inside its own lease window gets the same
fencing token back, not a new one. A same-owner-but-expired claim falls
through into the CAS exactly like a takeover attempt would, and wins it the
same way, minting a fresh `fencing_token` from the same `lease_tokens`
counter `fencing.py` uses. `Message` gains `fencing_token: int | None`.
`complete()` now takes `fencing_token` as a **required** keyword argument
(no default — a caller cannot silently skip presenting it) and verifies it
atomically, in the same `UPDATE ... WHERE claim_owner = ? AND
fencing_token IS ?` statement that performs the write, never re-derived
from the row being written (which would make staleness undetectable by
construction — the row's own current token always "matches itself").
`dead_letter()` verifies the token carried on the `Message` object the
caller passes in, the same way. Both refuse with category
`fencing_token_stale` on a mismatch. The original two-distinct-contenders
CAS property (`tests/test_concurrency.py::
test_only_one_contender_wins_a_contested_lease`) is unweakened and
unchanged — fencing adds a check *on top of* the addressed-recipient gate,
never replaces it.

### Property 4 — hard-kill recovery, by the supervisor, never the dead process

`docs/units-0-6-contract.md`, Unit 5: "A hard kill cannot be caught and
belongs to Unit 8 recovery: a process cannot record its own death."
`supervisor.recover_abandoned_assignments` is that recovery. It queries
`fencing.expired_execution_attempts` — every `ACTIVE` attempt still pointed
at by `assignments.current_execution_attempt` whose `expires_at` has
passed — and, for each one still genuinely `RUNNING` (a real race against
the worker's own late-arriving terminal write is lost gracefully, not
double-recovered), writes a durable `Receipt` with `status="failed"` and
`failure_category="worker_lost"` (one term, used everywhere — never mixed
with a second spelling), naming the expired attempt id and its fencing
token in the failure message. **It never infers success.** However far the
orphaned subprocess might actually have gotten — even if it would have
gone on to write a valid `completed` report eventually — the recovered
receipt is always `failed`; recovery has no way to know what a dead
process's subprocess would have produced, and Unit 5's "nothing is ever a
guessed success" rule extends here rather than exempting the recovery
path. No new `AssignmentState` was introduced: recovery reuses the
existing `FAILED` state, matching the ratified constraint that a hard kill
is not a cancellation.

The terminal write (assignment `FAILED`, SOW `FAILED`, the receipt, the
`assignment.finished` and `assignment.recovered` events) and the fence
release (`fencing.release_execution_attempt`, clearing
`current_execution_attempt` back to `NULL`) happen in **one** SQLite
transaction — which is what makes recovery **idempotent**: a second tick
sees an assignment with no current attempt and nothing left to recover
(`fencing.expired_execution_attempts` stops returning it, by construction,
since its query joins on `current_execution_attempt`). Workspace policy
(`workspace.reclaim_workspace`, unchanged from Unit 7) is applied **only
after** that transaction commits, never before — a crash between the two
leaves a terminal, correct ledger and a workspace a later tick can still
reclaim by policy, never a workspace reclaimed out from under a ledger
that was not yet durable.

### Property 5 — the supervisor's reconciliation boundary

`supervisor.tick(org, clock)` runs, in order: (1) report actor leases past
expiry — read-only, since expiry alone is not a fault, the lease simply
becomes acquirable again lazily; (2) proactively sweep every expired
mailbox claim back to `NEW`, across every recipient, not only the one
lazy per-actor form `relay.inbox()` already had; (3) recover abandoned
`RUNNING` assignments per Property 4. It creates **no** new outcome, SOW,
assignment, or message — proven directly by
`tests/test_supervisor.py::test_tick_never_creates_a_new_outcome_sow_or_
assignment` against a completely empty organization. It never reads a
Pulse signal, never fires a wake gate, never simulates proactive dispatch,
and never installs itself as an OS service.

### Property 6 — the foreground CLI: `supervisor`, distinct from `service` and `pulse`

`sovereign-agent supervisor --root PATH --once` runs a single deterministic
tick and exits 0 — the shape every test in this unit's proof matrix uses,
since it needs no real sleeping. Without `--once`, the same command loops
in the foreground, sleeping `TICK_INTERVAL_SECONDS` (2.0s) between ticks,
until an ordinary interruption — SIGINT (Ctrl-C) or a directly raised
`KeyboardInterrupt` — asks it to stop; caught cleanly (exit 0, no
traceback), not left to crash. **No hidden daemonization**: `supervisor.run`
never forks, never detaches from its controlling terminal, and never
installs itself as an OS service. The CLI's own help text distinguishes
three names on purpose, per
`docs/sows/sovereign-agent-v1-educational-control-plane.md` OQ-3: **`supervisor`**
is the runtime loop, implemented here; **`service`** would be future
operating-system hosting (`install`/`status`/`uninstall`) and is **not**
implemented — no `service` subcommand exists in this unit, on purpose (a
stub that pretends to do something was explicitly rejected in favor of
building nothing rather than something misleading); **`pulse`** is the
future proactive-wake pipeline (sale → signal → wake gate → pulse →
work), explicitly Unit 9's territory and **not** implemented here — no
`pulse` subcommand, no simulated Pulse event, anywhere in this unit's code
or tests.

## Explicit non-scope

- **Pulse, proactive waking, any simulated Pulse event, any wake gate** —
  Unit 9. Nothing in this unit creates work, reads a signal, or fires a
  gate; `supervisor.tick` reconciles only *existing* claimed/running/expired
  work.
- **Inventory-triggered replenishment, cron scheduling** — Unit 9's
  territory or later; not touched.
- **Distributed consensus, multi-host clustering** — out of scope for the
  educational reference entirely. SQLite on one machine is the sole
  authority; there is no remote coordination story here.
- **Remote APIs, sockets, dashboards, webhooks, Slack/email** — none of
  this unit's surface is network-reachable. `supervisor` is a local
  process reading a local SQLite file.
- **OS service installation** — no `service install`/`status`/`uninstall`
  verb exists. No ratified in-tree source requires one for Unit 8; if a
  future reader believes one does, that is a stop condition for the next
  stream to raise, not something this unit silently built.
- **A filesystem sandbox stronger than Unit 7's detection boundary** —
  fencing governs the *ledger*, not the filesystem. Unit 7's
  `workspace.snapshot_boundary`/`diff_boundary` (detection, not
  prevention) is unchanged and untouched by this unit.
- **Automatic retry after ambiguous execution** — recovery produces a
  terminal `FAILED` state and stops. Retrying a recovered assignment
  remains an explicit, governed act through the existing SOW/assignment
  rules (`assign` → `run_assignment` again), never automatic.
- **Credentialed Claude/Codex/Cursor execution** — Unit 12's territory,
  never run here. The `--live` marker's 9 deselected tests are exactly the
  Unit 6/Unit 7 credentialed provider smokes; this unit adds none of its
  own and runs none of the existing ones.
- **Production hardening beyond the educational reference** — this
  remains a teaching artifact, not a production control plane (per the
  educational reset ruling).
- **New runtime dependencies** — Pydantic and the standard library only,
  unchanged; `scripts/verify_runtime_dependencies.py` still reports
  exactly `pydantic`.

**No new book chapter or checkpoint tag.** Confirmed explicitly rather than
silently skipped: no ratified in-tree document assigns a chapter or
checkpoint tag to fencing, the supervisor, or hard-kill recovery. Unit 10's
scope (editorial completion of Chapters 0-7) is untouched by this unit.

## How to check this document against the repository

```bash
# Baseline, still green after Unit 8 lands
python -m pytest -q
python scripts/verify_source_budget.py
python scripts/verify_curriculum.py
python scripts/verify_runtime_dependencies.py

# Property 1 -- process identity and actor leases (CAS exclusivity, renewal,
# takeover after expiry, corrupt-state fail-closed)
python -m pytest -q tests/test_fencing.py -k \
  "process_identity or actor_lease or renewal or takeover or corrupt_lease"

# Property 2 -- execution-attempt fencing, including the decisive
# stolen-fence-mid-invocation property (mutation-checked, see below)
python -m pytest -q tests/test_fencing.py -k \
  "execution_attempt or stolen_fence or completed_assignment_run_via_the_real_path"

# Property 3 -- F-U4-1 closed: same-owner-expired reclaim mints a fresh
# token; complete()/dead_letter() refuse a stale one; distinct-contenders
# exclusivity is unweakened
python -m pytest -q tests/test_fencing.py -k \
  "fu4_1 or complete_with or dead_letter_with or unaddressed_actor"
python -m pytest -q tests/test_concurrency.py -k "contested_lease or two_processes"

# Property 4 -- hard-kill recovery via a REAL child process and a real
# SIGKILL, never a preclassified Refusal injection
python -m pytest -q tests/test_supervisor.py -k \
  "sigkill or recovers_a_real or idempotent or never_guesses_success or workspace_reclaim"

# Property 5 -- reconciliation boundary: reports leases, sweeps claims,
# creates no new work
python -m pytest -q tests/test_supervisor.py -k \
  "expired_actor_leases or sweeps_expired or never_creates"

# Property 6 -- the CLI: --once determinism, and a real SIGINT against a
# real child process running the loop
python -m pytest -q tests/test_supervisor.py -k "once_runs or sigint"
sovereign-agent supervisor --root /tmp/unit8-check --once   # after `sovereign-agent init --root /tmp/unit8-check`

# Credential absence confirmed -- must be empty, same as every prior unit
env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API" || true
```

## Mutation checking (Unit 7's own falsification discipline, applied here)

Every decisive property above was falsified before being reported as done:
the fix was reverted, the specific test that names the property was
confirmed to go red, and the file was restored and confirmed byte-identical
against a pre-mutation copy (`diff`, not merely "tests pass again") before
re-confirming green.

1. **The terminal-transaction fence check** (`organization.py`'s `WHERE ...
   AND current_execution_attempt = ?` clause) — removed; `tests/
   test_fencing.py::test_a_stolen_fence_mid_invocation_refuses_the_
   terminal_write` went red; restored.
2. **F-U4-1's fix** (the same-owner-unexpired-only short-circuit in
   `relay.claim()`) — reverted to the original unconditional short-circuit;
   three tests went red (`test_same_owner_expired_claim_mints_a_fresh_
   token_fu4_1`, `test_complete_with_a_stale_token_is_refused`,
   `test_dead_letter_with_a_stale_message_object_is_refused`); restored.
3. **`fencing.release_execution_attempt`'s fence-clearing UPDATE** —
   removed; `tests/test_fencing.py::test_release_execution_attempt_clears_
   the_fence` went red. (A first mutation attempt targeted a redundant
   defense-in-depth UPDATE elsewhere and correctly found the tests still
   passed — re-targeted to the actual load-bearing statement, an honest
   record of the process rather than a polished retelling.) Restored.
4. **The "never guesses success" recovery receipt** — flipped
   `status="failed"` to `"completed"` in `supervisor.py`; caught one test
   but not a second, which checked only `assignment.state` (already
   hardcoded `FAILED` regardless of receipt status) — a real gap the
   mutation exposed. Fixed by strengthening that test to assert the
   receipt's own `status` field directly; re-mutated to confirm the
   strengthened test now catches it; restored.

## Budget impact

Reproduced by `scripts/verify_source_budget.py`, before and after this
unit's change, both figures read from the script's own printed output.

| | modules | nonblank lines | root exports |
| --- | --- | --- | --- |
| Before (Units 0-7 accepted, `5dbcabca`) | 24/40 | 4307/6000 | 7/30 |
| After (this unit) | 26/40 | 5263/6000 | 7/30 |

Two new modules: `src/sovereign_agent/fencing.py` (process identity, actor
leases, execution-attempt fencing) and `src/sovereign_agent/supervisor.py`
(the reconciliation loop and hard-kill recovery). No new root export —
`fencing` and `supervisor` are called internally by `organization.py` and
`cli.py`; nothing from either module is re-exported from the package root.
Headroom remaining: 14 modules, 737 nonblank lines, 23 root exports.

## What this unit did not do

- **No credentialed provider evidence.** Every hard-kill test uses the
  Scripted provider, patched to run a real (uncredentialed) sleeping
  subprocess. No Claude/Codex/Cursor CLI is invoked anywhere in this
  unit's tests. The 9 deselected `live` tests are unchanged and unrun.
- **No Pulse, no proactive wake, no OS service hosting.** Named explicitly
  above, not merely absent by omission.
- **No `service` subcommand**, stub or otherwise. A stub that pretends to
  install/status/uninstall while doing nothing was considered and rejected
  as more misleading than no command at all.
- **No filesystem-level enforcement of fencing.** A worker that has lost
  its fence can still write bytes to disk if its subprocess is still
  running; this unit only guarantees those bytes never become the ledger's
  canonical record. Documented prominently above, not buried.
- **No automatic retry of a recovered assignment.** Retrying stays an
  explicit, governed act through the existing `assign`/`run` CLI path.
- **`Actor.workspace_policy` is still a bare `str`, not a `StrEnum`** —
  unchanged from Unit 7's own carried-forward note; this unit did not
  touch that type either, since fencing does not depend on it.
- **The actor-lease mechanism (`acquire_actor_lease`/`renew_actor_lease`)
  is built and tested but not yet wired into `run_assignment` or the CLI's
  `run` command as a mandatory precondition to invoking a provider** —
  `run_assignment` acquires and checks an *execution attempt* (Property 2,
  bound to one assignment) unconditionally, which is the mechanism the
  proof matrix's decisive stolen-fence test exercises; the separate
  *actor* lease (Property 1, bound to hosting an actor at all, independent
  of any one assignment) is a complete, CAS-proven primitive that a future
  unit can require at actor-invocation time without further schema work,
  but this unit does not itself gate `run_assignment` on holding one. This
  is a scope boundary, not an oversight: the SOW's central guarantee is
  stated in terms of *execution attempts* and *leases* together, and this
  unit closes the mailbox and execution-attempt halves completely while
  leaving the actor-lease-as-a-hard-precondition wiring for whichever unit
  next needs "an actor may not even be invoked without a live lease" as an
  enforced rule rather than an available one.
