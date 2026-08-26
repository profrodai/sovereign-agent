# Quickstart

Ten minutes and no API keys. You will run a small organization through
one complete piece of work and then check whether it told you the truth.

You need Python **3.14 or newer**, `git`, and a terminal. Nothing else — no
API key, no network after installation, and no database tools.

## 1. Install

!!! warning "Install from the repository, not from PyPI"

    PyPI still serves the **0.x** framework, which is a different product with a
    different API and a lower Python floor. Publishing 1.x is deferred to
    Unit 12. Until then, `pip install sovereign-agent` would give you the old
    package while this page teaches the new one.

=== "macOS and Linux"

    ```bash
    git clone https://github.com/zeroemployeeorg/sovereign-agent.git
    cd sovereign-agent
    python3.14 -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

=== "Windows"

    ```powershell
    git clone https://github.com/zeroemployeeorg/sovereign-agent.git
    cd sovereign-agent
    py -3.14 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -e .
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

!!! note "Windows"

    Use a path that exists on your machine, for example
    `--root C:\Users\you\andrea-shift`, and substitute it below.

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
sovereign-agent inspect --root /tmp/andrea-shift
```

Expected, in three parts:

```text
inventory
  OK  SKU-TEA: on_hand=8 reserved=0 reorder_point=3
cash
     10000  cash-opening
       800  cash_...
      -720  cash_...
     10080  = balance
events
    ...
    1  replenishment.committed
    ...
```

Read it as three separate claims:

- **`OK`** — available stock is at or above the reorder point. The tea jar
  really is full. `LOW` would mean it is not, whatever the outcome says.
- **`-720`** — money actually left the organization to buy stock. Six boxes at
  120 cents is exactly 720, and the balance still adds up.
- **`replenishment.committed`** — a restock is on the append-only ledger, not
  merely implied by the inventory number.

## 4. Break it on purpose

Change the world behind the organization's back:

```bash
python scripts/empty_the_shelf.py /tmp/andrea-shift
sovereign-agent inspect --root /tmp/andrea-shift
```

Inventory now reads `LOW`, and the outcome still reads `ACCEPTED` — because that
records a decision that was made, while the shelf is empty.

If you want the machine-checked version of that judgement, the repository ships
the release gate that catches exactly this:

```bash
python scripts/verify_store_outcome.py /tmp/andrea-shift
```

It exits non-zero and names every claim that no longer holds.

An earlier version of this very demo printed `ACCEPTED` while the jar held two
boxes against a reorder point of three. Every governance record existed and the
shelf was still empty. That gap is what the book is about.

## Where next

- [The book](../book/README.md) — Chapter 0 is this shift, explained.
- [Persistence boundary](persistence-boundary.md) — what is canonical, what is
  derived, and what this design does *not* promise.

## What this version does not do

The organization does not wake itself up. You ran a command and work happened.
Proactive waking is called Pulse and it does not exist yet; nothing here
simulates it.
