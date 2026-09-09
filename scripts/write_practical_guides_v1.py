"""Write chapter-specific facilitation and navigation for the ninety-minute units."""

from __future__ import annotations

import json

from build_practical_course_v1 import BANK, EDITION, ROOT, UNITS


def main():
    catalog = json.loads((ROOT / "book/always_on/exercises/source-tasks-v1.json").read_text())[
        "chapters"
    ]
    rows = []
    for chapter in range(1, 17):
        units = [unit for unit in UNITS if unit.identity.startswith(f"ch{chapter:02d}")]
        titles = [unit.source.read_text().split("— ", 1)[1].splitlines()[0] for unit in units]
        task = next((row for row in catalog if row["chapter"] == chapter), None)
        old_guide = (
            ROOT / f"book/always_on/exercises/ch{chapter:02d}/instructor-guide-v1.md"
        ).read_text()
        if task:
            evidence = task["construct"] + " " + task["connect"]
            misconception = task["diagnosis"]
            new_case = task["transfer"]
            limitation = task["limit"]
            solution_notes = task["hint"]
        else:
            evidence = {
                1: (
                    "Inspect response envelopes and exact shop snapshots, conne"
                    "ct the learner reader to the brief, and validate changed-p"
                    "roduct drafts independently of prompt wording."
                ),
                3: (
                    "Trace model admission, actual tool observations and termin"
                    "al counters; charge failed admitted attempts and refuse re"
                    "peated call identities."
                ),
                9: (
                    "Inspect local durable intent and independent supplier rows"
                    "; reconcile a lost reply without inventing another operati"
                    "on or spending a reservation twice."
                ),
            }[chapter]
            misconception = {
                1: "A completed assistant response may still contain false business claims.",
                3: (
                    "A provider failure does not erase an admitted attempt or i"
                    "ts configured exposure."
                ),
                9: "A timeout after acceptance is not evidence that no supplier order exists.",
            }[chapter]
            new_case = BANK[chapter]["contract"]
            limitation = {
                1: (
                    "Envelope and structured-draft checks do not certify arbitr"
                    "ary model prose or external purchases."
                ),
                3: (
                    "An authored replay demonstrates loop behavior, not the fre"
                    "quency of a live model choosing that sequence."
                ),
                9: (
                    "Supplier-fixture evidence does not establish that every re"
                    "al supplier supports the same discovery and identity contr"
                    "act."
                ),
            }[chapter]
            solution_notes = old_guide.split("## Worked solution notes", 1)[-1].split(
                "## Classroom record", 1
            )[0]
            if "## Worked solution notes" not in old_guide:
                solution_notes = evidence
        chapter_root = EDITION / f"ch{chapter:02d}"
        index = f"""# Chapter {chapter} practicals

**Created:** 2026-09-09 · **Edition:** ninety-minute-v1 · **Doctrinal basis:** CLAUDE.md Rev 17

Two independent ninety-minute units: three hours of dedicated practice for this chapter.
The standard-library vocabulary, relevant Pydantic/SQLite introductions, worked conceptual
examples and frozen runtime are included in each notebook. Only basic Python is assumed.

| Unit | Main objective | Student notebook | Matching Markdown |
|---|---|---|---|
| A · 90 min | {titles[0]} | [Notebook](student/unit-a-v1.ipynb) | [Text](student/unit-a-v1.md) |
| B · 90 min | {titles[1]} | [Notebook](student/unit-b-v1.ipynb) | [Text](student/unit-b-v1.md) |

[Student chapter ZIP](ch{chapter:02d}-student-pack-v1.zip) ·
[Instructor chapter ZIP](ch{chapter:02d}-instructor-pack-v1.zip) ·
[Teaching guide](TEACHING-GUIDE.md) · [Course index](../START-HERE.md)

Use Python 3.14 and Pydantic 2; the setup cell explains installation if needed. No repository
checkout, earlier notebook kernel or live account is required. Unit B explicitly selects either
a supplied reference start or your saved Unit A handoff. It never credits reference work as your
own construction. Student NEEDS_WORK feedback is intentional until you implement the exercises.

The instructor folder contains worked notebook/Markdown counterparts and additional checks.
Retain your first prediction and attempt before consulting it. The planned timing is not a
measured completion guarantee; the teaching guide records how to observe actual learning.
"""
        (chapter_root / "README.md").write_text(index)
        guide = f"""# Chapter {chapter}: teach the mechanism, then test transfer

**Created:** 2026-09-09 · **Edition:** v1 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

{evidence}

Unit A: **{titles[0]}**. Unit B: **{titles[1]}**. Allocate ninety minutes to each,
excluding installation. Use both for the complete three-hour chapter practice. Each notebook
is independently runnable and includes all required introductions. A learner who starts with
Unit B uses a labelled reference artifact unless they explicitly select their Unit A work.
Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

Use a Python 3.14 kernel with Pydantic 2. Restart and run the instructor notebook on the teaching
machine before class. Check the retained output folder and selected input provenance. The notebook
contains the reviewed source files and makes no installation or provider request in its core.
Distribute the student ZIP. The instructor ZIP adds answers and holdouts; public answers are
pedagogically separated, not secret examination material.

Ask learners whether they can explain a dictionary, a function call and a loop. Those are the
baseline prerequisites. Do not ask whether they have “used SQLite” or “used Pydantic” and skip
the explanation based on a vague yes. Have them predict one actual validation or transaction
result. The embedded primers explain each API used; use the observed explanation to decide
whether they should reread or retrieve from memory.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–5 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 5–25 | Library and conceptual examples | Values and corrected explanations |
| 25–35 | Trace the API and actual caller | Input → learner code → observed output |
| 35–60 | A: construct/connect; B: reproduce/repair | Source and runtime observations |
| 60–80 | Implement the transfer task | Function, positive case, refusal and novel input |
| 80–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

The second unit revisits foundations as retrieval before repair. This is deliberate reinforcement,
not a claim that merely rerunning examples demonstrates understanding. If a learner needs the
worked answer during the timebox, retain their first attempt and distinguish supported repair
from independent construction. No exercise is silently dropped from the assignment.

## Misconception to surface

**{misconception}**

Ask the learner to name the exact field, predicate or event order responsible. Then keep every
other condition valid and change that one condition. Returning an error without preventing the
wrong effect, or producing a plausible summary without the right source row, does not settle
the question. Require one useful admitted case so refusing everything cannot pass.

## Progressive hints and worked reasoning

First ask for the authoritative inputs and expected invariant. Next point to the specific data
representation or callback boundary. Only then discuss control-flow structure. The notebook's
core hints are attached to its construction/repair cells, and the additional transfer task has
its own contract and visible feedback. Reveal instructor code only after collecting an attempt.

{solution_notes.strip()}

The additional task is **{BANK[chapter]["title"]}**:

{BANK[chapter]["reason"]}

The instructor notebook replaces the original learner-owned definitions before the main path
runs, then executes additional core and transfer cases. Those cases include independently authored
expectations. Ask learners to explain why their implementation handles a new case, rather than
asking them to memorize the reference code. An alternative implementation is valid if it meets
the same behavioral contract. For a source-mutation exercise, an alternative form may require
an explicitly adapted, still-unique mutation anchor; do not silently mutate a different boundary.

## Changed-case prompt and remediation

{new_case}

For a shape/type error, return to the smallest validation example. For an incorrect calculation,
write the quantities before discussing code. For a state error, draw before/event/after rows and
include an interrupted transition. For a connection error, replace the candidate temporarily
with a visibly different implementation and inspect whether the actual output changes. Keep
the negative observation as evidence, then restore the learner's implementation.

## Assessment rubric

Score each dimension 0, 1 or 2: absent/incorrect, correct with specific assistance, or independently
supported by execution and explanation. The following 8/10 readiness suggestion is a teaching
choice, not a validated measurement scale. Require full boundary credit before consequential work.

| Dimension | Evidence for two points |
|---|---|
| Prediction and revision | Prior prediction, actual observation and a causal revision |
| Construction or repair | Learner-owned code satisfies the declared positive and negative cases |
| Connection | Traces actual runtime output through the invoked learner code |
| Transfer | Handles a changed constraint and explains an independent new case |
| Evidence and limits | Retains provenance and distinguishes observations from stronger claims |

Untouched student notebooks intentionally contain unfinished work. Run All passing means the
artifact executes, not that the learner passes. The rubric needs a human assessment of the
explanation. Do not convert code-cell counts, prose length or green outputs into a quality score.

## Record actual classroom evidence

Record anonymous counts for setup success, first successful connection, highest hint used,
independent versus revealed-answer repair, novel transfer and recurring misconceptions. Record
actual minutes per stage and where learners needed prerequisite remediation. Keep unknown values
unknown. Use those observations to revise the next uniquely named edition.

**Surviving limitation:** {limitation}

Keep live-model, phone, container and supported-host extensions separate from the offline core's
completion claim. The student can finish this notebook without those environments; the notebook
does not claim to have verified them.
"""
        (chapter_root / "TEACHING-GUIDE.md").write_text(guide)
        rows.append(
            f"| {chapter} | {titles[0]} | {titles[1]} | [Open chapter](ch{chapter:02d}/README.md) |"
        )
    (EDITION / "START-HERE.md").write_text(
        """# Ninety-minute practicals for the complete book

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
"""
        + "\n".join(rows)
        + """

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
"""
    )
    print("Wrote sixteen chapter indexes and teaching guides plus the complete course index.")


if __name__ == "__main__":
    main()
