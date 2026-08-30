# Teaching this book

This file indexes every chapter's own instructor note
(`chNN_<slug>/INSTRUCTOR.md`) and states how the curriculum fits together as
one course, for whoever is running a session rather than reading alone.

It carries no site frontmatter, matching every other file in `book/` — see
`book/CONTENT-SOURCE.md`'s own renderer-agnostic contract, which this file
extends to cover instructor notes explicitly.

## Who this is for

Someone facilitating Sovereign Agent as a taught course, a workshop, or a
guided onboarding session — not a learner working alone (that reader wants
the chapter `README.md`s, not this file). The audience this book itself is
written for is Andrea (`docs/andrea-alpha-evaluation.md`,
`docs/andrea-chapters-0-7-evaluation.md`): a master's student who knows some
Python but has not run a service, debugged a transaction, or argued about
governance. Every instructor note below is calibrated to that reader, not to
an expert.

## The shape of every chapter's instructor note

Each `chNN_<slug>/INSTRUCTOR.md` carries these seven sections, always in this
order, with no frontmatter:

| Section | What it answers |
| --- | --- |
| Teaching intent | What this chapter is FOR, beyond its own learning objective — why it exists in the sequence |
| Prerequisite knowledge | What a facilitator should confirm the learner already has, from earlier chapters or elsewhere |
| Likely misconceptions | Specific wrong beliefs learners tend to form here, and what corrects them |
| Observation checkpoints | Concrete moments in the exercise where a facilitator should stop and confirm the learner actually saw what mattered |
| Discussion prompts | Questions to open a group conversation, distinct from the chapter's own "Explain it back" (which is for an individual learner, unassisted) |
| Facilitation timing | A realistic time budget for a guided session, and where the time actually goes |
| Exercise debrief and assessment | How to tell, from watching or reading a learner's own answers, whether the chapter landed |

## The one course, chapter by chapter

| Chapter | Teaches | Depends on |
| --- | --- | --- |
| [0](ch00_first_shift/INSTRUCTOR.md) | `ACCEPTED` is a proved claim, not a status string | Nothing — the cold-start chapter |
| [1](ch01_organization_remembers/INSTRUCTOR.md) | Where truth lives: canonical SQLite vs. generated projections | Chapter 0's vocabulary (outcome, SOW, assignment) |
| [2](ch02_work_needs_governance/INSTRUCTOR.md) | The full governance vocabulary, and every way acceptance refuses a lie | Chapter 1's canonical/projection distinction |
| [3](ch03_actor_is_not_a_model/INSTRUCTOR.md) | An actor's identity survives swapping its intelligence | Chapter 2's no-self-approval property |
| [4](ch04_work_stays_inside_its_boundary/INSTRUCTOR.md) | The workspace boundary is detectable, not enforced by a sandbox | Chapter 3's provider/actor distinction |
| [5](ch05_authority_needs_a_fence/INSTRUCTOR.md) | Process identity vs. actor identity; leases and execution attempts | Chapter 4's workspace vocabulary |
| [6](ch06_the_organization_recovers/INSTRUCTOR.md) | A process cannot record its own death; the supervisor recovers, never guesses | Chapter 5's fencing vocabulary |
| [7](ch07_the_organization_wakes_itself/INSTRUCTOR.md) | Genuine proactive work, with durable structured evidence | Chapters 0-6, especially 5's fencing (Pulse reuses it unchanged) |
| [8](ch08_the_store_becomes_a_catalog/INSTRUCTOR.md) | A genuine multi-SKU catalog, independent at the schema level | Chapter 0's `Product`/`InventoryPosition` vocabulary |
| [9](ch09_each_product_has_its_own_threshold/INSTRUCTOR.md) | Independent stock state and reorder decisions, per SKU | Chapter 8's catalog |
| [10](ch10_one_signal_wakes_one_need/INSTRUCTOR.md) | The wake gate binds each signal to its own SKU's own outcome | Chapter 7's wake-gate vocabulary; Chapter 9's per-SKU thresholds |
| [11](ch11_replenishment_scales_without_losing_governance/INSTRUCTOR.md) | Governance scales to multiple SKUs without weakening | Chapters 0-10, especially the full accept chain and Chapter 10's binding |
| [12](ch12_the_pilot_begins_with_a_receipt/INSTRUCTOR.md) | The pilot-start mechanism; "started" is not "finished" | Chapter 7's CAS/idempotency vocabulary |

Chapters 0-3 teach the governed, human-dispatched core. Chapters 4-6 teach
what "the code exists but nobody has taught it yet" looked like for three
full units (7 and 8) before this unit closed that gap — none of it is new
production behavior, all of it was already `ACCEPTED` before this chapter
existed. Chapter 7 is the only chapter allowed to claim the organization
wakes itself, and only because its own exercise genuinely produces the
durable evidence that claim requires — see that chapter's own instructor
note for exactly how a facilitator should watch for a learner overclaiming
this past what the mechanism proves.

**Added, Unit 11:** Chapters 8-11 extend the Store's own governed pipeline
from one SKU to a genuine multi-product catalog, reusing every mechanism
Chapters 0-7 already taught (record_sale, the wake gate, run_pulse_once,
apply_restock, the full accept chain) without introducing any new signal
kind, effect kind, or governance concept — the teaching point across all
four chapters is that scaling to more SKUs required no new production
surface, only proof that isolation holds. Chapter 12 closes the book (for
now) with the pilot-start mechanism, built and proven but deliberately
never invoked against the real named pilot organization from inside this
curriculum — see that chapter's own instructor note for the disposable-
identity discipline and the started-vs-finished distinction it teaches.

## Running the whole course

A full guided run of Chapters 0-7, at the per-chapter facilitation timing
named in each instructor note, is a full day (roughly six hours of
facilitated time, not counting breaks) for a group with no prior exposure to
the codebase. Chapters 0-2 are the load-bearing conceptual chapters — an
instructor short on time should protect their timing before trimming
Chapters 4-6, which are more mechanically dense but individually shorter to
facilitate.

**Added, Unit 11:** Chapters 8-12 add roughly two more hours of facilitated
time (see each chapter's own "Facilitation timing"), with Chapter 11 as the
longest of the five — it is deliberately the capstone for the Store's own
multi-SKU arc, the way Chapter 7 was the capstone for Pulse itself. A
facilitator running the full twelve-chapter course in one guided session
should budget a long day, or split at the Chapter 7/8 boundary, which is
already a natural pause point in the book's own narrative (Pulse existing,
before the Store's own territory expands).

Nothing in this file or any chapter's instructor note is verified by
`scripts/verify_curriculum.py` beyond the structural checks named in
`book/CONTENT-SOURCE.md` (the file exists, every required section is
present). Facilitation quality is not something a script can grade.
