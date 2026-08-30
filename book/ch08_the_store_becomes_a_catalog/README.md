# Chapter 8 — The Store becomes a catalog

## Learning objective

See the Store's single-product fixture become a genuine catalog: two
distinct SKUs, each with its own row in `products` and its own row in
`inventory`, seeded by one production function call — and learn what
"independent" means at the schema level, before any sale or signal is
involved.

Chapters 0-7 all called `reference_organizations.store.seed`, which creates
exactly one product, `SKU-TEA`. That function still exists, unchanged — every
chapter and test written before this one depends on its exact shape. This
chapter uses the new function alongside it, `seed_catalog`, which is what a
real store with more than one product on the shelf actually needs.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Catalog** | More than one `Product`, each with its own `products` row and its own `inventory` row — not one product repeated, not a single row carrying a list. |
| **`CatalogEntry`** | One SKU's own opening position: the product itself, plus its own starting `on_hand` and `reorder_point`, independent of every other entry in the same catalog. |
| **`seed_catalog`** | The production function that writes a whole catalog in one transaction. Additive alongside `seed`, never a replacement for it. |

## The exercise

```bash
python book/ch08_the_store_becomes_a_catalog/solution.py --root /tmp/andrea-ch08
```

Read the file first. `seed_catalog` is called once, with the default
two-SKU catalog (`SKU-TEA` and `SKU-COFFEE`) — no loop written by this
chapter, no manual `INSERT`, nothing that copies what `seed_catalog` already
does inside the production package.

## Expected observations

```json
{
  "catalog_size": {
    "distinct_skus_seeded": 2,
    "skus": ["SKU-COFFEE", "SKU-TEA"],
    "at_least_two": true
  },
  "products_table": [
    {
      "sku": "SKU-COFFEE",
      "record": {
        "sku": "SKU-COFFEE",
        "name": "Kenyan coffee",
        "unit_cost_cents": 210,
        "price_cents": 650
      }
    },
    {
      "sku": "SKU-TEA",
      "record": {
        "sku": "SKU-TEA",
        "name": "Assam tea",
        "unit_cost_cents": 120,
        "price_cents": 400
      }
    }
  ],
  "inventory_table": [
    { "sku": "SKU-COFFEE", "on_hand": 10, "reserved": 0, "reorder_point": 6 },
    { "sku": "SKU-TEA", "on_hand": 4, "reserved": 0, "reorder_point": 3 }
  ],
  "independent_reorder_points": {
    "distinct_reorder_points": [3, 6],
    "not_all_the_same": true
  },
  "default_catalog_entry_count": 2
}
```

Three facts this run proves, not merely states:

1. **`distinct_skus_seeded: 2`.** Two real rows in `products`, read back
   from the database after `seed_catalog` returns — not the length of a
   Python list this chapter's own code built.
2. **`not_all_the_same: true`.** `SKU-TEA`'s reorder point (3) and
   `SKU-COFFEE`'s reorder point (6) are genuinely different numbers, seeded
   from two different `CatalogEntry` values. A catalog where every SKU
   happened to share one threshold would not prove independence; this one
   cannot be mistaken for that.
3. **`SKU-TEA` unchanged.** Compare this chapter's `SKU-TEA` row to Chapter
   0's: same cost, same price, same opening stock. `seed_catalog` did not
   invent a new tea fixture — it seeded the SAME `SKU-TEA` the rest of this
   book already knows, alongside a second, genuinely new product.

Confirm it yourself, independent of this exercise's own summary:

```bash
sqlite3 /tmp/andrea-ch08/.sovereign/organization.db <<'SQL'
SELECT sku, on_hand, reorder_point FROM inventory ORDER BY sku;
SQL
```

Expected: two rows, `SKU-COFFEE` and `SKU-TEA`, with different
`reorder_point` values.

## Learner verification command

```bash
python -m pytest tests/test_store_multi_sku.py -k "sales_isolation or a_sale_of_one_sku"
python scripts/verify_curriculum.py
```

Expected: all pass. The pytest selection proves a sale of one SKU cannot
touch another SKU's own row — this chapter only seeds the catalog, but the
isolation the rest of this unit relies on starts here, at the schema.

## Explain it back

1. `seed` and `seed_catalog` both exist in the same module. Why keep `seed`
   at all, instead of just widening it to take a list of products?
2. `CatalogEntry` carries `on_hand` and `reorder_point` per entry, not as
   catalog-wide defaults. What real bug would a single shared `reorder_point`
   for every SKU cause, once a sale is involved?
3. This chapter's own database has two `products` rows and two `inventory`
   rows. Where does `cash_entries` NOT get one row per SKU — and why is that
   the correct design, not a gap?
4. What would make this chapter's own "at least two independent SKUs" claim
   FALSE, even if `distinct_skus_seeded` still printed `2`?

## Where to look next

- `src/reference_organizations/store/__init__.py` — `seed_catalog`,
  `CatalogEntry`, `DEFAULT_CATALOG`
- `tests/test_store_multi_sku.py` — the full multi-SKU isolation proof
  matrix this unit's own acceptance requires
- `docs/v1-unit11-store-expansion-pilot-start.md` — the full contract

`solution.py` imports the production package rather than copying it.

Next: [Chapter 9 — Each product has its own threshold](../ch09_each_product_has_its_own_threshold/README.md)
