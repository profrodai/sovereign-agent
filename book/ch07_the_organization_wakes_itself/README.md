# Chapter 7 — The organization wakes itself

## Learning objective

Watch the organization create governed work **without a human prompt**, and
learn what makes that claim honest rather than theater: a durable
`pulse.work_created` event and a structured origin row, both produced by the
real mechanism, both checkable after the fact — never a status string, never
an inference from "nobody typed a command."

Chapter 0 ended by telling you the truth: "you started this... the
organization has no heartbeat yet." That was accurate when it was written.
This chapter is where that stops being true — and it is truthful about the
difference, because the ledger this exercise produces proves it rather than
merely claiming it.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Signal** | A durable, append-only "something needs attention" fact — e.g. inventory falling below the reorder point after a sale. |
| **Wake gate** | A deterministic callback that decides whether a signal fires, and what governed work it should create if it does. The Store's own gate lives outside `sovereign_agent`'s budget: it is domain logic about SKUs and reorder points, not a general Pulse mechanism. |
| **Wake decision** | The durable, `UNIQUE(source_signal_id)` claim that one signal fired — the SQLite-boundary enforcement of "exactly one canonical decision per signal," not a preflight check a race can slip past. |
| **Pulse origin** | The structured, queryable answer to "manual or Pulse, and from what?" — every SOW, manual or Pulse-created, has exactly one row. Absence of a row is never the definition of manual. |

## The exercise

```bash
python book/ch07_the_organization_wakes_itself/solution.py --root /tmp/andrea-ch07
```

Read the file before you run it. Notice what is missing: no `create_sow`, no
`ready_sow`, no `assign`. A sale is committed — the same everyday act Chapter
0's exercise triggered by hand — and then exactly one call,
`run_pulse_once(org, store_wake_gate)`, is what turns that sale into governed,
executed, accepted work.

## Expected observations

```json
{
  "sale_committed_no_human_dispatch": {
    "signal_id": "sig_...",
    "below_reorder_after_sale": true
  },
  "pulse_report": {
    "status": "created",
    "sow_id": "sow_...",
    "assignment_id": "asg_...",
    "assignment_state": "COMPLETED"
  },
  "durable_pulse_event": {
    "new_event_kinds_this_run": [
      "assignment.created",
      "assignment.finished",
      "assignment.running",
      "assignment.workspace_boundary_checked",
      "pulse.work_created",
      "sow.created",
      "sow.ready"
    ],
    "pulse_work_created_present": true
  },
  "structured_origin": {
    "origin_kind": "pulse",
    "sow_id": "sow_...",
    "assignment_id": "asg_...",
    "wake_decision_id": "pdec_...",
    "pulse_event_id": "evt_...",
    "wake_decision_source_signal_id": "sig_...",
    "wake_decision_source_event_id": "evt_...",
    "wake_decision_traces_back_to_this_signal": true
  }
}
```

This is the whole chapter, in four facts:

1. **`pulse_work_created_present: true`.** A genuine `pulse.work_created`
   event landed in the append-only event log during this run — not asserted
   in prose, read back from the ledger after the fact, the same way Chapter
   0 taught you to check every other claim in this book.
2. **`origin_kind: "pulse"`.** Not inferred from the absence of a manual
   dispatch call — a column, read directly.
   `docs/rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md`
   states the holding this row exists to prove: "absence of a CLI
   invocation, process logs, or a manual-origin row is NOT proof."
3. **`wake_decision_traces_back_to_this_signal: true`.** The full chain —
   signal → wake decision → Pulse event → SOW → assignment — is walkable,
   not merely claimed. The wake decision's own `source_signal_id` matches
   the exact signal this sale produced.
4. **`assignment_state: "COMPLETED"`.** The work Pulse created ran through
   the *exact same* `run_assignment` path a human-dispatched assignment
   uses — the same actor-lease and execution-attempt fencing from Chapter 5
   apply here with no exception, no Pulse-only bypass.

Confirm it yourself, independent of this exercise's own summary:

