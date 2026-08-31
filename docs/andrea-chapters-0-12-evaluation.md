# Andrea Chapters 0-12 evaluation (Unit 12 Andrea live evaluation protocol)

## Who Andrea is

The same person `docs/andrea-alpha-evaluation.md` describes: a master's
student who knows some Python, has written scripts and notebooks but not
production systems, and wants a path into data science or AI engineering.
Andrea is not a proxy for "a beginner" — Andrea is the specific person this
book is written for, and a change that makes the system more elegant for an
expert while making it opaque for Andrea is a regression.

This document extends `docs/andrea-chapters-0-7-evaluation.md` to the full
13-chapter curriculum. It does not rewrite either historical evaluation
(`docs/andrea-alpha-evaluation.md`, `docs/andrea-chapters-0-7-evaluation.md`)
— both remain intact historical records of their own prior sessions. Tasks
1-7 are retained verbatim, referenced by number, not restated in full here;
this document adds Tasks 8, 9, and 10, extending the curriculum through
Chapters 8-12 (the Store's multi-SKU expansion and the pilot-start
mechanism).

**Terminology**, per the governing ruling's Holding 7: this document uses
only **"Andrea live evaluation"** throughout. It never uses unqualified
"soak." "v0.6 infrastructure soak" would refer only to the unrelated
historical 72-hour exercise, which this document does not concern.

## What this evaluation scores

Identical scoring philosophy to both historical documents: **truth and
understanding, not memorization.** Score each task 0-2:

- **2** — did it, and can explain why it matters
- **1** — did it, explanation is shaky or partly wrong
- **0** — could not complete, or the explanation is confidently wrong

A confidently wrong answer scores below a hesitant right one.

## Participant

At least one real Andrea-profile learner — comfortable with Python scripts
and notebooks, unfamiliar with this implementation, and **not an author or
reviewer of it.** A participant who helped write or review Sovereign Agent's
own code or curriculum cannot run this session; their familiarity with the
implementation would make the session measure recall, not the book's own
teaching.

## Environment

Fresh laptop or notebook-style environment, Python 3.14, cold checkout and
install, no pre-run exercises, no credentialed provider required. The entire
session runs on the offline `scripted` provider; nothing here needs a Claude,
Codex, or Cursor credential.

```console
python --version          # expect 3.14.x
uv sync --all-groups
```

Do **not** pre-run any demo or exercise. Andrea should see a cold start for
every chapter, exactly as the historical documents required.

## Duration

