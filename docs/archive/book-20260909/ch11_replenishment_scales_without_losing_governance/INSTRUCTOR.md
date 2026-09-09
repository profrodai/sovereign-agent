# Instructor note — Chapter 11: Replenishment scales without losing governance

## Teaching intent

This is Unit 11's own payoff chapter, the way Chapter 7 was Unit 9's: it
combines every mechanism the preceding chapters (0-10) taught, at more than
one SKU, and proves nothing was silently weakened by scaling. The teaching
point is not "two replenishments happened" — it is that the SAME
constraints (idempotency, effect attribution, independent acceptance) that
made ONE SKU's replenishment trustworthy in Chapter 0 still hold, unweakened,
once a second SKU is added to the picture.

## Prerequisite knowledge

The full Chapter 0 governance vocabulary (outcome, SOW, assignment,
evidence, verification, review, acceptance) and Chapter 10's signal-to-SKU
binding. A learner who cannot already explain why `apply_restock`'s
`UNIQUE(assignment_id, kind, subject)` constraint makes a SECOND call safe
in the single-SKU case will not appreciate why proving it again for TWO
SKUs is meaningful rather than redundant.

## Likely misconceptions

- **"Scaling to two SKUs just means running the same code twice."** In one
  sense that is exactly right — and that is the POINT: nothing in
  `apply_restock`, `run_pulse_once`, or the verify/review/accept chain
  needed to change to support a second SKU. The risk this chapter guards
  against is not "the code doesn't run twice" but "running it twice
  accidentally lets state leak between the two runs" — which the effects
  table query directly refutes.
- **"The second `apply_restock` call for each SKU actually re-orders more
  stock."** It does not — `second_call_idempotent_replay: true` means the
  SECOND call returned the FIRST call's own recorded result without
  writing anything new. `on_hand_after` reflects only the first call's
  effect, not double the quantity.
- **"This chapter's sequential exercise IS the concurrency proof."** It
  is not, and this is worth stating explicitly: this chapter's own
  `solution.py` runs tea's chain, then coffee's, one after another in plain
  Python — never actually racing. The REAL concurrency proof lives in
  `tests/test_store_multi_sku.py`'s own two-connection test, pointed to
  directly in this chapter's own "Explain it back."

## Observation checkpoints

1. Before running: have the learner predict, before seeing output, whether
   `on_hand_after` for tea will reflect one restock or two, given that
   `apply_restock` is called twice.
2. After running: confirm the learner reads the `effects` table query
   themselves and confirms, unaided, that no row's `assignment_id` and
   `subject` are mismatched.
3. Have the learner run the pointed-to concurrency test
   (`test_two_real_connections_racing_two_different_skus_create_two_
   canonical_sows`) themselves and read its own assertions, connecting it
   back to this chapter's sequential exercise as the property that exercise
   alone cannot prove.

## Discussion prompts

- "If `effects` lacked its own `UNIQUE(assignment_id, kind, subject)`
  constraint, what would this chapter's second `apply_restock` call have
  done instead — and how would you notice from this chapter's own output
  alone?"
- "This chapter accepts both outcomes independently. What would it mean,
  operationally, if accepting the tea outcome accidentally also accepted
  the coffee outcome? Which check in `checks.py` or `organization.py` would
  have to fail for that to happen?"

## Facilitation timing

Roughly 30-35 minutes: 10 minutes reviewing the full governance chain from
memory before running anything, 10-15 minutes on the exercise output and
the `sqlite3` cross-checks, 10 minutes running and discussing the real
concurrency test. The longest chapter in this unit's own arc — it is
deliberately the capstone.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain, from the `effects`
table alone (no Python summary), why the ledger proves isolation rather
than merely suggesting it — and can then run the real two-connection
concurrency test themselves and explain what property it adds beyond what
this chapter's own sequential exercise already showed.
