# Chapter 8 — The Store becomes a catalog

Up to now Lucy's shop has sold exactly one thing. That was a convenient lie — it
let us build memory, judgement, boundaries, fencing, recovery, and a heartbeat
without the distraction of a second product. But a real ice cream shop has
vanilla *and* chocolate, and the moment there are two, a new question appears that
never existed with one: **when something happens to one product, does it stay
contained to that product?** A run on vanilla must not quietly change the
chocolate count. A low-stock signal for one flavor must not reorder the other.

This chapter is the smallest possible version of that step — turning the single
product into a genuine *catalog* of independent SKUs — because independence is
easiest to get right at the very beginning, at the schema, before any sale or
signal can blur the lines. (The shipped catalog uses two example SKUs to make the
mechanics concrete; they behave exactly as Lucy's vanilla and chocolate would.)

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

## Build the migration yourself: one product becomes a catalog, without losing the shop

"Add a SKU" sounds like data entry. It is a **schema evolution on populated
data** — the exact discipline Chapter 1 built — and the shop that needs it
is already running, with money in the till and history in the ledger. Start
from the tempting one-product schema most systems begin with:

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
    CREATE TABLE shop (id INTEGER PRIMARY KEY CHECK (id = 1),
                       product_name TEXT, on_hand INT, reorder INT);
    CREATE TABLE events (seq INTEGER PRIMARY KEY, kind TEXT, sku TEXT);
""")
db.execute("INSERT INTO shop VALUES (1, 'Assam tea', 4, 3)")
db.execute("INSERT INTO events(kind, sku) VALUES ('sale.committed', 'SKU-TEA')")
db.execute("INSERT INTO events(kind, sku) VALUES ('replenishment.committed', 'SKU-TEA')")
db.commit()
print(db.execute("SELECT * FROM shop").fetchone())
print("history rows:", db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
```

```text
(1, 'Assam tea', 4, 3)
history rows: 2
```

The `CHECK (id = 1)` is the one-product assumption made structural: this
table *cannot* hold a second product. Before reading further, design the
replacement yourself — you need product **identity**, product **display
name**, and stock **quantities**, and the design question is which of those
are the same concern. Predict what goes wrong if the name is the key. Then
compare with what follows.

### The migration, on live data, in one transaction

Three separate concerns get three separate homes: identity (`sku`, the
primary key — opaque, stable, never shown to customers), the display name
(mutable prose *about* the identity), and quantities (their own row, with a
constraint that makes negative stock unrepresentable):

```python
def migrate_to_catalog(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        db.execute("""
            CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL,
                                   price_cents INT NOT NULL)
        """)
        db.execute("""
            CREATE TABLE inventory (sku TEXT PRIMARY KEY REFERENCES products(sku),
                                    on_hand INT NOT NULL CHECK (on_hand >= 0),
                                    reserved INT NOT NULL DEFAULT 0,
                                    reorder INT NOT NULL)
        """)
        name, on_hand, reorder = db.execute(
            "SELECT product_name, on_hand, reorder FROM shop WHERE id = 1"
        ).fetchone()
        db.execute("INSERT INTO products VALUES ('SKU-TEA', ?, 400)", (name,))
        db.execute(
            "INSERT INTO inventory(sku, on_hand, reorder) VALUES ('SKU-TEA', ?, ?)",
            (on_hand, reorder),
        )
        migrated = db.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        original = db.execute("SELECT COUNT(*) FROM shop").fetchone()[0]
        if migrated != original:
            raise RuntimeError(f"row count mismatch: {original} became {migrated}")
        db.execute("DROP TABLE shop")
        db.execute("COMMIT")
        return "migrated: singleton shop is now a catalog"
    except BaseException:
        db.execute("ROLLBACK")
        raise


print(migrate_to_catalog(db))
print(db.execute("SELECT sku, name, price_cents FROM products").fetchone())
print(db.execute("SELECT sku, on_hand, reserved, reorder FROM inventory").fetchone())
print("history rows survived:", db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
```

```text
migrated: singleton shop is now a catalog
('SKU-TEA', 'Assam tea', 400)
('SKU-TEA', 4, 0, 3)
history rows survived: 2
```

Everything from Chapter 1 is load-bearing here: the copy, the count check,
the `DROP`, and the version stamp of a real migration all ride one
`BEGIN IMMEDIATE` — and the count check is the migration verifying *itself*
before it burns the bridge. The four on-hand tubs and both history rows
crossed intact. This is a guest arriving in a house where data already
lives, exactly as the production schema's own sixteen forward-only
migrations each had to be.

### Seeding a catalog is a validated act, not a loop of inserts

```python
def seed_catalog(db, entries):
    if len(entries) < 2:
        return "refused: a catalog needs at least two distinct SKUs"
    skus = [sku for sku, _, _, _, _ in entries]
    if len(set(skus)) != len(skus):
        return f"refused: duplicate SKUs in catalog: {skus}"
    if any(on_hand < 0 for _, _, _, on_hand, _ in entries):
        return "refused: negative opening stock is unrecorded debt, not inventory"
    db.execute("BEGIN IMMEDIATE")
    try:
        for sku, name, price, on_hand, reorder in entries:
            db.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?)", (sku, name, price))
            db.execute(
                "INSERT OR REPLACE INTO inventory(sku, on_hand, reorder) VALUES (?, ?, ?)",
                (sku, on_hand, reorder),
            )
        db.execute("COMMIT")
        return f"seeded {len(entries)} SKUs"
    except BaseException:
        db.execute("ROLLBACK")
        raise


print(seed_catalog(db, [("SKU-TEA", "Assam tea", 400, 4, 3)]))
print(seed_catalog(db, [("SKU-TEA", "Assam tea", 400, 4, 3), ("SKU-TEA", "Also tea", 500, 9, 6)]))
print(
    seed_catalog(
        db, [("SKU-TEA", "Assam tea", 400, 4, 3), ("SKU-COFFEE", "Kenyan coffee", 650, -2, 6)]
    )
)
print(
    seed_catalog(
        db, [("SKU-TEA", "Assam tea", 400, 4, 3), ("SKU-COFFEE", "Kenyan coffee", 650, 10, 6)]
    )
)
rows = db.execute("SELECT sku, on_hand, reorder FROM inventory ORDER BY sku").fetchall()
print(rows)
```

```text
refused: a catalog needs at least two distinct SKUs
refused: duplicate SKUs in catalog: ['SKU-TEA', 'SKU-TEA']
refused: negative opening stock is unrecorded debt, not inventory
seeded 2 SKUs
[('SKU-COFFEE', 10, 6), ('SKU-TEA', 4, 3)]
```

Three refusals, three different edge cases the map warned about. A
one-entry "catalog" is the singleton assumption sneaking back in a list
costume. Duplicate SKUs would make `INSERT OR REPLACE` silently collapse
two products into one — validated *before* the transaction opens, so the
refusal costs nothing. And negative opening stock is refused twice over:
once by the seed's own validation, and structurally by the `CHECK
(on_hand >= 0)` the migration installed — belt because the error message is
better, suspenders because a seed that skipped validation still cannot
write the lie. Production's `seed_catalog` carries the first two refusals
almost verbatim (`a catalog needs at least two distinct SKUs`,
`duplicate SKUs in catalog`), seeds everything in one transaction, and adds
the one deliberate shared resource — a single opening cash balance, because
a store has one till, not one per SKU.

### The fault, again, because populated data raises the stakes

```python
db2 = sqlite3.connect(":memory:")
db2.executescript("""
    CREATE TABLE shop (id INTEGER PRIMARY KEY CHECK (id = 1),
                       product_name TEXT, on_hand INT, reorder INT);
    CREATE TABLE events (seq INTEGER PRIMARY KEY, kind TEXT, sku TEXT);
