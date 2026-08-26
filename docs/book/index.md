# Sovereign Agent: the executable textbook

The book grows with the implementation. Each chapter uses the production
package; it does not copy or fork it.

Read them in order. Each one takes apart something the previous chapter asked
you to take on faith.

- [Chapter 0: Andrea's first shift](ch00_first_shift.md) — run one
  complete piece of work and learn that `ACCEPTED` is a proved claim
- [Chapter 1: The organization remembers](ch01_organization_remembers.md) —
  SQLite, transactions, append-only events, and what is canonical versus derived
- [Chapter 2: Work needs governance](ch02_work_needs_governance.md) —
  outcomes, SOWs, evidence, verification, review, and no-self-approval
- [Chapter 3: The actor is not a model](ch03_actor_is_not_a_model.md) —
  providers are probed CLIs; Cursor is equal to Claude and Codex

## What is not here yet

Pulse — the organization waking itself up — is Unit 9. Nothing in these chapters
simulates a Pulse event, and the store demo is explicitly manually dispatched. A
chapter that promised proactive behaviour before the code could do it would be
the same kind of lie this book spends Chapter 2 teaching you to catch.

## Every chapter contains

- a concrete learning objective
- a runnable exercise
- expected observations
- a learner verification command
- an "explain it back" section
- a `solution.py` that imports the production package

Run `python scripts/verify_curriculum.py` to check that all of that is actually
present and that the chapters' imports still work.
