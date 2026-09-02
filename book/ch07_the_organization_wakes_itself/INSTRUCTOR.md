# Instructor note — Chapter 7: The organization wakes itself

## Teaching intent

This is the payoff chapter for a thread every earlier chapter deliberately
left open: Chapter 0's exercise created no work from its own signal. The
teaching payoff is not "Pulse exists"—and Pulse must not be called a
heartbeat—it is that
this chapter's own claim ("the organization woke itself") is backed by
durable, structured, mechanically-checked evidence, not merely true prose.
This chapter is where the book's central discipline (a claim needs a check
behind it, Chapter 2's whole thesis) gets applied to the book's OWN writing,
not just to the software.

## Prerequisite knowledge

Chapter 5's fencing is directly reused, unchanged, by the assignment Pulse
creates — a learner who has not internalized "actor lease" and "execution
attempt" will not appreciate why `assignment_state: "COMPLETED"` in this
chapter's output is proof of something (no Pulse-only bypass), not just an
incidental fact. Chapters 0-6's full vocabulary (outcome, SOW, assignment,
signal) should already be fluent by this point.

## Likely misconceptions

- **"Pulse means the organization runs on a schedule now, in the
  background."** It does not. `run_pulse_once` is exactly what its name
  says: one deterministic pass, invoked explicitly (`sovereign-agent pulse
  --once`), with no looping, no cron, no OS service. Correct this
  immediately — it is the single most likely overclaim a learner will make
  after this chapter, and the book's own non-scope section says so
  explicitly ("no OS service, no scheduling, no cron, no webhooks").
- **"Pulse is the heartbeat."** It is not. Pulse converts business signals
  into governed work during one explicit pass. A heartbeat would publish
  process/actor liveness periodically; no such mechanism exists here. A
  scheduler could invoke Pulse, but scheduling would still not make Pulse a
  liveness protocol.
- **"Any chapter could claim Pulse fired if the prose sounds right."** This
  is the misconception to correct most forcefully, because it is the exact
  defect class this chapter's own mechanical guard exists to prevent. Point
  the learner at `scripts/verify_curriculum.py`'s chapter-scoped Pulse
  guard: it does not trust the WORDS "pulse fired" — it re-runs this
  chapter's own exercise and inspects the resulting database for a genuine
  `pulse.work_created` event and a traceable `pulse_origins` row. A
  fabricated event inserted directly (bypassing `run_pulse_once`) would
  fail this check even if the prose read identically. This is worth a full
  live demonstration if time allows: show the guard passing, then show it
  would fail against a hypothetical chapter that faked the event.

## Observation checkpoints

1. Before running the exercise: have the learner actually read the solution
   file and confirm, themselves, that `create_sow`, `ready_sow`, and
   `assign` do not appear anywhere in it — do not just tell them this, let
   them grep for it.
2. After running: confirm the learner reads `pulse_work_created_present:
   true` and understands this was READ BACK from the ledger's own event
   log, not asserted by the exercise's own summary text.
3. On the structured origin section: confirm the learner can walk the full
   chain themselves — signal id, to wake-decision's `source_signal_id`, to
   origin's `wake_decision_id`, to the SOW — using the `sqlite3` query
   provided, independent of the exercise's own Python output.
4. Confirm the learner notices `assignment_state: "COMPLETED"` and connects
   it to Chapter 5: this ran through the identical fencing every other
   assignment does, with no special Pulse path around it.

## Discussion prompts

- "The chapter-scoped Pulse guard inspects a fresh database after running
  this chapter's own exercise, rather than trusting the prose. What would
  you have to change about the guard if a future chapter wanted to make a
  similar 'genuinely happened' claim about some other proactive behavior?"
- "Chapters 0-6 are mechanically FORBIDDEN from claiming Pulse fired, even
  if it would be true by then (e.g., if a later chapter's exercise happened
  to run after this one in the same process). Why keep that prohibition
  unconditional by chapter number, rather than trying to detect 'did Pulse
  actually run before this point in the narrative'?"
- "This is the last written chapter. What's still missing from the whole
  system that you'd want before trusting it with a real store's real
  inventory?"

## Facilitation timing

Roughly 35-40 minutes guided: 10 minutes reading the solution file for what
is ABSENT (no manual dispatch calls) before running anything, 10 minutes on
the exercise output and the structured-origin `sqlite3` query, 10-15 minutes
on the mechanical-guard discussion above (worth the time investment — this
is the chapter where the book's own truthfulness becomes the subject, not
just the software's).

## Exercise debrief and assessment

A learner has landed this chapter if they can explain what would make this
chapter's own Pulse claim FALSE — this is the chapter's own final "Explain it
back" question, and it is deliberately the hardest one in the book: it asks
the learner to reason about how the CLAIM ITSELF could fail to be backed by
evidence, not just how the underlying feature could have a bug. This
directly maps onto `docs/andrea-chapters-0-7-evaluation.md`'s own Task 7,
which assesses exactly this: not "can Andrea run the pulse command," but
"can Andrea explain and independently verify that Pulse genuinely fired,"
using the offline `sqlite3` queries this chapter already taught. A learner
who can run the exercise and report `COMPLETED` but cannot explain why that
result is trustworthy — as opposed to merely printed — has not yet landed
this book's central lesson, applied one last time to its own newest and most
consequential claim.
