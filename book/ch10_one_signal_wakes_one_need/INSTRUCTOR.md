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
  matches. Point at `store_wake_gate`'s own `len(matching) != 1` check and
  have the learner explain what happens if this chapter accidentally
  created two ACTIVE outcomes for the same SKU.
- **"Two signals means Pulse runs twice."** `run_pulse_once` is still one
  deterministic pass — it evaluates every unevaluated signal within that
  one call, not once per signal. Confirm the learner reads `report.items`
  as a single pass's own result covering both signals, not two separate
  invocations.
- **"This chapter proves replenishment isolation."** It does not — it
  proves signal-to-outcome BINDING and canonical SOW creation are correct.
  Chapter 11 is where the actual replenishment effects (inventory, cash)
  are shown not to cross between SKUs.

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

## Facilitation timing

Roughly 20-25 minutes: 5 minutes reviewing Chapter 7's gate mechanism, 10
minutes on the exercise output and the `sqlite3` cross-check, 5-10 minutes
on the discussion prompts, particularly the concurrency-test pointer.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain what `store_wake_
gate` would do (refuse, via `len(matching) != 1`) if this chapter
accidentally created two ACTIVE outcomes for the same SKU — reasoning from
the gate's own fail-closed contract, not from having watched it happen.
