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

Chapters 0-3 teach the governed, human-dispatched core. Chapters 4-6 teach
what "the code exists but nobody has taught it yet" looked like for three
full units (7 and 8) before this unit closed that gap — none of it is new
production behavior, all of it was already `ACCEPTED` before this chapter
existed. Chapter 7 is the only chapter allowed to claim the organization
wakes itself, and only because its own exercise genuinely produces the
durable evidence that claim requires — see that chapter's own instructor
note for exactly how a facilitator should watch for a learner overclaiming
this past what the mechanism proves.

## Running the whole course

A full guided run of Chapters 0-7, at the per-chapter facilitation timing
named in each instructor note, is a full day (roughly six hours of
facilitated time, not counting breaks) for a group with no prior exposure to
the codebase. Chapters 0-2 are the load-bearing conceptual chapters — an
instructor short on time should protect their timing before trimming
Chapters 4-6, which are more mechanically dense but individually shorter to
facilitate.

Nothing in this file or any chapter's instructor note is verified by
`scripts/verify_curriculum.py` beyond the structural checks named in
`book/CONTENT-SOURCE.md` (the file exists, every required section is
present). Facilitation quality is not something a script can grade.