60-minute ceiling for the complete session. The first truthful accepted
outcome (Task 2, Chapter 0's `demo store`) must still occur within 10
minutes — this matches the top-level design memo's own existing `done_when`
clause and is unchanged by this document.

## Sampling and repetition

One fresh participant and one complete cold-start session are sufficient for
1.0. If a blocking defect surfaces during the session and requires a code or
curriculum change, acceptance requires a **new** cold-start session run
against the corrected exact head — the prior session's evidence is
preserved, not overwritten, so a reader can see what the defect was and how
it was fixed.

## Scope of this session

Andrea works through Chapters 0-12 in order.

### Tasks 1-7 (see `docs/andrea-chapters-0-7-evaluation.md` for full text)

| Task | What it covers | Chapters exercised |
| --- | --- | --- |
| 1 | Enter the environment, `doctor` | Chapter 0 |
| 2 | Reach a truthful accepted outcome, `ACCEPTED` vs. verified true | Chapter 0 |
| 3 | Locate the eight governance/operational artifacts | Chapters 0-2 |
| 4 | Explain four core ideas (actor vs. provider, no self-approval, evidence binding, governance vs. operational data) | Chapters 2-3 |
| 5 | Change a reorder point and predict the verifier's verdict | Chapter 2 |
| 6 | Diagnose a malformed provider report | Chapter 2 |
| 7 | Genuine proactive Pulse: run, predict, independently verify, explain the boundary (7a-7d) | Chapter 7 |

Retained verbatim from the historical document, maximum 14 across these
seven two-point tasks, confirmed at this document's own base commit
(`grep -n "maximum 14" docs/andrea-chapters-0-7-evaluation.md`). An
evaluator already familiar with that document can run Tasks 1-7 using its
own task text; what follows here names them only so this document is
readable standalone. Task 3.5 (Chapters 4-6 reachability) is optional and,
as in the historical document, not counted toward the scored maximum.

## Task 8: multi-SKU isolation (target: 5 min)

### 8a. Run Chapter 8's exercise (target: 1 min)

```console
python book/ch08_the_store_becomes_a_catalog/solution.py --root /tmp/andrea-ch08
```

Pass: exits 0, prints JSON with `"at_least_two": true` under
`catalog_size` and `"not_all_the_same": true` under
`independent_reorder_points` — at least two distinct SKUs, each with its own
reorder point.

### 8b. Verify independently (target: 2 min)

```console
sqlite3 /tmp/andrea-ch08/.sovereign/organization.db <<'SQL'
SELECT sku, on_hand, reserved, reorder_point FROM inventory ORDER BY sku;
SQL
```

Pass: Andrea reads at least two rows, each with its own `sku`, and can point
at the fact that `reorder_point` differs between them as proof the two
products are tracked independently — not sharing one row, one counter, or
one threshold.

### 8c. Explain isolation (target: 2 min)

Ask: *"If I recorded a sale of SKU-COFFEE right now, what in this table
would change, and what would definitely NOT change?"*

Pass (score 2): Andrea correctly predicts that only `SKU-COFFEE`'s own
`on_hand` (and its own cash entry) changes, and that `SKU-TEA`'s row is
untouched — and can say why: `record_sale`, the wake gate, and replenishment
are all keyed by `sku`, so one product's state living in its own row is what
makes that isolation possible, not a coincidence of the demo data chosen.
Score 0 if Andrea believes selling one product could affect another's
recorded stock.

## Task 9: pilot-start structured evidence, replay, and refusal (target: 6 min)

### 9a. Run Chapter 12's exercise (target: 1 min)

```console
python book/ch12_the_pilot_begins_with_a_receipt/solution.py --root /tmp/andrea-ch12
```

Pass: exits 0, prints JSON with `"idempotent_replay": true` under `replay`
and `"exactly_one_despite_the_replay_above": true` under `durable_event`.

### 9b. Verify the durable record independently (target: 2 min)

```console
sqlite3 /tmp/andrea-ch12/.sovereign/organization.db <<'SQL'
SELECT pilot_id, started_at, store_org_id FROM pilots;
SELECT COUNT(*) AS pilot_started_events FROM events WHERE kind = 'pilot.started';
SQL
```

Pass: Andrea reads exactly one `pilots` row and exactly one `pilot.started`
event, despite the exercise having called `start_pilot` twice with the same
identity — the replay did not create a second row or a second event.

### 9c. Predict a refusal, then explain it (target: 2 min)

Ask: *"The exercise's own pilot is now active. If I tried to start a
DIFFERENT pilot right now, what do you think would happen?"* Then show:

```console
python -c "
from pathlib import Path
from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from reference_organizations.store.pilot import start_pilot

db = Database(Path('/tmp/andrea-ch12/.sovereign/organization.db'))
try:
    start_pilot(db, pilot_id='a-different-pilot', store_org_id='different-org',
                pilot_profile_id='different-profile', evidence_namespace='different-ns')
    print('NOT REFUSED')
except Refusal as r:
    print('REFUSED:', r.category)
"
```

Pass: Andrea predicts a refusal (score 2 if the prediction names "only one
pilot can be active" even loosely worded), the command prints
`REFUSED: pilot_already_active`, and Andrea can explain that the refusal
rolled back the whole attempt — no half-written row was left behind.

### 9d. Explain what makes the replay trustworthy (target: 1 min)

Ask: *"If someone directly inserted a `pilot.started` event into the events
table by hand, without calling `start_pilot`, would there be a matching row
in the `pilots` table?"*

Pass: Andrea says no — a fabricated event has no matching `pilots` row,
because the two are written together in one atomic transaction only inside
`start_pilot` itself; a hand-inserted event bypasses that transaction
entirely, the same "fabrication leaves no traceable chain" property Chapter
7's own Task 7c already taught for Pulse.

## Task 10: local mechanism vs. real deployment, and ZEO Go (target: 3 min)

This task is a comprehension question; nothing about it is machine-checkable
— it deliberately has no companion command block. Ask directly:

*"You just started a 'pilot' against a database on this laptop. Has a real
30-day Sovereign Store pilot begun somewhere? If not, what would actually
have to be true for a real pilot to exist, and what project would that
belong to?"*

Pass (score 2): Andrea correctly says no real pilot has begun — this ran
against a disposable, exercise-scoped identity on a local, throwaway
database, not a deployed system with a real 30-day clock, a real
organization, or a governance receipt. Andrea identifies that a genuine
production deployment is a separate, later, operational undertaking —
**ZEO Go** — not something this executable textbook builds or claims. Score
1 if Andrea correctly says "no real pilot" but cannot name what a real one
would require or where it belongs. Score 0 if Andrea believes running this
chapter's exercise constitutes, or is equivalent to, a real deployment
pilot — that would be exactly the "local mechanism mistaken for a real
deployment" claim this task exists to catch, and the mistake this project's
own governing ruling
(`docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md`)
was written to prevent from ever being taught as true.

## Scoring

Tasks 1-7 (maximum 14) plus Tasks 8, 9, 10 (three tasks × 2 = 6): **new
maximum 20.**

- **17-20** — Passes. Andrea can reach and explain genuine multi-SKU
  isolation, the pilot-start mechanism's structured evidence and refusal
  behavior, and correctly distinguishes the local exercise from a real
  deployment.
- **12-16** — Passes with named gaps. Record which task scored low.
- **≤11** — Fails. The book is not yet teaching what the code does.

**Zero-tolerance tasks**: a **0 on Task 2, 7, 8, 9, or 10 fails the session
outright, regardless of total score** — these are the truth-critical tasks
where a confidently wrong answer is worse than a low total (believing a
false `ACCEPTED`, believing the organization already runs unattended,
believing one SKU's state can leak into another's, believing a fabricated
event is trustworthy, or believing a local exercise is a real deployment).

**Pass criteria, restated exactly**: total score at least 17/20, no zero on
Tasks 2, 7, 8, 9, or 10, first accepted outcome within 10 minutes, complete
session within 60 minutes. All four conditions must hold; none substitutes
for another.

Record every wrong answer verbatim, exactly as both historical documents
instruct. A wrong answer is a bug report about the writing, not about
Andrea.

## What this document does not authorize

This is a protocol, task definition, and scoring key, with a
machine-checkable pre-check for Tasks 8-9's own reachability/evidence
portions (see below). It does **not** run the Andrea live evaluation itself
— that is a real human session, a separate, later, separately-authorized
Principal (or Operator, for participant selection) act, not implied by this
document's own existence or by Unit 12's implementation acceptance. No
credentialed provider execution is introduced here: every task in this
document, like every task in both historical documents, runs entirely
offline on the `scripted` provider.

## Automated pre-check

Before spending a human session, confirm the machine-checkable parts of
Tasks 8-9 (Task 10 is a comprehension question no script can score):

```console
python scripts/evaluate_andrea_chapters_0_7.py
python scripts/evaluate_andrea_chapters_0_12.py
```

The first command covers Tasks 1-7's own machine-checkable portions
(unchanged, reused as-is). The second, new for this document, runs Chapter
8's and Chapter 12's own exercises and independently re-verifies, via a
fresh sqlite3 connection, that the catalog is genuinely isolated and that a
different pilot_id is genuinely refused while one is active — it does not
trust either exercise's own printed summary. Neither script scores
understanding; both report honestly which tasks they can and cannot
themselves evaluate.