```bash
sqlite3 /tmp/andrea-ch07/.sovereign/organization.db <<'SQL'
SELECT po.origin_kind, po.sow_id, po.assignment_id,
       wd.source_signal_id, wd.source_event_id
FROM pulse_origins po
LEFT JOIN pulse_wake_decisions wd ON wd.id = po.wake_decision_id
ORDER BY po.created_at;
SQL
```

Expected: one row, `origin_kind = pulse`, naming a real signal and a real
source event.

## Why this claim is allowed here and nowhere else in this book

Chapters 0 through 3 say the organization has no heartbeat, and mean it — no
chapter before this one ever calls `run_pulse_once`, and this project's own
curriculum checker refuses any of them from claiming otherwise, mechanically,
every time it runs. That is not this chapter overwriting an old truth; it is
this book being honest about when a truth changed. Chapter 0 itself was
updated, additively, the moment Pulse became real: "Pulse is now real, as a
separate mechanism you invoke yourself... it is not this chapter's exercise,
and it never runs itself." That sentence is still true. This is the chapter
where you invoke it.

The same curriculum checker that refuses an early chapter's Pulse claim
holds THIS chapter to a stricter standard than "the words are true": it
actually runs this exercise and inspects the resulting database for a real
`pulse.*` event and a real, traceable `pulse_origins` row before it will
accept this chapter's own prose claiming Pulse fired. A chapter that
fabricated a `pulse.work_created` event directly — bypassing
`run_pulse_once` entirely — would fail that check even though the *word*
"pulse" appeared nowhere suspicious in its prose. The claim has to be earned
by the mechanism, not merely phrased carefully.

## Learner verification command

```bash
python -m pytest tests/test_pulse.py -k \
  "full_teaching_slice or attribution or does_not_bypass"
python scripts/verify_curriculum.py
```

Expected: all pass. The pytest selection proves the full sale-to-accepted
slice through the real mechanism, the source-event-to-SOW attribution chain,
and that Pulse-created work is not exempt from Unit 8's fencing.
`verify_curriculum.py` proves this chapter's own claim is backed by durable
evidence, not merely present in the prose — the mechanical guard this
project's own curriculum checker enforces specifically for Chapter 7.

## Explain it back

1. This file never calls `create_sow`, `ready_sow`, or `assign`. What
   function call is doing the work those three calls did in every earlier
   chapter, and what does it do differently?
2. `pulse_wake_decisions.source_signal_id` is `UNIQUE`. What real problem
   does that one constraint prevent, at the database level, that a
   Python-level "check first, then insert" could not?
3. "Absence of a manual-origin row is not proof of Pulse origin." Why is
   that distinction worth a dedicated table rather than just checking
   whether any human-facing CLI command was invoked?
4. The assignment Pulse created ran through the exact same `run_assignment`
   path Chapter 5 fenced. Why does that matter for trusting this chapter's
   own `COMPLETED` result?
5. What specifically would make this chapter's own Pulse claim FALSE — name
   at least two different ways the underlying ledger could fail to back up
   the prose above, and explain how you would notice.

## Where to look next

- `src/sovereign_agent/pulse.py` — `run_pulse_once`, the whole mechanism
- `src/reference_organizations/store/pulse_gate.py` — the Store's own wake
  gate, deliberately outside `sovereign_agent`'s own module budget
- `docs/v1-unit9-pulse-proactive-work.md` — the full contract and proof
  matrix, including the F-U9-1 correction that made the canonical creation
  transaction genuinely atomic
- `docs/rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md` — why
  Pulse is not a fourth step of the supervisor's own tick

`solution.py` imports the production package rather than copying it.

You have now completed all seven chapters. **Added, Unit 11:** the Store's
own governed territory now expands — Chapters 8 through 12 land alongside
it, the same way Chapters 4 through 7 landed alongside Units 7 through 9.

Next: [Chapter 8 — The Store becomes a catalog](../ch08_the_store_becomes_a_catalog/README.md)
