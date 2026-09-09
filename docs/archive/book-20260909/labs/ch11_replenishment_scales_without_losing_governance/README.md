# Chapter 11 lab: scale the effect, keep the authority

## Challenge

Implement a restock operation that survives two callers racing on the same
request. Exactly one caller changes inventory and cash; the other observes an
idempotent replay. A reused key with different content is a conflict, not a
replay. An unauthorized assignment must fail even when its effect key is new.
Inventory, cash, and the durable effect must commit or roll back together.

## Production map

Compare your transaction with `apply_restock`, the database transaction
wrapper, and the causal contribution checks in `Organization.accept`. Follow
the exact tests in `lab.json`. The teaching model is intentionally smaller,
but retains the production distinctions between authority, identity,
idempotency, and atomicity.

## Run it

```bash
python book/labs/ch11_replenishment_scales_without_losing_governance/check.py \
  book/labs/ch11_replenishment_scales_without_losing_governance/solution.py \
  /tmp/sa-ch11-lab
```

The checker uses two threads with separate SQLite connections; it does not
simulate concurrency by calling the function twice in sequence.

Copy the scaffold and check your implementation directly:

```bash
cp book/labs/ch11_replenishment_scales_without_losing_governance/starter.py \
  book/labs/ch11_replenishment_scales_without_losing_governance/work.py
python book/labs/ch11_replenishment_scales_without_losing_governance/check.py \
  book/labs/ch11_replenishment_scales_without_losing_governance/work.py \
  /tmp/sa-ch11-work
```

## Break it

Move the effect lookup outside `BEGIN IMMEDIATE`, or replace the primary key
with a read-then-write boolean. Run the race repeatedly. Next, catch the
injected fault and commit anyway: inventory will diverge from cash and the
effect ledger. Finally, skip the payload comparison on replay and observe how
one key can silently change meaning.

## Explain it back

Why are “authorized,” “idempotent,” and “atomic” three independent claims?
Explain what the unique effect key proves, what it cannot prove, why exact
request identity matters, and which transaction boundary prevents partial
world changes after a crash.
