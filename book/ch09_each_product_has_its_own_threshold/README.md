# Chapter 9 — Each product has its own threshold

Lucy sells a *lot* of vanilla and only a little of her weird lavender-honey
flavor. If both had the same "reorder when you hit 3 tubs" rule, one of two bad
things would happen: either she'd run out of vanilla constantly (3 is far too low
for something that flies out the door), or she'd drown in lavender-honey (3 is far
too high for something nobody buys). Different products need different thresholds.
That is obvious in a shop and surprisingly easy to get wrong in code, where it is
tempting to reach for one tidy constant.

Chapter 8 seeded a catalog where each SKU *had* its own reorder point, sitting in
its own row. This chapter proves that number actually *does its job* once real
sales start moving — that selling one product past its own line never trips
another's, and that the very same sale can be an alarm for one product and a
shrug for another.

## Learning objective

Prove, with real sales, that "independent reorder point" from Chapter 8
means what it says once a sale actually happens: selling tea past its own
threshold never flags coffee, and a small coffee sale that stays above
coffee's own (higher) threshold is correctly left alone — even though the
exact same-shaped sale already flagged tea.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Per-SKU threshold** | `below_reorder` evaluates EACH SKU's `on_hand` against THAT SKU's own `reorder_point` — never a catalog-wide number. |
| **Signal severity** | `record_sale`'s own `warning`/`info` distinction, now shown to depend on the selling SKU's own threshold, not a shared one. |

## The exercise

```bash
python book/ch09_each_product_has_its_own_threshold/solution.py --root /tmp/lucy-ch09
```

Read the file first. Two sales happen: 2 units of tea (4 on hand, reorder at
3 — this crosses it), then 1 unit of coffee (10 on hand, reorder at 6 — this
does not). Both are genuine calls to the same `record_sale` Chapter 0
already used.

## Expected observations

```json
{
  "opening_positions": {
    "SKU-COFFEE": { "on_hand": 10, "reorder_point": 6 },
    "SKU-TEA": { "on_hand": 4, "reorder_point": 3 }
  },
  "tea_sale": {
    "signal_severity": "warning",
    "on_hand_after": 2,
    "coffee_on_hand_unaffected": true
  },
  "below_reorder_after_tea_sale": ["SKU-TEA"],
  "small_coffee_sale": {
    "signal_severity": "info",
    "on_hand_after": 9
  },
  "below_reorder_after_small_coffee_sale": ["SKU-TEA"],
  "each_sku_evaluated_against_its_own_threshold": {
    "tea_flagged_at_its_own_lower_threshold": true,
    "coffee_not_flagged_by_a_sale_still_above_its_own_higher_threshold": true
  }
}
```

(`signal_id` values are omitted above — they are fresh, timestamp-prefixed
identifiers on every run; the exercise itself prints the real ones.)

The two facts this run proves:

1. **`coffee_on_hand_unaffected: true`.** Selling tea changed exactly one
   row in `inventory` — coffee's own `on_hand` is untouched, read back after
   the tea sale, not merely assumed.
2. **`signal_severity` is judged per SKU, against that SKU's own line.** The tea
   sale leaves 2 on hand, at-or-below tea's reorder point of 3, so its signal is
   `warning`. The coffee sale leaves 9, still above coffee's reorder point of 6,
   so its signal is `info`. These are two different-sized sales — that is the
   point: severity is not a property of how much sold, but of where each SKU
   landed relative to *its own* threshold. (Try editing the exercise to sell the
   *same* quantity from both — selling 2 of each still warns tea and leaves coffee
   at `info`, because 8 is above coffee's line of 6. The split follows the
   thresholds, not the quantities.)

Confirm it yourself:

```bash
sqlite3 /tmp/lucy-ch09/.sovereign/organization.db <<'SQL'
SELECT sku, on_hand, reorder_point, on_hand <= reorder_point AS below FROM inventory ORDER BY sku;
SQL
```

Expected: `SKU-TEA` shows `below = 1`; `SKU-COFFEE` shows `below = 0`.

## Learner verification command

```bash
python -m pytest tests/test_store_multi_sku.py -k "threshold or wake_gate_never_fires"
python scripts/verify_curriculum.py
```

Expected: all pass.

## Explain it back

1. `below_reorder` takes no SKU argument — it scans the whole `inventory`
   table. Where does the per-SKU comparison actually happen, in the SQL
   itself or in Python?
2. Why does this chapter sell only 1 unit of coffee, not 2 (the same
   quantity as the tea sale)? What would selling 2 units of coffee instead
   have shown, or failed to show?
3. If `CatalogEntry.reorder_point` were removed and replaced with one
   module-level constant shared by every SKU, which specific line of this
   chapter's own JSON output would become false first?

## Where to look next

- `src/reference_organizations/store/__init__.py` — `record_sale`,
  `below_reorder`
- `tests/test_store_multi_sku.py` — the signal-isolation and
  wake-decision-isolation tests this chapter's proof extends into Chapter 10

`solution.py` imports the production package rather than copying it.

Next: [Chapter 10 — One signal wakes one need](../ch10_one_signal_wakes_one_need/README.md)
