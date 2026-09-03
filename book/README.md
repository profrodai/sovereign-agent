# Sovereign Agent: the executable textbook

The book grows with the implementation. Each chapter uses the production
package; it does not copy or fork it.

**New here? Start with the front matter:** [`PREFACE.md`](PREFACE.md) (who
this book is for, prerequisites, setup, and the build-break-repair teaching
method) and [`CONVENTIONS.md`](CONVENTIONS.md) (notation, recurring terms,
and the chapter-to-lab map). Both are additive — the chapter sequence below
is unchanged and remains the required reading path.

Read them in order. Each one takes apart something the previous chapter asked
you to take on faith.

Use the [companion labs](labs/README.md) alongside the chapters. Every lab gives
you an intentionally incomplete starter, behavioral checks, adversarial
mutations, and a verified reference solution. The checks grade observable
invariants rather than requiring your code to look like the reference.

- [Chapter 0: Lucy's first shift](ch00_first_shift/README.md) — run one
  complete piece of work and learn that `ACCEPTED` is a proved claim
- [Chapter 1: The organization remembers](ch01_organization_remembers/README.md) —
  SQLite, transactions, append-only events, and what is canonical versus derived
- [Chapter 2: Work needs governance](ch02_work_needs_governance/README.md) —
  outcomes, SOWs, evidence, verification, review, and no-self-approval
- [Chapter 3: The actor is not a model](ch03_actor_is_not_a_model/README.md) —
  providers are probed CLIs; Cursor is equal to Claude and Codex
- [Chapter 4: Work stays inside its boundary](ch04_work_stays_inside_its_boundary/README.md) —
  a detectable workspace boundary, safe joins, and reclaim as a policy choice
- [Chapter 5: Authority needs a fence](ch05_authority_needs_a_fence/README.md) —
  process identity, actor leases, and execution-attempt fencing bound together
- [Chapter 6: The organization recovers](ch06_the_organization_recovers/README.md) —
  a real hard-killed worker, and the supervisor that recovers it without
  guessing success
- [Chapter 7: The organization wakes itself](ch07_the_organization_wakes_itself/README.md) —
  genuine Pulse: governed work created without a human prompt, with durable,
  structured evidence
- [Chapter 8: The Store becomes a catalog](ch08_the_store_becomes_a_catalog/README.md) —
  the single-product fixture becomes a genuine multi-SKU catalog
- [Chapter 9: Each product has its own threshold](ch09_each_product_has_its_own_threshold/README.md) —
  independent stock state and reorder decisions, per SKU
- [Chapter 10: One signal wakes one need](ch10_one_signal_wakes_one_need/README.md) —
  the wake gate binds each signal to its own SKU's own outcome, never another's
- [Chapter 11: Replenishment scales without losing governance](ch11_replenishment_scales_without_losing_governance/README.md) —
  multiple governed replenishment chains, idempotency and attribution intact
- [Chapter 12: The pilot begins with a receipt](ch12_the_pilot_begins_with_a_receipt/README.md) —
  the pilot-start mechanism, exercised against a disposable identity, and
  what "started" does and does not mean

## What is not here yet

Pulse — the organization waking itself up — was Unit 9's own future territory
when Chapters 0-3 were written. Nothing in Chapters 0-3 simulates a Pulse
event, and their store demo is explicitly manually dispatched. A chapter that
promised proactive behaviour before the code could do it would be the same
kind of lie this book spends Chapter 2 teaching you to catch. That claim is
still true of Chapters 0-3 today, and is mechanically enforced: this
project's own curriculum checker refuses any of them from claiming Pulse
fired.

**Added, Unit 9:** Pulse became real production code (`sovereign-agent pulse
--once`; see `docs/v1-unit9-pulse-proactive-work.md`).

**Added, Unit 10:** Chapter 7 is where this book exercises it — the first and
only chapter allowed to claim the organization wakes itself, and only because
its own exercise genuinely invokes the mechanism and leaves durable,
structured evidence behind, mechanically checked, not merely asserted in
prose. Chapters 0-3 remain exactly as they were: manually dispatched, and
truthful about it. Chapters 4-6 (workspace lifecycle, fencing, recovery)
teach real, ACCEPTED Units 7 and 8 behavior that was already true before Unit
10; they were simply not yet chapters.

**Added, Unit 11:** Chapters 8 through 12 land alongside the Store's own
expansion into a genuine multi-SKU catalog and the pilot-start mechanism.
Chapter 12's own exercise runs against a disposable, exercise-scoped pilot
identity — the real 30-day Store pilot has not started; that is a separate,
later, separately-authorized act outside this book's own scope. See
`docs/v1-unit11-store-expansion-pilot-start.md` for the full contract.

## Every chapter contains

- a concrete learning objective
- a runnable exercise
- expected observations
- a learner verification command
- an "explain it back" section
- a `solution.py` that imports the production package

Run `python scripts/verify_curriculum.py` to check that all of that is actually
present and that the chapters' imports still work.

Run `python scripts/verify_book_labs.py` to execute all companion reference
solutions twice from fresh roots and compare their observations with the
checked-in expected results.
