# Instructor note — Chapter 9: Each product has its own threshold

## Teaching intent

Chapter 8 proved independence at rest (the seeded rows differ). This
chapter proves independence under the SAME kind of action Chapters 0-7
already trusted for one SKU: a sale. The teaching payoff is the contrast
between the two sales in the exercise — same function, same shape of call,
different SKU, different correct outcome — which is a stronger proof of
"per-SKU, not per-catalog" than simply asserting the code reads a
`reorder_point` column.

## Prerequisite knowledge

Chapter 0's `record_sale`/signal vocabulary, and Chapter 8's catalog. A
learner who has not seen `record_sale` produce a `severity` of `warning` vs.
`info` in Chapter 0 will not immediately understand why this chapter's own
contrast (`warning` for tea, `info` for coffee, same 1-2 unit sale shape) is
the point.

## Likely misconceptions

- **"Selling less of coffee is why it wasn't flagged."** Quantity alone is
  not the reason — REORDER POINT is. A facilitator should have the learner
  compute what would happen if 5 units of coffee were sold instead (10 - 5 =
  5, still not below reorder_point 6... wait, 5 < 6, so it WOULD flag) to
  sharpen the distinction between "sold less" and "still above this SKU's
  own threshold."
- **"`below_reorder` must take a SKU parameter somewhere I'm not seeing."**
  It does not — it scans the whole table and lets each row's own
  `reorder_point` column do the comparison. This is worth pointing at
  directly in `src/reference_organizations/store/__init__.py`.
- **"This proves signals are isolated."** It proves inventory state and
  severity are isolated. Signal ROW isolation (two SKUs never sharing a
  `dedupe_key` or signal id) is a related but distinct property, covered in
  `tests/test_store_multi_sku.py`, not directly observed in this chapter's
  own exercise output.

## Observation checkpoints

1. Before running: have the learner predict, in writing, what
   `small_coffee_sale.signal_severity` will be, and why — before seeing the
   real output.
2. After running: confirm the learner connects `on_hand_after: 9` and
   `reorder_point: 6` to `signal_severity: "info"` themselves, not by
   reading the summary field that already states it.
3. On the `sqlite3` query: confirm the learner reads `below = 1` for tea and
   `below = 0` for coffee directly from SQL, independent of the exercise's
   own Python-computed booleans.

## Discussion prompts

- "Chapter 8 proved the catalog's OPENING state was independent. What
  specifically does THIS chapter add that Chapter 8 could not have shown?"
- "What would a bug that accidentally shared one `reorder_point` across the
  whole catalog look like in this chapter's own output — which field would
  change first?"

## Facilitation timing

Roughly 15-20 minutes: 5 minutes predicting the coffee sale's severity
before running, 5-10 minutes on the actual output and the `sqlite3`
cross-check, 5 minutes on the discussion prompts.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain, unprompted, why the
coffee sale's signal is `info` rather than `warning` using coffee's OWN
reorder point (not tea's, not a shared default) — and can state what
quantity of coffee sold WOULD have produced `warning` instead.
