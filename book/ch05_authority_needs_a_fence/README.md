# Chapter 5 — Authority needs a fence

Two of Lucy's staff each believe they are closing tonight. One of them is wrong —
maybe they swapped shifts and forgot, maybe one went home and came back. It does
not matter *why*. What matters is that only one person can count the till, lock
the freezer, and set the alarm, and the shop must never let *both* do it, because
two people each doing "the closing" is how money goes missing and doors get left
open.

Software has exactly this problem, and it is sneakier there. A worker process
crashes and gets restarted; for a moment, *two* processes both believe they are
the same actor, `operator-course`, finishing the same job. If both are allowed to
write "done," the ledger ends up with two conflicting truths. This chapter builds
the fence that makes that impossible — not by trusting workers to behave, but with
a numbered claim (think of it as a numbered key) that only one process can hold at
a time, where every handover mints a *higher* number so a stale worker's old key
simply stops turning.

## Learning objective

Understand the difference between an **actor** (a durable, governed identity)
and a **process** (one running instance of the program), and why the ledger
needs to fence at both levels: two different *processes* claiming to be the
same actor is the ordinary shape of a crashed-and-restarted worker, and
nothing before this chapter's mechanism could tell them apart.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Process identity** | A fresh, random id (`proc_<uuid4>`) minted once per running `Organization` instance — **never a PID**, because PIDs are reused by the operating system. |
| **Actor lease** | A compare-and-set claim that one process identity may host one actor right now. Exclusive, renewable, expires. |
| **Fencing token** | A number drawn from one shared, strictly increasing counter. A takeover always mints a token higher than any the previous holder ever saw, so a resumed stale process can never present a token that still compares as current. |
| **Execution attempt** | A compare-and-set claim that one process may write ONE assignment's terminal state (`COMPLETED`/`BLOCKED`/`FAILED`) — bound to, and re-verified against, the actor lease that was live when it was acquired. |

## The central guarantee, in one sentence

**A worker that no longer holds the current lease may not commit completion,
mutate canonical execution state, acknowledge mailbox work, or reclaim the
active workspace.**

## The exercise

```bash
python book/ch05_authority_needs_a_fence/solution.py --root /tmp/lucy-ch05
```

Exercises `fencing.acquire_actor_lease` and `fencing.acquire_execution_attempt`
directly, then proves the decisive property end to end: two genuinely
separate `Organization` instances — standing in for two separate operating
system processes — contend for the *same actor* through the real,
unmodified `run_assignment` path every other caller uses.

## Expected observations

```json
{
  "actor_lease_cas": {
    "process_a_acquired": "token=1",
    "process_b_while_a_holds_it": "refused: actor_lease_held",
    "process_a_released": "True",
    "process_b_now_acquires_cleanly": "token=2"
  },
  "execution_attempt_fencing": {
    "acquired": "attempt_id=att_...",
    "second_attempt_same_assignment": "refused: execution_attempt_held",
    "stale_lease_token": "refused: actor_lease_lost"
  },
  "second_process_same_actor_different_assignment": {
    "outcome": "refused",
    "category": "actor_lease_held"
  },
  "assignment_never_reached_running": "CREATED",
  "same_actor_next_assignment_after_release": "COMPLETED"
}
```

Read this in order:

1. **The actor lease is a compare-and-set, not a courtesy.** Process B is
   refused outright — `actor_lease_held` — while process A's lease is live,
   with no window where both believe they hold it. Once A releases, B
   acquires cleanly, minting a fresh, strictly higher token (`2`, not `1`
   reused).
2. **An execution attempt requires a *current* actor lease, re-verified
   inside its own transaction.** Presenting a stale token (`-1`, standing in
   for one that no longer matches any real row) is refused — the check is
   never merely "trust the caller's earlier acquisition."
3. **The decisive property: two DIFFERENT assignments for the SAME actor,
   two SEPARATE processes.** This is the gap an ordinary message queue leaves
   open: it can prove two distinct *actors* contending for one message produce
   one winner, but says nothing about two *processes* both claiming to be the
   same actor. `second_process_same_actor_different_
   assignment` shows the refusal happening through the ordinary
   `run_assignment` call, before the provider is ever invoked —
   `assignment_never_reached_running` confirms the second assignment stayed
   `CREATED`, not merely that its result was discarded afterward.
4. **Once the lease is free, the same actor's next assignment runs
   cleanly** under a fresh process — the fence is about exclusivity at a
   moment in time, not a permanent lockout.

## Fencing is not an OS sandbox

Every guarantee here is a **ledger** guarantee, not a filesystem one. A
process that has lost its lease can still be running; if it already started
a provider subprocess, nothing in this chapter kills it, and it may run to
completion and write files. What fencing guarantees is narrower: **those
bytes never become canonical.** The terminal transaction that would write
`COMPLETED`/`BLOCKED`/`FAILED` checks the caller's execution-attempt token
atomically, in the same SQL statement that performs the write — a stale
token means the write is refused, not silently accepted.

## Learner verification command

```bash
python -m pytest tests/test_fencing.py -k \
  "acquire_actor_lease_succeeds_with_no_prior_lease or acquire_execution_attempt_succeeds_for_a_fresh_assignment or acquire_execution_attempt_refuses_without_a_live_actor_lease or actor_lease_blocks_a_second_assignment_for_the_same_actor_before_invocation or the_ordinary_run_assignment_path_cannot_bypass_the_actor_lease"
```

Expected: all pass. Together they prove the actor-lease CAS, the
execution-attempt fencing bound to it, and that the ordinary CLI path
cannot bypass either.

## Explain it back

1. Why is a fencing token drawn from one shared, strictly increasing
   counter, rather than each lease type keeping its own?
2. `new_process_identity()` explicitly never uses the operating system's
   PID. What specific failure would using a PID reintroduce?
3. An execution attempt requires a *current* actor lease and re-verifies
   its token inside its own transaction, rather than trusting the caller's
   earlier acquisition. What real race does that re-verification close?
4. The second process's assignment never reached `RUNNING`. Why does that
   matter more than merely "the result was discarded"?
5. "A worker that no longer holds the current lease may still be running."
   What, precisely, does the fence guarantee stop that worker from doing,
   and what does it explicitly *not* stop?

## Where to look next

- `src/sovereign_agent/fencing.py` — process identity, actor leases, and the
  execution-attempt compare-and-set. Note that the lease is released on every
  refusal path, not only on success — a leak there would strand an actor after
  any failure.

`solution.py` imports the production package rather than copying it.

Next: [Chapter 6 — The organization recovers](../ch06_the_organization_recovers/README.md)
