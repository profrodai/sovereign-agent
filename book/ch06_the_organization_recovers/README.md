# Chapter 6 — The organization recovers

## Learning objective

Understand why "a process cannot record its own death" (Unit 5's own rule)
forces a *second* process to own recovery, and see the supervisor do exactly
that: recover a genuinely, violently killed worker's assignment — never
guessing that it might have succeeded.

Chapter 5 fenced who may hold authority right now. This chapter is about what
happens when the process holding it simply stops existing.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Supervisor tick** | One deterministic reconciliation pass: report expired actor leases, sweep expired mailbox claims, recover abandoned running assignments. Creates no new work. |
| **Hard-kill recovery** | The supervisor writing a durable `FAILED` receipt for an assignment whose execution attempt expired with no worker left to finish it — `failure_category="worker_lost"`. |
| **Worker lost** | The one failure category this recovery path ever writes. Never inferred success, however far the dead subprocess might actually have gotten. |

## A note on realism, before you run this

This exercise does not simulate a crash with a caught exception. It starts a
**real** child process, waits until that process has genuinely acquired its
execution attempt and moved the assignment to `RUNNING`, then sends it a
**real** `SIGKILL` — the one signal a Python program cannot catch or clean up
after. No receipt gets written by the dying process, because a `SIGKILL`
gives it no chance to run any code at all. This is the same fixture and
polling discipline `tests/test_supervisor.py`'s own hard-kill proof matrix
uses, not a weaker teaching stand-in: the failure mode a supervisor has to
recover from is a real one, and a caught, pre-classified exception would
prove something narrower than what actually happens when a worker's process
disappears.

## The exercise

```bash
python book/ch06_the_organization_recovers/solution.py --root /tmp/andrea-ch06
```

Takes a few seconds — it genuinely waits for a real subprocess to reach
`RUNNING`, kills it, and runs two real supervisor ticks.

## Expected observations

```json
{
  "worker_reached_running_before_sigkill": true,
  "worker_died_abnormally": true,
  "before_recovery": {
    "assignment_state": "RUNNING",
    "execution_attempt_still_referenced": true
  },
  "first_tick": {
    "recovered_count": 1
  },
  "second_tick_is_idempotent": {
    "recovered_count": 0
  },
  "after_recovery": {
    "assignment_state": "FAILED",
    "receipt_status": "failed",
    "receipt_failure_category": "worker_lost"
  }
}
```

Four things worth reading closely:

1. **The ledger tells the truth about the moment of death.** Immediately
   after the kill, the assignment still reads `RUNNING`, with its execution
   attempt still referenced — the dead process never got to write anything,
   so the ledger honestly reflects "still going" until something else says
   otherwise.
2. **The supervisor decides, not the dead process.** `first_tick` recovers
   exactly one assignment — using a far-future clock in place of waiting out
   the real execution-attempt TTL (15 minutes), so this exercise finishes in
   seconds without weakening what the recovery logic itself does.
3. **Recovery is idempotent.** The second tick recovers nothing more — the
   fence was cleared inside the same transaction as the terminal write, so
   there is nothing left for a later tick to find.
4. **The recovered receipt is always `failed`, never a guess.** However far
   the killed subprocess might actually have gotten — it might have been
   about to write a valid `report.json` — the organization has no way to know
   that, and Unit 5's own rule ("nothing is ever a guessed success") extends
   here without exception.

## Why this is not a cancellation

No new `AssignmentState` was introduced for this. Recovery reuses the
existing `FAILED` state — a hard kill is not treated as though someone
decided to stop the work; it is treated as though the work's outcome is
simply unknown, and unknown is not success. Retrying is a fresh, explicit,
governed act (`assign` → `run_assignment` again), never automatic.

## Learner verification command

```bash
python -m pytest tests/test_supervisor.py -k \
  "sigkilled or recovers_a_real or idempotent or never_guesses_success or workspace_reclaim"
```

Expected: all pass. Together they prove a real hard-kill leaves the ledger
honest, the supervisor (not the dead process) recovers it, recovery is
idempotent, the receipt is always `failed`, and workspace reclaim happens
only after the recovery transaction is durable.

## Explain it back

1. Why does `SIGKILL` specifically matter here — what would change if this
   chapter used a caught exception instead?
2. The assignment still read `RUNNING` immediately after the kill. Why is
   that the *correct* thing for the ledger to say at that moment, rather
   than a bug?
3. "Nothing is ever a guessed success" — what is the dangerous alternative
   this rule forbids, concretely, for a killed worker that might have been
   one line away from finishing correctly?
4. Recovery clears the fence in the *same* transaction as the terminal
   write. What would go wrong on a second tick if those were two separate
   transactions instead?
5. No new `AssignmentState` was added for a recovered assignment — it reuses
   `FAILED`. What would a dedicated `RECOVERED` state let a reader assume
   that they should not be allowed to assume?

## Where to look next

- `src/sovereign_agent/supervisor.py` — `tick`, `recover_abandoned_assignments`
- `tests/fixtures/hard_kill_worker.py` — the real child process this
  exercise's own `solution.py` reuses
- `docs/v1-unit8-supervisor-fencing-recovery.md` — the full contract,
  Property 4 in particular

`solution.py` imports the production package rather than copying it.

Next: [Chapter 7 — The organization wakes itself](../ch07_the_organization_wakes_itself/README.md)
