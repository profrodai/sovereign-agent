# Chapter 8 lab: migrate a populated catalog safely

## Challenge

Turn a populated, denormalized `catalog_v1` table into separate `products` and
`inventory` tables. Preserve every product, introduce database-enforced
inventory constraints, and prove that malformed legacy data rolls the entire
migration back instead of leaving a half-created schema.

Implement `exercise(root)` so it runs both a successful migration and a
duplicate-SKU failure experiment. Its deterministic observations must match
`expected.json`.

## Production map

- `sovereign_agent.database.MIGRATIONS` applies forward-only schema changes in
  transactions and records their versions.
- `reference_organizations.store.seed_catalog` treats SKU identity, stock, and
  reorder points as per-product facts.
- Persistence tests exercise upgrades with populated state, malformed
  migrations, rollback, and schema constraints.

This compact lab uses a new-table/copy/swap shape without hiding migration
failure behind `INSERT OR REPLACE`.

## Run it

```bash
cp book/labs/ch08_the_store_becomes_a_catalog/starter.py \
  book/labs/ch08_the_store_becomes_a_catalog/work.py
python book/labs/ch08_the_store_becomes_a_catalog/check.py \
  book/labs/ch08_the_store_becomes_a_catalog/work.py /tmp/sa-ch08-lab
```

Fill the numbered TODO seams in `work.py`. Once it passes, run it twice to
confirm the harness starts from the same known legacy state and produces the
same result. Use `solution.py` as a final comparison, not the starting point.

## Break it

Try these mutations one at a time:

1. Commit after creating `products` but before copying `inventory`.
2. Replace plain `INSERT` with `INSERT OR REPLACE` during the copy.
3. Remove `CHECK (reserved <= on_hand)`.
4. Disable foreign keys and insert inventory for an unknown SKU.
5. Drop `catalog_v1` before the copy has proved successful.

Observe which mutations destroy information and which merely postpone the
failure until later application code.

## Explain it back

Why must a migration be tested with existing rows rather than an empty test
database? Why is a duplicate a reason to stop instead of a reason to choose one
row? Which invariants belong in SQLite even if Python also validates them?
