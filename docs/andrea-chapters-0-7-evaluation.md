# Andrea Chapters 0-7 evaluation (post-Unit-9 curriculum)

## Who Andrea is

The same person `docs/andrea-alpha-evaluation.md` describes: a master's
student who knows some Python, has written scripts and notebooks but not
production systems, and wants a path into data science or AI engineering.
Andrea is not a proxy for "a beginner" — Andrea is the specific person this
book is written for, and a change that makes the system more elegant for an
expert while making it opaque for Andrea is a regression.

This document extends, rather than replaces, the historical evaluation. It
does not restate Tasks 1-6 — they are unchanged in substance and are
referenced below, not duplicated. What this document adds is a session that
continues through Chapters 4-7 and closes with a genuine Task 7 assessing
Pulse, replacing the historical document's own Task 7 (which correctly
scored "the organization does not wake itself," true at the time it was
written and still true of Chapters 0-3 alone).

## What this evaluation scores

Identical scoring philosophy to the historical document: **truth and
understanding, not memorization.** Score each task 0-2:

- **2** — did it, and can explain why it matters
- **1** — did it, explanation is shaky or partly wrong
- **0** — could not complete, or the explanation is confidently wrong

A confidently wrong answer scores below a hesitant right one.

## Setup (evaluator, before the session)

Identical to the historical document:

```console
python --version          # expect 3.14.x
uv sync --all-groups
```

Do **not** pre-run any demo or exercise. Andrea should see a cold start for
every chapter.

## Scope of this session

Andrea works through Chapters 0-7 in order. Tasks 1-6 below are the
historical document's own six tasks, referenced by number and briefly
described — an evaluator already familiar with that document can run this
session using its own task text verbatim; what follows here names them only
so this document is readable standalone.

### Tasks 1-6 (see `docs/andrea-alpha-evaluation.md` for full text)

| Task | What it covers | Chapters exercised |
| --- | --- | --- |
| 1 | Enter the environment, `doctor` | Chapter 0 |
| 2 | Reach a truthful accepted outcome, `ACCEPTED` vs. verified true | Chapter 0 |
| 3 | Locate the eight governance/operational artifacts | Chapters 0-2 |
| 4 | Explain four core ideas (actor vs. provider, no self-approval, evidence binding, governance vs. operational data) | Chapters 2-3 |
| 5 | Change a reorder point and predict the verifier's verdict | Chapter 2 |
| 6 | Diagnose a malformed provider report | Chapter 2 |

For a session that also wants coverage of Chapters 4-6 explicitly (not
required for Task 7 below, but recommended for a full post-Unit-9 session),
add:

### Task 3.5: Chapters 4-6, reachability (target: 6 min)

```console
python book/ch04_work_stays_inside_its_boundary/solution.py --root /tmp/andrea-ch04
python book/ch05_authority_needs_a_fence/solution.py --root /tmp/andrea-ch05
python book/ch06_the_organization_recovers/solution.py --root /tmp/andrea-ch06
```

Pass: all three exit 0 and print JSON output. Ask Andrea to point at one
field in each output and say what it proves — this is a reachability check,
not a deep comprehension check; Task 7 below is where comprehension is
actually scored for the chapter that matters most for this document's own
purpose.

## Task 7 (replaces the historical document's Task 7): genuine proactive Pulse (target: 5 min)

The historical Task 7 asked Andrea to explain why the organization is still
passive, and correctly scored 0 if Andrea believed the system was already
autonomous — because Pulse did not exist in the code at the time. That
question is now the wrong one to ask: Pulse is real, and asking Andrea to
explain why the system is passive would coach a wrong answer. This task
replaces it entirely, assessing the opposite: can Andrea explain and
independently verify genuine proactive Pulse behaviour.

### 7a. Run Chapter 7's exercise (target: 1 min)

```console
python book/ch07_the_organization_wakes_itself/solution.py --root /tmp/andrea-ch07
```

Pass: exits 0, prints JSON with `"pulse_work_created_present": true` and
`"origin_kind": "pulse"`.

### 7b. Predict before reading the code (target: 1 min)

