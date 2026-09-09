# Chapter 9 lab: make a sale one indivisible fact

## Challenge

Implement a sale whose stock read, inventory decrement, cash movement, and
event append happen in one immediate transaction. This lab strengthens the
boundary by reading price from the catalog rather than accepting it from the
caller. Availability is `on_hand - reserved`, not `on_hand`.

The exercise must also inject a failure after the cash insert and race two
independent SQLite connections that each want more than half the remaining
stock. The database should commit one complete sale and refuse the other.

## Production map

- `reference_organizations.store.record_sale` reads stock under
  `BEGIN IMMEDIATE`, rejects negative inventory, computes cash as quantity
  times the supplied unit price, and commits the signal/event beside the state
  changes. Compare that production boundary with this lab's catalog lookup.
- `checks.inventory_at_or_above_reorder_point` reasons over available stock,
  `on_hand - reserved`.
- Store tests cover multiple SKU isolation and genuine two-connection
  oversell contention.

## Run it

```bash
cp book/labs/ch09_each_product_has_its_own_threshold/starter.py \
  book/labs/ch09_each_product_has_its_own_threshold/work.py
python book/labs/ch09_each_product_has_its_own_threshold/check.py \
  book/labs/ch09_each_product_has_its_own_threshold/work.py /tmp/sa-ch09-lab
```

Fill the numbered TODO seams in `work.py`. The passing output is
timing-independent: it records one winner and one refusal, not which thread
happened to acquire the lock first. Consult `solution.py` after your attempt.

## Break it

Try each mutation and inspect all four ledgers afterward:

1. Read `on_hand` before opening the immediate transaction.
2. Ignore `reserved` when computing availability.
3. Accept `unit_price_cents` from the caller instead of reading the product.
4. Commit inventory before inserting cash and the event.
5. Catch an exception after the cash insert but forget to roll back.

For each break, ask whether the database now tells one coherent story or
several incompatible stories.

## Explain it back

Why is `quantity * catalog price` part of the invariant rather than a display
calculation? Why does reservation reduce sellable stock without reducing
on-hand stock? What property does `BEGIN IMMEDIATE` add that a Python lock does
not provide to another process?
