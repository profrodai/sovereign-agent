# Chapter 12 — The pilot begins with a receipt

Lucy is ready to let the organization run her shop for real — a trial period, a
pilot. It is the moment everything has been building toward, and it is exactly the
moment a lesser system would start lying. "Pilot started!" it would announce, and
a week later nobody could say for sure whether it actually had, or whether it had
quietly finished, or stalled, or half-begun twice.

This final chapter builds the smallest, most careful version of that first step —
and spends as much energy on what it *doesn't* prove as on what it does. Starting
a pilot leaves a receipt: a durable, queryable record that it began. That receipt
says nothing about whether the pilot has *finished*, and — crucially — the system
does not pretend otherwise, because the machinery to check completion does not
exist. A book about telling the truth ends by drawing the exact line between what
has been proven and what has not.

## Learning objective

Run the pilot-start mechanism, against a disposable
exercise identity, and read back the durable record and event it produces —
then understand precisely why that record proves the pilot **started** and
proves nothing at all about whether it has **finished**.

**This chapter never touches the real named pilot organization.** The
identity this exercise uses, `book-ch12-exercise-pilot`, is structurally
distinct from any real pilot identity: it is a fixture value, reserved for
this exercise, that appears nowhere in this project's own real-pilot
tooling — because no real-pilot tooling exists yet. The real pilot start is
a separate, later, separately-authorized act, entirely outside this book.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Pilot-start mechanism** | `start_pilot`: one atomic transaction that writes a queryable `pilots` row and an append-only `pilot.started` event, together or not at all. |
| **Idempotent replay** | Calling `start_pilot` again with the SAME pilot identity never creates a second row or a second event — it returns the first call's own record. |
| **Fail-closed refusal** | A DIFFERENT pilot identity, while one is already active, is refused outright — never silently ignored, never silently allowed to proceed. |
| **Started vs. finished** | This mechanism proves a pilot BEGAN. Nothing in this project claims, or could currently check, that a pilot has ENDED — there is no completion mechanism yet. |

## The exercise

```bash
python book/ch12_the_pilot_begins_with_a_receipt/solution.py --root /tmp/lucy-ch12
```

Read the file first, and read `EXERCISE_PILOT_ID`'s own comment before
running anything: the whole point of this chapter is that its own exercise
can never reach a real pilot, by construction, not merely by convention.

## Expected observations

```json
{
  "disposable_identity": {
    "exercise_pilot_id": "book-ch12-exercise-pilot",
    "structurally_distinct_prefix": true
  },
  "first_start": { "idempotent_replay": false },
  "replay": { "idempotent_replay": true, "same_started_at_as_first": true },
  "durable_record": {
    "pilot_row_exists": true,
    "store_org_id": "book-ch12-exercise-store-org",
    "pilot_profile_id": "book-ch12-exercise-profile",
    "evidence_namespace": "book-ch12-exercise-evidence-ns"
  },
  "durable_event": {
    "pilot_started_event_count": 1,
    "exactly_one_despite_the_replay_above": true
  },
  "no_duplicate_pilot_row": { "pilots_row_count": 1 },
  "active_pilot": { "pilot_id": "book-ch12-exercise-pilot" },
  "started_is_not_finished": {
    "no_completion_table_exists": true
  }
}
```

Four facts this run proves:

1. **`idempotent_replay: false` then `true`.** The first call genuinely
   creates the pilot; the second call, with the identical identity, is
   recognized as a replay and returns the SAME record — never a second one.
2. **`exactly_one_despite_the_replay_above: true`.** Two calls to
   `start_pilot`, only one `pilot.started` event in the append-only log.
   This is the CAS discipline this project has used throughout
   (`relay.claim()`, `fencing.acquire_actor_lease()`), applied here to a
   pilot's own identity.
3. **`pilots_row_count: 1`.** Not a count this exercise computed in Python
   — read directly from the `pilots` table after both calls.
4. **`no_completion_table_exists: true`.** This is the honesty check this
   chapter's own title promises: nothing in this database claims the pilot
   is finished, because nothing CAN — that mechanism does not exist yet.

Confirm it yourself:

```bash
sqlite3 /tmp/lucy-ch12/.sovereign/organization.db <<'SQL'
SELECT pilot_id, started_at, store_org_id FROM pilots;
SELECT pilot_id FROM active_pilot;
SELECT COUNT(*) FROM events WHERE kind = 'pilot.started';
SQL
```

Expected: one `pilots` row, one `active_pilot` row, and `1` for the event
count.

## Learner verification command

```bash
python -m pytest tests/test_pilot.py
python scripts/verify_curriculum.py
```

Expected: all pass. `tests/test_pilot.py` is where this mechanism's
idempotency, fail-closed refusal, atomicity, and REAL two-connection
concurrency are proven exhaustively — this chapter's own exercise shows you
one slice of that proof matrix, running.

## Explain it back

1. This chapter calls `start_pilot` twice with the SAME identity. What
   would happen, concretely — which table, which constraint — if you
   instead called it a second time with a DIFFERENT pilot identity?
2. `EXERCISE_PILOT_ID` carries a `book-ch12-exercise-` prefix. What makes
   this a STRUCTURAL guarantee against ever touching a real pilot, rather
   than merely a naming convention a careless caller could ignore?
3. `no_completion_table_exists` checks for a table matching
   `%pilot%complet%`. Why does this chapter check for the ABSENCE of a
   mechanism, rather than simply not mentioning completion at all?
4. `tests/test_pilot.py` proves fail-closed refusal and real two-connection
   concurrency — properties this chapter's own single-process exercise does
   not exercise. Why does this chapter still count as proof that the
   mechanism WORKS, even though it does not run those tests itself?

## Where to look next

- `src/reference_organizations/store/pilot.py` — `start_pilot`,
  `active_pilot_id`, the full mechanism
- `src/sovereign_agent/database.py` — migration 16, the `pilots` and
  `active_pilot` schema
- `tests/test_pilot.py` — the full pilot-start proof matrix: the
  different-identity refusal and the two-connection race, which together show
  the pilot's identity is claimed exactly once, atomically, or not at all

`solution.py` imports the production package rather than copying it.

You have now completed all twelve chapters — and built, from an empty
directory, an organization that remembers, refuses, fences, recovers, wakes
itself, scales, and can begin a pilot without lying about it. That last verb is
the one that matters. At every boundary this book named exactly what it had not
yet done, and it ends the same way: the real, live 30-day pilot has not started
here — only a disposable exercise identity has. Starting it for real, running it,
and judging whether it succeeded are the next work, beyond this book. Knowing
precisely where the proven part ends is not a limitation of the system. It is the
system.
