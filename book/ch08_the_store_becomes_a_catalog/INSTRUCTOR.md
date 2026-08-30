# Instructor note — Chapter 8: The Store becomes a catalog

## Teaching intent

This chapter opens Unit 11's own arc (Chapters 8-12) the same way Chapter 4
opened the workspace-lifecycle arc: it introduces the new vocabulary at its
simplest possible shape, with no sale, no signal, and no governed work yet
in the picture. The teaching payoff is narrow on purpose — "a catalog is
more than one independently-tracked product row" — so that Chapter 9 can
build stock thresholds on it, Chapter 10 can build signal routing on it, and
Chapter 11 can build governed replenishment on it, each chapter adding
exactly one new fact rather than re-deriving the catalog concept from
scratch.

## Prerequisite knowledge

Chapter 1's canonical-vs-projection distinction (`products` and `inventory`
are real SQLite tables, read back after the fact) and Chapter 0's
`Product`/`InventoryPosition` vocabulary. A learner who has not internalized
"the database, not the Python object, is the truth" will not appreciate why
this chapter reads `products_table` and `inventory_table` back with raw SQL
rather than trusting `seed_catalog`'s own return value.

## Likely misconceptions

- **"`seed_catalog` replaced `seed`."** It did not. `seed` is untouched and
  still seeds exactly one product (`SKU-TEA`) — every chapter and test
  written before Unit 11 depends on that exact behavior. `seed_catalog` is
  a genuinely new, additive entry point. Point at `src/reference_
  organizations/store/__init__.py` and have the learner confirm both
  functions exist, unmodified relative to each other.
- **"More SKUs means a bigger `products` table with more columns."** The
  schema did not change at all — `products` and `inventory` already had a
  `sku` primary/foreign key from Unit 2 onward. What changed is how many
  ROWS `seed_catalog` writes, not the shape of any row. This is worth
  contrasting explicitly with the pilot-start mechanism (Chapter 12), which
  DOES add new tables — a learner should be able to say which kind of
  change this chapter is and which kind Chapter 12 is.
- **"Independent reorder points means the values just happen to differ."**
  They differ because `CatalogEntry` carries `on_hand` and `reorder_point`
  per SKU, not because of coincidence. A facilitator should have the learner
  trace one instance of `CatalogEntry` in `DEFAULT_CATALOG` to its own row
  in the exercise's `inventory_table` output.

## Observation checkpoints

1. Before running: have the learner read `seed_catalog`'s own docstring and
   summarize, in their own words, why it does not replace `seed`.
2. After running: confirm the learner reads `not_all_the_same: true` and
   explains what a hypothetical bug (e.g. `CatalogEntry`'s `reorder_point`
   silently defaulting to the same value for every SKU) would have produced
   here instead.
3. On the `sqlite3` query: confirm the learner can run it themselves and
   match its two rows against the exercise's own JSON output, independent
   of the Python summary.

## Discussion prompts

- "This chapter proves a catalog EXISTS. What does it deliberately NOT yet
  prove — about sales, signals, or replenishment — that Chapters 9 through
  11 each add one piece of?"
- "Why does `seed_catalog` refuse fewer than two SKUs (`ValueError`) instead
  of silently accepting a one-product catalog?"

## Facilitation timing

Roughly 15-20 minutes: 5 minutes reading `seed_catalog` and `CatalogEntry`
before running anything, 5-10 minutes on the exercise output and the
`sqlite3` cross-check, 5 minutes on the discussion prompts above. Shorter
than Chapter 7 — this chapter's own claim is narrower.

## Exercise debrief and assessment

A learner has landed this chapter if they can point at the exact two
`CatalogEntry` values in `DEFAULT_CATALOG` and match each one to its own row
in both `products_table` and `inventory_table` in the exercise's output,
and can state — without looking it up again — why `seed` was left alone
rather than folded into `seed_catalog`.
