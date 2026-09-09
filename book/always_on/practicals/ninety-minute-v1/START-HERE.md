# Ninety-minute practicals for the complete book

**Created:** 2026-09-09 · **Edition:** v1 · **Doctrinal basis:** CLAUDE.md Rev 17

There are **32 student notebooks: two for each of 16 chapters**. Every notebook is planned for
**90 minutes of dedicated work**, making 48 hours of core practical study. Unit A builds and
connects; Unit B investigates, repairs and transfers. Each has matching Markdown and a separate
worked instructor edition. The earlier Chapter 2 classroom pack remains an archived shorter
teaching option; this course applies ninety minutes to each unit.

[Complete student ZIP](complete-student-course-v1.zip) ·
[Complete instructor ZIP](complete-instructor-course-v1.zip)

## Start one notebook independently

Use a Python 3.14 Jupyter kernel. Pydantic 2 is the only additional runtime package; setup provides
`%pip install "pydantic==2.13.4"` if needed. Install before class and restart the kernel. These
complete-book notebooks do not claim compatibility with a hosted service's default interpreter.
No repository checkout, previous kernel, model API key or supplier account is required. Each
notebook embeds the frozen teaching runtime and explains the concepts and APIs used by its work.

Basic Python variables, functions, loops, conditions, lists and dictionaries are prerequisites.
New specialized concepts and libraries are introduced with small runnable examples. Read the
goal and predict before execution. Unfinished student functions print NEEDS_WORK; fill the exercise
cells and rerun their feedback. Preserve your first attempt before consulting instructor answers.

Unit B defaults to a labelled supplied reference start. To use your own Unit A work, set
`LEARNER_HANDOFF` to the successful saved artifact. Invalid selected work refuses rather than
silently falling back. Retained notebooks, source, predictions and observations are learning
evidence; the reference starting point does not certify prior learner construction.

## Choose a chapter

| Chapter | Unit A · 90 minutes | Unit B · 90 minutes | Files and teaching guide |
|---|---|---|---|
| 1 | Build a grounded morning brief | Put prompts inside a harness | [Open chapter](ch01/README.md) |
| 2 | Construct typed shop tools | Break, repair and transfer typed shop tools | [Open chapter](ch02/README.md) |
| 3 | Build a bounded model and tool loop | Repair failed-call accounting | [Open chapter](ch03/README.md) |
| 4 | Construct durable memory | Break, repair and transfer durable memory | [Open chapter](ch04/README.md) |
| 5 | Construct versioned skills | Break, repair and transfer versioned skills | [Open chapter](ch05/README.md) |
| 6 | Construct private messaging | Break, repair and transfer private messaging | [Open chapter](ch06/README.md) |
| 7 | Construct scheduling | Break, repair and transfer scheduling | [Open chapter](ch07/README.md) |
| 8 | Construct exact approval | Break, repair and transfer exact approval | [Open chapter](ch08/README.md) |
| 9 | Build durable intent and evidence | Survive the ambiguous order | [Open chapter](ch09/README.md) |
| 10 | Construct worker recovery | Break, repair and transfer worker recovery | [Open chapter](ch10/README.md) |
| 11 | Construct tool isolation | Break, repair and transfer tool isolation | [Open chapter](ch11/README.md) |
| 12 | Construct evaluation | Break, repair and transfer evaluation | [Open chapter](ch12/README.md) |
| 13 | Construct controlled improvement | Break, repair and transfer controlled improvement | [Open chapter](ch13/README.md) |
| 14 | Construct bounded delegation | Break, repair and transfer bounded delegation | [Open chapter](ch14/README.md) |
| 15 | Construct operating and restoring | Break, repair and transfer operating and restoring | [Open chapter](ch15/README.md) |
| 16 | Construct acceptance | Break, repair and transfer acceptance | [Open chapter](ch16/README.md) |

## What is included and what is verified

Each chapter includes two student notebook/Markdown pairs, two worked instructor pairs, a
ninety-minute-per-unit guide, a chapter index and separate chapter ZIPs. The complete student
archive excludes instructor answers, holdouts and teaching guides. The instructor archive adds
those materials. The source repository also contains the reproducible authoring and verification
tools and a receipt binding the generated files to their tested bytes.

The release gate executes all notebooks independently, checks repeated execution and selected
learner handoff paths, checks canonical Markdown/notebook parity, and challenges graders with
incorrect implementations. Instructor holdouts verify additional cases. These are mechanical
checks; dedicated-work duration, explanation quality and classroom learning are observed by the
teacher, not inferred from a cell count. Live providers, phone delivery, OS containment and host
operation remain separately labelled extensions.
