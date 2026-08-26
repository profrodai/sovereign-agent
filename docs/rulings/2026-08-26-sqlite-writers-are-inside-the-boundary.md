# Ruling: SQLite writers are inside the trust boundary

- **id:** `ruling-2026-08-26-sqlite-writers-are-inside-the-boundary`
- **decided:** 2026-08-26
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x append-only guarantees and effect corroboration
- **status:** ACTIVE

## Why this exists

`docs/persistence-boundary.md` already says it plainly:

> anyone who can write arbitrary rows can rewrite the organization's memory

and

> everything here protects the ledger from *mistakes and ordinary tools*, not
> from an actor with arbitrary write access to the database file.

Then a fix for a forged-effect finding described cross-table corroboration as
putting "the proof back on the table where a forged append is detectable", and
Chapter 2 repeated it. **The code and the book claimed a guarantee the project
had already documented that it does not have.**

Both reviewers demonstrated the same thing from different directions. Two
coordinated fresh appends — an effect and its witnessing event — are mutually
consistent and equally forged, and acceptance takes them:

```text
three fresh appends (cash, event, effect) — no trigger fires
*** ACCEPTED — the execution did no work ***
```

Sparring, which had previously reported the corroboration as four layers deep,
retracted: it had found one *ordering* in which the attack failed and reported
it as depth.

## Holdings

1. **SQLite writers are inside the trust boundary.** An actor with arbitrary
   write access to the database file can rewrite the organization's memory. This
   is not a defect to be fixed in 1.x; it is the boundary, stated.
2. **Append-only triggers are mutation safety.** They prevent rewriting and
   replacement by ordinary tools and honest mistakes. They do not prevent
   appending, and appending is how a forgery gets in.
3. **Effect/event corroboration detects incomplete or inconsistent records.** An
   effect with no witnessing event is a half-written state or a hand-added row.
   Corroboration establishes consistency between two claims; it authenticates
   neither.
4. **Two coordinated fresh appends remain a documented limitation.** Not a bug
   to be closed by a third cross-table check.
5. **Authenticating against an arbitrary writer requires a trust root outside
   the database** — signatures or keyed MACs whose key the database never holds
   — and a precise attacker model. Deliberately out of scope for an educational
   release.

## Why not fix it

Because the fix would be the mistake, one table over. Each of the last three
rounds added a mechanism to shore up the previous mechanism, and each new
mechanism inherited the same property: it constrains what the *code* writes, and
an arbitrary writer is not the code. A learner who understands why cross-table
checks cannot authenticate has learned more than one who believes they can.

The honest teaching is the boundary, drawn where it actually falls.

## Consequences

- `Organization.effect_kinds_for_execution` documents detection, not
  authentication.
- `book/ch02_work_needs_governance` teaches the limitation rather than past it.
- `APPEND_ONLY_TABLES` (formerly `PROOF_TABLES`) is named for what it does, and
  is a maintained list rather than a claim of exhaustiveness.
- `test_corroboration_detects_inconsistency_but_does_not_authenticate` records
  the limitation as an asserted fact, so nobody re-derives it as a bug.
