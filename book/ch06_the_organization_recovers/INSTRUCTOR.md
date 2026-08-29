# Instructor note — Chapter 6: The organization recovers

## Teaching intent

This chapter closes the loop Chapter 1 opened when it discussed a crash
between two writes, and directly operationalizes Unit 5's rule ("a process
cannot record its own death"). The teaching payoff is watching a REAL
process get REAL `SIGKILL`ed and observing the ledger's own honest account of
that moment (still `RUNNING`, execution attempt still referenced) before a
second process — the supervisor — decides what happened and writes a
receipt that never guesses success.

## Prerequisite knowledge

Chapter 5's fencing vocabulary is required: recovery is specifically about
what happens to an execution attempt when the process that acquired it stops
existing. A learner who has not internalized "execution attempt" and
"expiry" from Chapter 5 will not understand what the supervisor is actually
checking for here.

## Likely misconceptions

- **"This must be simulated — you can't actually kill a process in a
  teaching exercise."** It is not simulated. Say this explicitly before
  running the exercise: a real child process is started, the exercise
  genuinely waits (polling, not a fixed sleep) until it has acquired its
  execution attempt and reached `RUNNING`, and then it receives a real
  `SIGKILL` — the one signal a Python program cannot catch. If a learner
  doubts this, have them read `tests/fixtures/hard_kill_worker.py` directly.
- **"The recovered receipt says `failed` because the work actually failed."**
  It says `failed` because the organization has NO WAY TO KNOW what the
  subprocess would have produced — it might have been one line from writing
  a valid completed report. `failure_category="worker_lost"` names the
  ignorance honestly; it does not claim the work was bad.
- **"A second supervisor tick will recover the same assignment again."** It
  will not — recovery clears the fence in the SAME transaction as the
  terminal write, so a second tick finds nothing left to recover. This is
  the idempotency property the exercise's own `second_tick_is_idempotent`
  field demonstrates directly; do not let a learner assume this without
  seeing the `0` in the output.

## Observation checkpoints

1. Before recovery: confirm the learner reads `assignment_state: "RUNNING"`
   and `execution_attempt_still_referenced: true` and can explain why the
   ledger is telling the truth at this moment, not lying.
2. After the first tick: confirm the learner connects `recovered_count: 1`
   to the specific assignment that was killed — not just a count in the
   abstract.
3. After the second tick: confirm the learner predicts `recovered_count: 0`
   BEFORE seeing it, based on the fence-clearing argument above.
4. On the receipt: confirm the learner reads BOTH `receipt_status: "failed"`
   and `receipt_failure_category: "worker_lost"` and can distinguish this
   from a receipt that says the work was attempted and genuinely failed for
   a different reason (a malformed report, a timeout).

## Discussion prompts

- "No new `AssignmentState` was added for a recovered assignment — it
  reuses `FAILED`. What would a facilitator or auditor lose if there were a
  separate `RECOVERED` state instead?"
- "The far-future clock stands in for a real 15-minute wait. What would
  change about this exercise's teaching value if it genuinely waited 15
  minutes instead — and why did this project choose not to make a learner
  do that?"
- "If you were designing a retry policy on top of this recovery mechanism,
  what would you need to know about the killed work before deciding whether
  to retry it automatically? Why does this unit deliberately not build that
  retry policy?"

## Facilitation timing

Roughly 20-25 minutes guided, most of it waiting for the real subprocess and
discussing the output rather than reading new material — the exercise itself
takes a few real seconds to run (do not schedule this as instantaneous). Do
not compress the "before recovery" observation step; it is the one most
learners skip past to get to the "interesting" recovered-receipt result.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain, unprompted, why the
recovery receipt is always `failed` regardless of how far the killed
subprocess actually got — and can connect this back to Unit 5's own rule
("nothing is ever a guessed success") as the same principle applied to a
harder case (a hard kill, not merely a caught exception). A learner who
frames the recovered receipt as "the system deciding the work failed" rather
than "the system honestly admitting it does not know" has not yet landed
this chapter's central distinction.