Before Andrea opens `solution.py`, ask: *"Chapter 0's demo needed you to run
several commands by hand — create an outcome, plan a SOW, assign it, run it.
This chapter's exercise does none of that by hand. What do you think replaced
those manual steps?"*

Score 2 if Andrea's prediction is in the right shape (something reads a
signal and decides on its own) even if imprecisely worded — this is a
prediction, not a definition.

### 7c. Verify independently, without trusting the script's own summary
(target: 2 min)

```console
sqlite3 /tmp/andrea-ch07/.sovereign/organization.db <<'SQL'
SELECT po.origin_kind, po.sow_id, po.assignment_id,
       wd.source_signal_id, wd.source_event_id
FROM pulse_origins po
LEFT JOIN pulse_wake_decisions wd ON wd.id = po.wake_decision_id
ORDER BY po.created_at;
SQL
```

Pass: Andrea reads exactly one row, `origin_kind = pulse`, and can explain
that this ROW — not the Python script's own printed summary — is what proves
the SOW was Pulse-created. Ask the follow-up: *"If I told you this row could
be faked by directly inserting into the events table, would that convince
you? What would you check instead?"* Looking for: the `pulse_origins` row's
own foreign key to a real `pulse_wake_decisions` row is what makes it
trustworthy, not the presence of a `pulse.*` event kind string alone — a
fabricated event with no matching origin/decision chain is exactly what this
project's own curriculum checker (`scripts/verify_curriculum.py`) refuses,
and Andrea arriving at that same reasoning independently is the strongest
possible pass.

### 7d. Explain the boundary (target: 1 min)

Ask: *"`sovereign-agent pulse --once` ran one pass and stopped. What does
this system NOT yet do, even though it can now create work on its own?"*

Pass: Andrea names that there is no scheduling, no cron, no OS service, no
looping — `--once` is the only shape, and something external (a human, a
future scheduler this unit does not build) has to invoke it. Score 0 if
Andrea believes the organization now runs continuously in the background;
that would mean this document, like the historical Task 7 before it, is
scoring against an oversold claim.

## Scoring

Tasks 1-6 (see the historical document) plus Task 7 above: maximum 14 (seven
tasks × 2), same scale as the historical document. If the evaluator also
runs Task 3.5 (Chapters 4-6 reachability), record it separately — it is not
counted in the 14-point maximum, since it deliberately does not carry the
same depth-of-explanation bar Task 7 does.

- **12-14** — Alpha passes. Andrea can reach and explain genuine proactive
  work, and can independently verify it rather than trusting a script's own
  summary.
- **9-11** — Alpha passes with named gaps. Record which task scored low.
- **≤8** — Alpha fails. The book is not yet teaching what the code does.

Record every wrong answer verbatim, exactly as the historical document
instructs. A wrong answer is a bug report about the writing, not about
Andrea.

## What this document does not authorize

This is an offline task and scoring key, mechanically validated (see below).
It does **not** authorize or perform the Unit 12 Andrea soak — a timed,
human, live session is Unit 12's own territory. No credentialed provider
execution is introduced here: Task 7, like every task in the historical
document, runs entirely offline on the `scripted` provider.

**Terminology correction (2026-08-31):** the phrase "Unit 12 Andrea soak"
directly above is superseded, stale wording — retained here unedited, per
this project's own established discipline of naming a superseded passage
rather than silently rewriting it. Current terminology, per
`docs/rulings/2026-08-31-unit12-scope.md` (Holding 7), is **"Andrea live
evaluation"**: the timed, human, live session
`docs/andrea-chapters-0-12-evaluation.md` defines. "Unit 12 Andrea soak" and
"Andrea-profile soak" no longer describe that session; "v0.6 infrastructure
soak" remains the only current use of unqualified "soak," and refers to the
unrelated historical 72-hour exercise, not to anything Andrea-related.

## Automated pre-check

Before spending a human session, confirm the machine-checkable parts:

```console
python scripts/evaluate_andrea_chapters_0_7.py
```

It runs the cold-start path through Chapter 7 end to end and reports which
tasks are machine-verifiable. It cannot score understanding — Task 4 (from
the historical document) and Tasks 7b/7c/7d above need a human reading the
answers.
