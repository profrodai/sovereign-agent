# `book/` is a content source, not a site

This directory is the source of truth for the Sovereign Agent textbook. It is
designated for rendering by a separate site repository; **which** repository is
recorded in the ruling, not here. That integration does not exist yet, so this
document describes the contract a consumer inherits, not a pipeline you can
watch run.

This file names no consumer on purpose. A source that hardcodes its destination
has to be edited whenever the destination changes — and it did change: an
earlier draft named the wrong site in three files. The contract a renderer
inherits does not depend on which renderer it is.

**This repository builds no site of its own.** It previously carried a MkDocs
configuration and a Documentation workflow; those existed only to produce a
second site nobody wanted, and were removed. Anything here that looks like a
publishing pipeline is gone deliberately — if you find one, it drifted back in.

## What a consumer can rely on

Each chapter is a directory `chNN_<slug>/` containing:

| File | Contract |
| --- | --- |
| `README.md` | the chapter, in Markdown, with the sections below |
| `solution.py` | runnable code that **imports the production package** rather than copying it |
| `INSTRUCTOR.md` | the chapter's own facilitation note (added Unit 10; see below) |

Every chapter README carries these sections, in this order:

- `## Learning objective` — one concrete thing the reader will be able to do
- an exercise (`## The exercise` or `## Exercise N`)
- expected observations, with the **real output** of the commands shown
- `## Learner verification command` — how the reader checks their own work
- `## Explain it back` — questions with no lookup answer

## Instructor notes (added Unit 10)

Each chapter directory also carries an `INSTRUCTOR.md`, co-located beside its
`README.md` and `solution.py`. `book/INSTRUCTOR.md` indexes every chapter's
own note and states how the curriculum fits together as one taught course.

`INSTRUCTOR.md` carries no site frontmatter — the same renderer-agnostic
constraint stated below for every chapter `README.md`. It is written for
whoever is facilitating a guided session, not for a learner reading alone;
see `book/INSTRUCTOR.md` itself for who that audience is and why.

Every chapter `INSTRUCTOR.md` carries these seven sections, in this order:

| Section | What it answers |
| --- | --- |
| `## Teaching intent` | What this chapter is FOR, beyond its own learning objective |
| `## Prerequisite knowledge` | What a facilitator should confirm the learner already has |
| `## Likely misconceptions` | Specific wrong beliefs learners tend to form, and what corrects them |
| `## Observation checkpoints` | Concrete moments to stop and confirm the learner actually saw what mattered |
| `## Discussion prompts` | Group-conversation questions, distinct from the chapter's own "Explain it back" |
| `## Facilitation timing` | A realistic guided-session time budget |
| `## Exercise debrief and assessment` | How to tell, from watching or reading a learner's answers, whether the chapter landed |

`scripts/verify_curriculum.py` mechanically checks that every required
chapter's `INSTRUCTOR.md` exists and carries all seven sections — a
structural check only. It cannot and does not grade whether a misconception
list is accurate, whether a timing estimate is realistic, or whether a
discussion prompt is any good; that judgment stays with whoever facilitates.

## What is guaranteed, and by what

`scripts/verify_curriculum.py` runs in CI and fails the build if any of these
break:

- a required chapter is missing, or lacks any required section
- a required chapter's co-located `INSTRUCTOR.md` is missing, or lacks any of
  its seven required sections (added Unit 10)
- `solution.py` does not import the production package, or copies implementation
- **the exercise does not execute** — every runnable chapter is actually run
  against a fresh organization, not merely imported
- a chapter links to a file that does not exist
- a chapter references a `scripts/*.py` that does not exist
- a chapter's previous/next links, and `book/README.md`'s own index, do not
  form one coherent sequence (added Unit 10) — each chapter's forward link
  must point at the immediate next required chapter, the last chapter must
  carry none, and the index must list every required chapter in order. The
  earlier version of this gate checked only that individual links resolved,
  never that they chained correctly.
- a chapter claims Pulse behaviour it did not earn — **chapter-scoped as of
  Unit 10, not removed.** Chapters 0-6 remain unconditionally forbidden from
  claiming the organization woke itself, exactly as before Unit 9 existed.
  Chapter 7 may make that claim, but only because its own already-executed
  exercise leaves durable, structured evidence behind: a real `pulse.*` event
  in the append-only event log, AND a traceable `pulse_origins` row whose
  `wake_decision_id` resolves to a real `pulse_wake_decisions` row naming a
  real source signal. A claim backed by no such chain fails identically
  whether the underlying `run_pulse_once` call was quietly removed or the
  evidence was fabricated by inserting a `pulse.*` event directly — the check
  does not special-case how the gap arose, only whether the trace exists.
- any `book/**/*.md` file begins with a site frontmatter block (added
  Unit 10) — a leading `---` YAML block fails the gate, formalizing what this
  document already states in prose two sections below.

So a consumer inherits chapters whose **exercises execute**, whose links
resolve and chain in order, whose code imports what it says it imports, and
whose Pulse claims (Chapter 7 only) are backed by evidence the gate itself
re-derives rather than trusts.

### What is deliberately NOT mechanically checked

Additive-only editing of Chapters 0-3 (no rewritten claim, no weakened
exercise, only navigation, terminology, and forward-reference improvements)
is a review-discipline requirement, not a mechanical check. No heuristic here
(e.g. "no line was deleted") would actually prove the property it claims to
— a line can be deleted and re-added with different meaning, or left alone
while its surrounding claim is quietly undermined by an edit elsewhere. Unit
10 does not build a check that cannot verify what it claims; this is stated
here as a known, permanent limit, not a gap to be silently papered over
later.

### The limit, stated exactly

The gate executes each chapter's `solution.py` entry point. It does **not**
execute the commands shown in prose, and it does not compare displayed output
against a real run. Replacing `sovereign-agent doctor` in a fenced block with
`sovereign-agent definitely-not-a-command` leaves the gate reporting
`curriculum sound`. That was reproduced, not assumed.

An earlier version of this document claimed fenced commands were verified. They
are not, and a contract that overstates its own guarantee is worse than one
claiming less: a consumer would trust prose that nothing checks. What is checked
is the list above; what is not checked is this paragraph's subject.

## What a consumer must supply

Presentation. Ordering beyond the `chNN_` prefix. Any frontmatter its own
collection schema requires — this directory carries none, because frontmatter
belongs to the site that renders it, not to the source.

## Rendering notes

- Chapter cross-links are relative, of the form `../chNN_<slug>/README.md`.
- Links into `../../docs/` point at repository reference material and may need
  rewriting or dropping depending on what the site publishes.
- Fenced code blocks are real commands with real output, executed by hand when
  written. They are **not** verified by any gate — see the limit below — so
  render them verbatim rather than reformatting, and treat a mismatch between a
  block and reality as a bug worth reporting.

## Checking it yourself

```bash
python scripts/verify_curriculum.py
```

Exits 0 only when every statement in "What is guaranteed" holds. It says nothing
about the prose, by design and as stated above.
