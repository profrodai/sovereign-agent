# Chapter 2 — Work needs governance

## Learning objective

Understand how a piece of work travels from "somebody wants this" to "this is
done", and why every step in that journey exists. By the end you should be able
to explain what makes `ACCEPTED` mean something — and to break it on purpose.

Chapter 1 was about memory. This chapter is about **judgement**: who is allowed
to decide what, and what has to be true before a decision sticks.

## The vocabulary, in the order the work moves

| Word | What it is |
| --- | --- |
| **Outcome** | The state of the world someone wants. "The tea jar stays stocked." |
| **Acceptance check** | A deterministic question that decides whether the outcome is true. |
| **SOW** | A statement of work: scope, non-goals, deliverables, done-when. |
| **Assignment** | One actor bound to one SOW, with a workspace. |
| **Receipt** | The durable record of an execution: who ran, how it ended. |
| **Evidence** | The record of a check having been run, bound to what it proves. |
| **Verification** | Actually executing the declared checks. |
| **Review** | A different actor reading the work. |
| **Acceptance** | The Principal declaring the outcome true — if it survives proof. |
| **Ruling** | A recorded decision that changes the rules. |

## Exercise 1: follow one outcome through the whole chain

```bash
sovereign-agent demo store --mode simulated --root /tmp/andrea-gov
DB=/tmp/andrea-gov/.sovereign/organization.db

sqlite3 -header -column "$DB" \
  "SELECT json_extract(record,'$.title') AS title,
          json_extract(record,'$.state') AS state,
          json_extract(record,'$.acceptance_checks') AS checks
   FROM outcomes;"
```

The outcome declares **three** acceptance checks. Note that the outcome declares
them — not the provider, and not the operator who does the work. The thing being
judged does not get to choose its own judges.

```bash
sqlite3 -header -column "$DB" \
  "SELECT check_id, success, substr(outcome_id,1,20) AS outcome,
          substr(assignment_id,1,20) AS execution
   FROM evidence;"
```

Three evidence rows, one per declared check. Each one records *which question*
was asked, *about which outcome*, and *during which execution*. That binding is
the difference between evidence and a filename.

## Exercise 2: try to accept something that is not true

This is the important exercise. Governance is only real if it refuses.

```bash
python - <<'PY'
import pathlib, tempfile
from reference_organizations.store.demo import run_simulated
from sovereign_agent.organization import Organization
from sovereign_agent.errors import Refusal

root = pathlib.Path(tempfile.mkdtemp())
run_simulated(root)
org = Organization(root)
outcome_id = org.db.connection.execute("SELECT id FROM outcomes").fetchone()["id"]

# Empty the shelf, then re-open the outcome and try to accept it again.
org.db.connection.execute("UPDATE inventory SET on_hand=0 WHERE sku='SKU-TEA'")
org.db.connection.execute(
    "UPDATE outcomes SET record=json_set(record,'$.state','VERIFYING') WHERE id=?",
    (outcome_id,))
org.db.connection.commit()

try:
    org.accept(outcome_id, "principal-human")
    print("ACCEPTED  <-- this would be a bug")
except Refusal as refusal:
    print("REFUSED:", str(refusal).splitlines()[0])
PY
```

Expected: a refusal naming `inventory_at_or_above_reorder_point`. Acceptance
**re-runs the checks against the world at the moment of acceptance**. It does
not trust that they passed earlier.

That last sentence is the entire lesson of this chapter, and it was learned the
hard way: an earlier version of this system accepted an outcome by checking that
someone had handed it a non-empty list of evidence IDs. The IDs were never
looked up. You could accept with `["evd_i_just_made_this_up"]`.

## Exercise 3: try the other ways of lying

Each of these is refused for a different reason. Run the suite that proves it:

```bash
python -m pytest tests/test_acceptance_falsification.py -v
```

Read the test names. They are the list of lies this system knows how to catch:

- evidence that does not exist (refused by a **foreign key**, in the database)
- evidence that reports failure
- evidence for a different outcome
- evidence from a different execution
- evidence that is **stale** — true when written, but the world moved since
- a declared check with no evidence at all
- an outcome with no SOW
- the operator trying to accept its own work
- a malformed provider report
- a proposal outside its allowed bounds

## Exercise 4: no self-approval

```bash
python -c "
from sovereign_agent.policy import forbid_self_approval
from sovereign_agent.errors import Refusal
try:
    forbid_self_approval('operator-course','operator-course')
except Refusal as r:
    print('REFUSED:', str(r).splitlines()[0])
"
```

Three different actors touch the store outcome, and none of them can do another's
job:

- `operator-course` does the work.
- `sparring-course` reviews it.
- `principal-human` accepts it.

`accept()` does not take a "who performed this" argument. It **derives** the
performers from the assignments in the ledger, then refuses if the accepter is
among them. If the caller could name the performer, the caller could name a
convenient stranger, and the separation would be decoration.

## Exercise 5: watch verification actually run

```bash
python -c "
import tempfile, pathlib
from reference_organizations.store.demo import run_simulated
from sovereign_agent.organization import Organization
from sovereign_agent.checks import run_check
root = pathlib.Path(tempfile.mkdtemp()); run_simulated(root)
org = Organization(root)
oid = org.db.connection.execute('SELECT id FROM outcomes').fetchone()['id']
for check_id in org._outcome(oid).acceptance_checks:
    r = run_check(org.db, check_id, 'SKU-TEA')
    print(f'{r.check_id}: {\"PASS\" if r.success else \"FAIL\"} - {r.detail}')
"
```

