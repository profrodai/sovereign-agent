# Quickstart

Ten minutes, no API keys, no network. You will run a small organization through
one complete piece of work and then check whether it told you the truth.

You need Python **3.14 or newer** and a terminal.

## 1. Install

=== "macOS and Linux"

    ```bash
    python3.14 -m venv .venv
    source .venv/bin/activate
    pip install sovereign-agent
    ```

=== "Windows"

    ```powershell
    py -3.14 -m venv .venv
    .venv\Scripts\activate
    pip install sovereign-agent
    ```

Check the install:

```bash
sovereign-agent --version
sovereign-agent doctor
```

`doctor` reports your Python and Pydantic versions and lists which provider CLIs
you happen to have. **You do not need any of them.** The quickstart runs on the
`scripted` provider, which is a deterministic fixture.

## 2. Run one shift

```bash
sovereign-agent demo store --mode simulated --root /tmp/andrea-shift
```

Expected, ending with:

```text
outcome ACCEPTED
```

A customer bought tea, stock fell below the reorder point, the organization
raised a signal, wrote a statement of work, assigned it to an operator actor
whose provider proposed a restock, validated that proposal in ordinary Python,
committed the purchase, verified the result, had it reviewed by a different
actor, and accepted it.

## 3. Check whether it is telling the truth

This is the part that matters. `ACCEPTED` is a claim; here is how you audit it.

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "SELECT sku, on_hand, reorder_point FROM inventory;"
```

Expected `SKU-TEA|8|3` — on-hand is at or above the reorder point, so the tea jar
really is full.

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "SELECT id, amount_cents FROM cash_entries;"
```

Expected three rows: `10000` opening, `+800` for the sale, `-720` for the
purchase. Six boxes at 120 cents is exactly 720.

## 4. Break it on purpose

```bash
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "UPDATE inventory SET on_hand = 0 WHERE sku = 'SKU-TEA';"

sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "SELECT json_extract(record,'$.state') FROM outcomes;"
```

The stored state still reads `ACCEPTED`, because that records a decision that was
made. But the shelf is empty.

If you cloned the repository rather than installing from PyPI, the release gate
that catches exactly this is one command:

```bash
python scripts/verify_store_outcome.py /tmp/andrea-shift
```

It exits non-zero and names every claim that no longer holds.

An earlier version of this very demo printed `ACCEPTED` while the jar held two
boxes against a reorder point of three. Every governance record existed and the
shelf was still empty. That gap is what the book is about.

## Where next

- [The book](book/index.md) — Chapter 0 is this shift, explained.
- [Persistence boundary](persistence-boundary.md) — what is canonical, what is
  derived, and what this design does *not* promise.

## What this version does not do

The organization does not wake itself up. You ran a command and work happened.
Proactive waking is called Pulse and it does not exist yet; nothing here
simulates it.
