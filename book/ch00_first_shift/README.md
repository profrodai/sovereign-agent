# Chapter 0 — Andrea's first shift

## Learning objective

Run a Zero-Employee Organization through one complete piece of work, and learn
that `ACCEPTED` is a **claim the system proved**, not a status string someone
felt like printing.

It is fine if this chapter feels like magic. Chapters 1 to 3 take the magic
apart. What matters here is that you see the whole shape once.

## The exercise

```bash
sovereign-agent doctor
sovereign-agent demo store --mode simulated --root /tmp/andrea-shift
```

No API keys. No network. No provider subscription. `doctor` will tell you which
provider CLIs you happen to have installed, and the demo does not need any of
them: it uses the `scripted` provider, which is a deterministic fixture.

## What the organization did

```text
a customer buys 2 boxes of tea
  → inventory drops to 2, below the reorder point of 3
  → the organization records a durable signal: "stock is low"
  → the Principal's outcome says: keep the tea jar stocked
  → a Master writes a SOW and assigns it to an Operator actor
  → the Operator's provider PROPOSES restocking 6 boxes
  → deterministic Python VALIDATES the proposal and commits the purchase
  → inventory, cash, and the event all commit together, or not at all
  → a Verifier runs the acceptance checks and records evidence
  → Sparring reviews the work (a different actor than the one who did it)
  → the Principal accepts
```

## Expected observations

You should see:

```text
out_...  ACCEPTED  Keep the tea jar stocked
  sow_...  ACCEPTED  Manually dispatched replenishment after signal sig_...
outcome ACCEPTED
```

Now confirm the organization is telling the truth.

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "SELECT sku, on_hand, reorder_point FROM inventory;"
```

Expected: `SKU-TEA|8|3`. On-hand is **at or above** the reorder point. The tea
jar is genuinely full.

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "SELECT id, amount_cents FROM cash_entries;"
```

Expected: three rows — an opening balance of `10000`, a sale of `+800`, and a
purchase of `-720`. Money left the organization to buy the stock. Six boxes at
120 cents each is exactly 720.

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "SELECT kind FROM events ORDER BY seq;"
```

Expected: a `replenishment.committed` event sitting between
`assignment.finished` and `sow.reviewed`.

## Learner verification command

One command that checks all of it at once:

```bash
python scripts/verify_store_outcome.py /tmp/andrea-shift
```

It exits 0 only if the accepted outcome is actually true. Try breaking it:

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA';"
python scripts/verify_store_outcome.py /tmp/andrea-shift
```

Now it fails, and says why. The status field still reads `ACCEPTED`, because
that is a historical record of a decision — but the verifier checks the *world*,
and the world no longer matches. That gap is the whole subject of this book.

## Why this is not a toy

An earlier version of this exact demo printed `ACCEPTED` while the tea jar sat
at 2 boxes against a reorder point of 3. Every governance record existed —
outcome, SOW, assignment, review, acceptance — and the shelf was still empty.
The paperwork was perfect and the claim was false.

That is the failure this book is about. An organization that cannot tell you
the difference between "we did the work" and "we filed the forms" will
confidently tell you the forms are the work.

## Why nothing happened until you typed

Worth noticing before you move on: **you** started this. The sale, the signal,
the statement of work, the restock — none of it began until you ran a command.

The organization has no heartbeat yet. It cannot notice that stock fell, or
decide on its own that the tea needs reordering. Every step you just watched was
dispatched because the demo dispatched it.

That capacity — the organization waking itself and creating work with nobody
prompting it — is called **Pulse**. This exercise does not run it: the demo
above dispatches every step by hand, and no event in the ledger you just
inspected pretends otherwise. You can check that claim the same way you
checked the others:

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "SELECT DISTINCT kind FROM events ORDER BY kind;"
```

Every `kind` describes something a human or a governed actor did. There is no
`pulse.*` anywhere in THIS run, because this exercise never calls Pulse.

**Added, Unit 9:** Pulse is now real, as a separate mechanism you invoke
yourself with `sovereign-agent pulse --once --root PATH` — it is not this
chapter's exercise, and it never runs itself. See
`docs/v1-unit9-pulse-proactive-work.md` for the sale-to-proactive-work slice
this chapter's own dispatched-by-hand version is contrasted against.

Knowing what a system cannot yet do is part of knowing what it does.

## Explain it back

Answer these in your own words before moving on. If you cannot, re-read the
observations above — the answers are all visible in the database.

1. The demo printed `ACCEPTED`. What would you check, and in what order, to
   decide for yourself whether that word is earned?
2. The provider asked for 6 boxes. Where did the *price* of those boxes come
   from — the provider, or somewhere else? Why does that distinction matter?
3. `sparring-course` reviewed the work and `principal-human` accepted it. Why
   not let `operator-course`, who did the work, do either of those?
4. Which of these is a fact about the world, and which is a fact about the
   process: "inventory is at 8" versus "the SOW is in state ACCEPTED"?
5. Nothing happened until you typed a command. What would have to exist for the
   organization to start this work on its own, and why is it honest that the
   ledger contains no `pulse.*` event today?

## Where to look next

- `governance/outcomes/*/outcome.json` — the outcome, projected for reading
- `governance/outcomes/*/README.md` — the same thing, generated for humans
- `.sovereign/organization.db` — the authority for everything operational
- `.sovereign/runs/*/.sovereign-out/report.json` — what the provider proposed
- `.sovereign/runs/*/receipt.json` — what the organization recorded about the run

`solution.py` imports the production demo rather than copying it.

Next: [Chapter 1 — The organization remembers](../ch01_organization_remembers/README.md)