Expected:

```text
inventory_at_or_above_reorder_point: PASS - on_hand=8 vs reorder_point=3
cash_reconciles: PASS - 1 purchase entr(y/ies) reconcile
replenishment_event_exists: PASS - 1 replenishment event(s) for SKU-TEA
```

Each check reports the facts it observed. `verify_outcome` used to change a
status field and run no checks at all — a verification step that verified
nothing. Now it executes every declared check, and an unknown or crashing check
**fails closed** rather than being skipped.

## Exercise 6: the proof itself cannot be rewritten

Chapter 1 showed that `events` refuses `UPDATE` and `DELETE`. The same guarantee
now covers every table acceptance reads as proof — `effects`, `verifications`,
`reviews`, `evidence`:

```bash
sqlite3 /tmp/andrea-gov/.sovereign/organization.db \
  "UPDATE evidence SET success = 1;"
```

Expected: `Error: stepping, evidence are append-only: update refused`.

This was not always true, and the story is worth knowing. Append-only was added
to `events` because acceptance rested on events. Then acceptance came to rest on
evidence, reviews, verifications and effects — and the guards stayed where they
were. For a while the tables carrying the proof were the ones with no
protection, while the table they replaced was still immune. A reviewer put it
exactly: *the guarantee stayed put while the load moved.*

One thing append-only cannot do is stop a forged **append**: inserting is
precisely what it permits. An effect is therefore cross-checked against the
event committed alongside it, and an effect with no matching event is an
incomplete record.

Now the part that matters more, because it is where most systems overclaim.
That cross-check detects **inconsistency**. It does not prove **authenticity**.
Someone who can write arbitrary rows can append an effect *and* its matching
event — two rows that agree with each other and are both invented. The
organization will accept them.

That is not a hole to be plugged with a third table. Every check you can write
inside the database constrains what the *code* does, and an attacker with a
database handle is not the code. Proving authenticity needs something the
database does not hold — a signature key kept outside it — which is a different
subject and out of scope here.

So the honest statement, which
[the ruling](../../docs/rulings/2026-08-26-sqlite-writers-are-inside-the-boundary.md)
records: **anyone who can write arbitrary rows can rewrite the organization's
memory.** Everything in this chapter protects the ledger from mistakes and
ordinary tools. Knowing exactly which door is open is worth more than believing
they are all shut.

## Exercise 7: being refused is not the end

Chapter 2 has spent five exercises showing the organization refusing things. A
fair question: what happens to work that gets refused? Is it dead?

```bash
python -m pytest tests/test_recovery.py -v
```

Read the test names. The cycle they prove is:

```text
verification fails
  -> Sparring requests changes           (SOW state: CHANGES_REQUESTED)
  -> the world is repaired
  -> a NEW assignment is created         (SOW state: ASSIGNED)
  -> verification runs again             (a new batch)
  -> Sparring reviews the new batch      (accepted)
  -> the Principal accepts
```

Two details worth pausing on.

**Recovery creates a new assignment.** Repaired work is new work, and the ledger
says so. The failed execution is not overwritten or reused — you can still read
what went wrong the first time.

**Nothing is deleted.** After recovery the database holds two verifications and
two reviews, including the `changes_requested` one. The organization remembers
being wrong. That is the difference between a system that learns and a system
that launders its history.

This path did not exist while this chapter was first written. `changes_requested`
was terminal: the only way forward from a refusal was to delete the organization
and start over. A book that teaches "refusal is the system working" while
shipping a refusal you cannot recover from is teaching the opposite of what it
says.

## Learner verification command

```bash
python -m pytest tests/test_acceptance_falsification.py tests/test_actors_and_mailbox.py \
  tests/test_recovery.py -q
```

Expected: all pass. Together they prove that acceptance refuses every lie listed
above, and that authority cannot be self-granted.

## Explain it back

1. An outcome declares its acceptance checks. Why is it dangerous to let the
   actor doing the work declare them instead?
2. Evidence records a check id, an outcome id, and an execution id. Remove any
   one of those three. What lie becomes possible?
3. "Stale evidence" is refused even when the check would still pass today.
   Why bother refusing something that is still true?
4. `accept()` deliberately has no `performer_id` parameter. Explain why adding
   one back would quietly disable no-self-approval.
5. What is the difference between a **receipt** and **evidence**? One describes
   an execution; the other describes a fact about the world. Which is which?
6. Recovery from `changes_requested` creates a *new* assignment rather than
   reusing the failed one. What would you lose if it reused it?
7. `events` was append-only long before `evidence` was. Explain, in terms of
   where the proof lives, why protecting only `events` stopped being enough.
8. Append-only refuses rewriting a row but permits adding one. Why does that
   make corroboration necessary, and what corroborates an effect?
7. Acceptance requires a review of the **exact** verification batch it is
   accepting on. Describe the lie that would be possible if it accepted any
   review of the outcome instead.

Next: [Chapter 3 — The actor is not a model](../ch03_actor_is_not_a_model/README.md)
