# Andrea Alpha evaluation (Units 0–6.5)

## Who Andrea is

A master's student. Knows some Python. Has written scripts and notebooks, not
production systems. Wants a path into data science or AI engineering. Has not
run a service, debugged a transaction, or argued about governance.

Andrea is not a proxy for "a beginner". Andrea is the specific person this book
is written for, and a change that makes the system more elegant for an expert
while making it opaque for Andrea is a regression.

## What this evaluation scores

**Truth and understanding — not memorization.** A session that can recite
"evidence must be bound to an outcome" but cannot say *what breaks without it*
has failed. A session that says "I think it's so you can't reuse a check from a
different job" in imperfect words has passed.

Score each task 0–2:

- **2** — did it, and can explain why it matters
- **1** — did it, explanation is shaky or partly wrong
- **0** — could not complete, or the explanation is confidently wrong

A confidently wrong answer scores below a hesitant right one. This book is about
not believing your own paperwork.

## Setup (evaluator, before the session)

Use a machine with Python 3.14 and no Sovereign Agent state:

```console
python --version          # expect 3.14.x
uv sync --all-groups
```

Do **not** pre-run the demo. Andrea should see a cold start.

## Timing

The commands themselves take about **1.3 seconds** of machine time end to end.
The ten-minute budget is entirely Andrea's reading, typing, and thinking time.
If Andrea exceeds ten minutes to a truthful accepted outcome, the blocker is the
writing, not the software — record where the time went.

## The tasks

### 1. Enter the environment (target: 2 min)

```console
uv sync --all-groups
sovereign-agent doctor
```

Pass: `doctor` reports Python and Pydantic OK, and lists which providers are
installed. Andrea should notice that **no provider is required**.

### 2. Reach a truthful accepted outcome (target: 3 min)

```console
sovereign-agent demo store --mode simulated --root /tmp/andrea-shift
python scripts/verify_store_outcome.py /tmp/andrea-shift
```

Pass: `outcome ACCEPTED`, then `ACCEPTED and true: ...`.

Ask: *"The demo said ACCEPTED. The second command said it was true. Why are
those two different questions?"*

Score 2 if Andrea says something like: the first is what the system recorded,
the second checks the world.

### 3. Locate the eight artifacts (target: 3 min)

Andrea must find and say what each one is:

| Artifact | Where |
| --- | --- |
| outcome | `governance/outcomes/*/outcome.json`, or the `outcomes` table |
| SOW | `governance/outcomes/*/sows/*.json`, or the `sows` table |
| assignment | `assignments` table |
| receipt | `.sovereign/runs/*/receipt.json` |
| evidence | `evidence` table |
| inventory | `inventory` table |
| cash entry | `cash_entries` table |
| event history | `events` table |

Score 2 only if Andrea can say **what each is for**, not just where it lives.

### 4. Explain the four ideas (target: 4 min)

Ask each. Record the answer verbatim; do not coach.

1. *Why is an actor not a provider?*
   Looking for: the actor is the accountable identity; the provider is
   swappable intelligence. Rebinding the provider changes who does the thinking,
   not who is answerable.

2. *Why can the operator not approve its own work?*
   Looking for: an actor that checks itself provides no independent evidence.
   Bonus: `accept()` derives the performer from the ledger, so a caller cannot
   nominate a convenient stranger.

3. *Why is evidence more than a filename or an ID?*
   Looking for: it must say which check, about which outcome, during which
   execution, with what result, over what state. Bonus: an earlier version
   accepted a made-up ID.

4. *Which data is governance and which is operational?*
   Looking for: `sovereign.toml` and rulings are committed governance and are
   read back; inventory, cash, events, and execution state live in SQLite;
   Markdown is generated and never authoritative.

### 5. Change a reorder point and predict (target: 2 min)

Before running anything, Andrea predicts what will happen:

```console
sqlite3 /tmp/andrea-shift/.sovereign/organization.db \
  "UPDATE inventory SET reorder_point = 99 WHERE sku = 'SKU-TEA';"
python scripts/verify_store_outcome.py /tmp/andrea-shift
```

Pass: Andrea predicts the verifier will now fail, and can say why — the world
did not change, but the *standard* did, and the claim is judged against the
standard as it is now.

Score 2 if the prediction was made **before** running the command and was right.

### 6. Diagnose a malformed provider report (target: 3 min)

```console
python -c "
import pathlib, tempfile
from reference_organizations.store.demo import propose_restock_from_report
from sovereign_agent.errors import Refusal
bad = pathlib.Path(tempfile.mkdtemp())/'report.json'
bad.write_text('{not json')
try:
    propose_restock_from_report(bad, 'SKU-TEA')
except Refusal as r:
    print(r)
"
```

Pass: Andrea reads the refusal and explains that a malformed report becomes a
failure, never a guessed success. Ask the follow-up: *"What would be the
dangerous alternative?"* Looking for: assuming the provider meant something
reasonable and proceeding.

### 7. Explain why the organization is still passive (target: 1 min)

Ask: *"You ran a command and work happened. What has to be true for this to run
without you?"*

Pass: Andrea says the organization does not wake itself — something must call
it. Proactive waking is Pulse, and Pulse does not exist yet (Unit 9). Score 0 if
Andrea believes the system is already autonomous; that would mean the book
oversold it.

**Added, Unit 9:** this evaluation's own title scopes it to Units 0-6.5 — a
session run against that curriculum state correctly used the pass criterion
above, because Pulse genuinely did not exist yet at the time this document
was written. Pulse is now real production code (`sovereign-agent pulse
--once`; see `docs/v1-unit9-pulse-proactive-work.md`), but no chapter Andrea
would have worked through under this evaluation's own Units 0-6.5 scope
exercises it — that editorial work is Unit 10's, not silently folded in
here. A future evaluation covering post-Unit-9 curriculum will need its own
task 7 and its own scoring key, since "the system does not wake itself" is
no longer true of the underlying code, only of what Chapters 0-3 currently
teach; this document is left as the historical record of what a correct
Units 0-6.5 session looked like, not silently rewritten to score a
curriculum state it never evaluated.

**Added, Unit 10:** that future evaluation now exists —
[`docs/andrea-chapters-0-7-evaluation.md`](andrea-chapters-0-7-evaluation.md).
It carries its own complete, replacement Task 7 and its own complete scoring
instructions, assessing whether Andrea can explain and verify genuine
proactive Pulse behaviour after completing Chapter 7. This document is not
edited beyond this note and remains the correct evaluation for a session run
against the Units 0-6.5 curriculum state exactly as it stood when this
document was written.

## Scoring

Maximum 14 (seven tasks × 2).

- **12–14** — Alpha passes. Andrea can reach and explain a truthful outcome.
- **9–11** — Alpha passes with named gaps. Record which task scored low; that
  chapter needs work.
- **≤8** — Alpha fails. The book is not yet teaching what the code does.

Record every wrong answer verbatim. A wrong answer is a bug report about the
writing, not about Andrea.

## Automated pre-check

Before spending a human session, confirm the machine-checkable parts:

```console
python scripts/evaluate_andrea_alpha.py
```

It runs the cold-start path end to end and reports which tasks are
machine-verifiable. It cannot score understanding — tasks 4 and 7 need a human
reading the answers.
