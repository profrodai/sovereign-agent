# Quickstart

Ten minutes and no API keys. You will run a small organization through
one complete piece of work and then check whether it told you the truth.

You need [`uv`](https://docs.astral.sh/uv/), `git`, and a terminal. Nothing
else — uv supplies Python 3.14 itself, and after installation there is no
API key, no network, and no database tools.

## 1. Install

Clone the repository (the book, labs, and audit scripts live there — the
same walkthrough below uses them) and let uv build the environment:

```bash
git clone https://github.com/profrodai/sovereign-agent.git
cd sovereign-agent
uv sync
```

The same three commands work on macOS, Linux, and Windows.

!!! note "Just the CLI?"

    If you only want the installed organization without the repository,
    `uvx sovereign-agent@latest doctor` runs the current PyPI release
    directly. This page assumes the clone, because the audit scripts in
    step 4 ship in the repository, not the wheel.

Check the install:

```bash
uv run sovereign-agent --version
uv run sovereign-agent doctor
```

`doctor` reports your Python and Pydantic versions, probes the Claude, Codex, and
Cursor CLIs, and shows the configured OpenAI-compatible provider without making
a network request. **You do not need any of them.** The quickstart runs on the
`scripted` provider, which is a deterministic fixture.

## 2. Run one shift

```bash
uv run sovereign-agent demo store --mode simulated --root /tmp/andrea-shift
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
uv run sovereign-agent inspect --root /tmp/andrea-shift
```

Expected, in four parts:

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
outcomes
  ACCEPTED out_...  Keep the tea jar stocked
```

Read it as four separate claims:

- **`OK`** — available stock is at or above the reorder point. The tea jar
  really is full. `LOW` would mean it is not, whatever the outcome says.
- **`-720`** — money actually left the organization to buy stock. Six boxes at
  120 cents is exactly 720, and the balance still adds up.
- **`replenishment.committed`** — a restock is on the append-only ledger, not
  merely implied by the inventory number.
- **`ACCEPTED`** — the governed outcome reached its terminal state after its
  checks, evidence, and review; it does not replace the three world-state
  observations above.

## 4. Break it on purpose

Change the world behind the organization's back:

```bash
uv run python scripts/empty_the_shelf.py /tmp/andrea-shift
uv run sovereign-agent inspect --root /tmp/andrea-shift
```

Inventory now reads `LOW`, and the outcome still reads `ACCEPTED` — because that
records a decision that was made, while the shelf is empty.

If you want the machine-checked version of that judgement, the repository ships
the release gate that catches exactly this:

```bash
uv run python scripts/verify_store_outcome.py /tmp/andrea-shift
```

It exits non-zero and names every claim that no longer holds.

An earlier version of this very demo printed `ACCEPTED` while the jar held two
boxes against a reorder point of three. Every governance record existed and the
shelf was still empty. That gap is what the book is about.

## Where next

- [The book](../book/README.md) — Chapter 0 is this shift, explained.
- [Persistence boundary](persistence-boundary.md) — what is canonical, what is
  derived, and what this design does *not* promise.

## What this walkthrough does not do

This walkthrough uses the manual dispatch path: you ran a command and work
happened. The installed package also contains Pulse, which can turn a durable
business signal into governed work during one explicit pass, but this example
does not invoke it and its ledger contains no `pulse.*` event. Pulse is distinct
from both scheduling and the heartbeat liveness record. Continue to Chapter 7
and [the Pulse reference](v1-unit9-pulse-proactive-work.md) for that mechanism.

## Liveness, separately: the `heartbeat` command

Heartbeat is unrelated to everything above — it is not Pulse, it is not the
supervisor, and it never creates work. It answers exactly one question: "was
this organization's runtime alive recently?"

```bash
# Record one liveness beat (default source "cli"):
uv run sovereign-agent heartbeat --root /tmp/andrea-shift
# -> beat recorded: <beat-id>

# From a different watcher/source:
uv run sovereign-agent heartbeat --root /tmp/andrea-shift --source watchdog

# Read the verdict on the newest beat:
uv run sovereign-agent heartbeat --status --root /tmp/andrea-shift
# -> ALIVE: last beat <id> from 'watchdog' at <timestamp>, <N>s ago (threshold 900s)
```

`--status` prints one of three honest verdicts and exits accordingly:

- `ALIVE` — the newest beat is within the staleness window (`--stale-after`
  seconds, default `900`). Exit code `0`.
- `STALE` — no beat was recorded within the window. This proves silence, not
  death: the recorder may be wedged, crashed, or merely cut off from the
  database. Exit code `1`.
- `NO_BEATS` — the `heartbeats` table is empty; nothing has ever recorded a
  beat here. Exit code `1`.

Because `--status` exits `0` only on `ALIVE`, a cron job or external watchdog
can key off the exit code directly, without parsing output.

Beats live in their own append-only `heartbeats` table, entirely separate from
the `events` ledger that records governed work — so a live process can never
be mistaken for progress having been made. See
[`heartbeat.py`](../src/sovereign_agent/heartbeat.py) for the full contract.