""")
db2.execute("INSERT INTO shop VALUES (1, 'Assam tea', 4, 3)")
db2.commit()


def migrate_but_crash(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        db.execute("CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT, price_cents INT)")
        db.execute("INSERT INTO products VALUES ('SKU-TEA', 'Assam tea', 400)")
        raise RuntimeError("power cut before inventory was copied and shop dropped")
    except RuntimeError as error:
        db.execute("ROLLBACK")
        return f"fault: {error}"


print(migrate_but_crash(db2))
tables = [
    r[0] for r in db2.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
]
print("tables after the fault:", tables)
print("the shop row, untouched:", db2.execute("SELECT * FROM shop").fetchone())
```

```text
fault: power cut before inventory was copied and shop dropped
tables after the fault: ['events', 'shop']
the shop row, untouched: (1, 'Assam tea', 4, 3)
```

No `products` table left behind, no half-copied catalog, and the running
shop exactly as it was — the second half of Chapter 1's migration lesson,
now with live inventory on the line. A migration that can strand a shop
between two schemas is worse than no migration.

### The payoff of identity: the name is free to change

```python
db.execute("UPDATE products SET name = 'Lucy''s house blend' WHERE sku = 'SKU-TEA'")
db.commit()
print(db.execute("SELECT sku, name FROM products WHERE sku = 'SKU-TEA'").fetchone())
linked = db.execute("SELECT COUNT(*) FROM events WHERE sku = 'SKU-TEA'").fetchone()[0]
print("history rows still bound to the identity:", linked)
```

```text
('SKU-TEA', "Lucy's house blend")
history rows still bound to the identity: 2
```

Lucy rebrands the tea; every sale, signal, and replenishment in the history
still points at `SKU-TEA`, untouched. Had the *name* been the key, that
rename would have orphaned the entire history — or been forbidden forever.
Identity is what the ledger binds to; the display name is prose about it.
One more design note worth carrying from production: `seed_catalog` is
*additive alongside* the old single-product `seed`, never a replacement —
every chapter and test written before the catalog existed still relies on
the old contract, and breaking it out from under them is exactly the
revert-what-works move this book's Chapter 1 warned against. Schemas grow
the way ledgers do: forward.

## The exercise

```bash
uv run python book/ch08_the_store_becomes_a_catalog/solution.py --root /tmp/lucy-ch08
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
sqlite3 /tmp/lucy-ch08/.sovereign/organization.db <<'SQL'
SELECT sku, on_hand, reorder_point FROM inventory ORDER BY sku;
SQL
```

Expected: two rows, `SKU-COFFEE` and `SKU-TEA`, with different
`reorder_point` values.

## Learner verification command

```bash
uv run python -m pytest tests/test_store_multi_sku.py -k "sales_isolation or a_sale_of_one_sku"
uv run python scripts/verify_curriculum.py
```

Expected: all pass. The pytest selection proves a sale of one SKU cannot
touch another SKU's own row — this chapter only seeds the catalog, but the
isolation the next chapters rely on starts here, at the schema.

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
5. The migration's count check runs BEFORE `DROP TABLE shop`, inside the
   same transaction. Explain what each of those two placement decisions
   protects, separately.
6. Negative opening stock is refused twice — by the seed's validation and
   by the `CHECK` constraint. Why keep both, when either alone would stop
   the write?
7. The rename demo changed the display name and every history row survived.
   Walk through exactly what would have broken, table by table, if
   `product_name` had been the primary key instead of `sku`.
8. `CHECK (id = 1)` made the one-product assumption structural. Was that a
   mistake? Argue both sides in a sentence each, then say which this book's
   own migration discipline favors and why.

## Where to look next

- `src/reference_organizations/store/__init__.py` — `seed_catalog`,
  `CatalogEntry`, `DEFAULT_CATALOG`
- `tests/test_store_multi_sku.py` — the full multi-SKU isolation proof matrix:
  every way one SKU's row could leak into another's, and the proof it cannot

`solution.py` imports the production package rather than copying it.

Next: [Chapter 9 — Each product has its own threshold](../ch09_each_product_has_its_own_threshold/README.md)
