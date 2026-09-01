# Chapter 11 — Replenishment scales without losing governance

Here is the failure mode that ends most "it works!" demos: the guarantee that
held beautifully for one order quietly breaks the first time two orders run at
once. Two restocks in flight, and an effect meant for vanilla lands on chocolate;
or a retried order double-charges because "we already did this" was checked in
Python a heartbeat too late. A guarantee that only holds when the shop is quiet is
worse than no guarantee at all, because you will have learned to trust it.

So this chapter does the unglamorous, essential thing: it runs *two* complete
governed replenishment chains — every step you have built, from the self-woken
signal all the way to acceptance — and checks that every property still holds with
two SKUs in play. Nothing new is introduced. That is the point: scaling should
add products, not exceptions.

## Learning objective

Run TWO full governed replenishment chains to completion — Pulse-created
SOW, assignment, provider proposal, `apply_restock`, verification, review,
acceptance — and prove that scaling from one SKU to two loses none of the
governance properties Chapters 0-7 already established: no effect can be
attributed to the wrong assignment, and `apply_restock`'s own idempotency
holds independently for each SKU's own assignment.

## Vocabulary this chapter adds

None new — this chapter combines every mechanism Chapters 0-10 already
named (outcome, SOW, assignment, effect, verification, review, acceptance,
wake gate, Pulse) and proves they compose correctly at more than one SKU.

## The exercise

```bash
python book/ch11_replenishment_scales_without_losing_governance/solution.py --root /tmp/lucy-ch11
```

Read the file first. Both SKUs' signals fire, both get their own canonical
SOW and assignment through the same `run_pulse_once` Chapter 10 already
used, both run through `apply_restock` TWICE each (proving replay
idempotency per SKU), and both reach `ACCEPTED`.

## Expected observations

```json
{
  "both_assignments_completed": { "tea": true, "coffee": true },
  "idempotent_replay_per_sku": {
    "SKU-TEA": {
      "first_call_idempotent_replay": false,
      "second_call_idempotent_replay": true,
      "on_hand_after": 8
    },
    "SKU-COFFEE": {
      "first_call_idempotent_replay": false,
      "second_call_idempotent_replay": true,
      "on_hand_after": 11
    }
  },
  "effects_never_cross_assignments": {
    "each_assignment_authorizes_only_its_own_sku": true,
    "exactly_two_effect_rows": true
  },
  "both_outcomes_accepted": {
    "tea": "out_... ACCEPTED Keep the tea jar stocked",
    "coffee": "out_... ACCEPTED Keep the coffee tin stocked"
  }
}
```

Three facts this run proves:

1. **`second_call_idempotent_replay: true`, for BOTH SKUs.** Calling
   `apply_restock` a second time with the SAME assignment id never moves
   inventory or cash twice — `effects`' own `UNIQUE(assignment_id, kind,
   subject)` constraint (the same constraint from the single-SKU case) refuses the
   second write and returns the first call's own recorded payload instead.
   This is not new behavior; this chapter proves it still holds with two
   assignments in play, not one.
2. **`each_assignment_authorizes_only_its_own_sku: true`.** Reading the
   `effects` table directly: the tea assignment's own effect row names
   `SKU-TEA`; the coffee assignment's own effect row names `SKU-COFFEE`.
   Neither assignment's id appears next to the other SKU anywhere in the
   ledger.
3. **Both outcomes reach `ACCEPTED` independently.** Each SKU's own outcome
   goes through its OWN verify/review/accept sequence — accepting one never
   implicitly accepts or blocks the other.

Confirm it yourself:

```bash
sqlite3 /tmp/lucy-ch11/.sovereign/organization.db <<'SQL'
SELECT assignment_id, subject, kind FROM effects ORDER BY created_at;
SELECT id, state FROM outcomes ORDER BY id;
SQL
```

Expected: two `effects` rows, one per SKU; two `outcomes` rows, both
`ACCEPTED`.

## Learner verification command

```bash
python -m pytest tests/test_store_multi_sku.py -k "assignment_isolation or replenishment_effect or multiple_qualifying"
python -m pytest tests/test_store_multi_sku.py -k "two_real_connections"
python scripts/verify_curriculum.py
```

Expected: all pass. The second command is the REAL two-connection
concurrency proof — two genuinely separate database connections racing two
different SKUs' canonical creation — which this chapter's own sequential
exercise cannot demonstrate by itself.

## Explain it back

1. This chapter calls `apply_restock` twice for each SKU, on purpose. What
   specific database constraint makes the second call safe, and where is
   it declared?
2. `effects_never_cross_assignments` reads the `effects` table with one
   plain `SELECT`, no `WHERE assignment_id = ...` filter. Why does reading
   ALL rows, unfiltered, make this a stronger proof than checking one
   assignment's own rows in isolation?
3. This chapter's own exercise runs the two SKUs' chains SEQUENTIALLY, one
   after the other in Python. What property does the concurrency test
   (`test_two_real_connections_racing_two_different_skus_create_two_
   canonical_sows`) prove that this chapter's own sequential run cannot?

## Where to look next

- `src/reference_organizations/store/__init__.py` — `apply_restock`, the
  `UNIQUE(assignment_id, kind, subject)` idempotency constraint
- `tests/test_store_multi_sku.py` — the full isolation matrix, including
  the real two-connection concurrency proof this chapter's own exercise
  cannot show by itself
- `tests/test_store_multi_sku.py::...racing_two_different_skus...` — the
  canonical-creation transaction under genuine concurrent pressure

`solution.py` imports the production package rather than copying it.

Next: [Chapter 12 — The pilot begins with a receipt](../ch12_the_pilot_begins_with_a_receipt/README.md)
