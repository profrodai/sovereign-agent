# Instructor note — Chapter 10: One signal wakes one need

## Teaching intent

Chapter 7's payoff was "the organization can wake itself up, with proof."
This chapter's payoff is narrower and more structural: given MORE than one
thing that could need attention, the gate binds each signal to exactly the
right need. This is the chapter where a learner who has only ever seen one
SKU's worth of Pulse activity has to update their mental model from "the
gate decides yes or no" to "the gate decides yes-for-THIS-outcome or no,"
which matters directly for trusting Chapter 11's governed replenishment at
scale.

## Prerequisite knowledge

Chapter 7's full vocabulary (signal, wake gate, wake decision, Pulse
origin) is a hard prerequisite — this chapter does not re-teach any of it,
it re-uses it under a new condition (two qualifying signals instead of
one). Chapter 9's per-SKU threshold proof is also assumed.

## Likely misconceptions

- **"The gate picks the FIRST matching outcome, so order matters."** It
  does not pick by order — it filters outcomes by `subject == sku` AND
  `state == ACTIVE`, and refuses (returns `None`) unless EXACTLY one
  matches. "Break it" now runs this for real: the mutation that DOES pick
  the first match on ambiguity gets the older row purely as an artifact of
  SQLite's own row order, never a governed fact. Point the learner at the
  comparison table right after the mutated run and have them state, in
  their own words, why "picked the first row" and "resolved the ambiguity
  correctly" are indistinguishable from the caller's side.
- **"Two signals means Pulse runs twice."** `run_pulse_once` is still one
  deterministic pass — it evaluates every unevaluated signal within that
  one call, not once per signal. Confirm the learner reads `report.items`
  as a single pass's own result covering both signals, not two separate
  invocations.
- **"This chapter proves replenishment isolation."** It does not — it
  proves signal-to-outcome BINDING and canonical SOW creation are correct.
  Chapter 11 is where the actual replenishment effects (inventory, cash)
  are shown not to cross between SKUs.
- **"A stale signal just means the alert was late."** The `severity`
  section shows the more precise failure mode: staleness is not about
  timing, it is about which field the gate is willing to trust. The signal
  itself is never wrong (it recorded a true fact for a moment in the
  past); the mistake would be treating a snapshot field as if it were a
  live one. Have the learner say what would happen if `store_wake_gate`
  branched on `signal.severity == "warning"` instead of calling
  `below_reorder(org.db)` again.

## Observation checkpoints

1. Before running: have the learner predict how many `pulse_wake_decisions`
   rows will exist after this exercise runs, and why.
2. After running: confirm the learner can name, from the JSON output alone,
   which `sow_id` belongs to tea and which belongs to coffee — without
   re-running the exercise or guessing from ordering.
3. On the `sqlite3` query: confirm the learner reads `subject` directly
   from `pulse_wake_decisions` and matches it to the correct `sow_id` via
   the join, independent of the exercise's own summary.

## Discussion prompts

- "What test in `tests/test_store_multi_sku.py` proves this same binding
  property under a REAL concurrent race, rather than the sequential order
  this chapter's exercise happens to run in?"
- "If a third SKU were added to this chapter's catalog with no active
  outcome naming it, what would `store_wake_gate` do with a qualifying
  signal for that SKU?"
- "'Break it' shows two refusal causes (zero matches, ambiguous matches)
  collapsing to the same `None`. Name a system you've used where an error
  message DID distinguish those two causes to the caller, and say whether
  `store_wake_gate` losing that distinction is a real cost or a deliberate,
  acceptable simplification given what a Pulse pass does with the result."

## Facilitation timing

Roughly 25-30 minutes: 5 minutes reviewing Chapter 7's gate mechanism, 10
minutes on the exercise output and the `sqlite3` cross-check, 5-10 minutes
on "Break it" and the severity/live-read distinction, 5-10 minutes on the
discussion prompts, particularly the concurrency-test pointer.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain what `store_wake_
gate` would do (refuse, via `len(matching) != 1`) if this chapter
accidentally created two ACTIVE outcomes for the same SKU, AND has now
watched it happen against the real function in "Break it" — the two
should agree. A learner has landed the severity material if they can state,
without re-reading the source, which fields on a `Signal` the gate reads
(`kind`, `source`, `subject_ref`) and which one it deliberately never reads
(`severity`), and why that omission is the whole point rather than an
oversight.
