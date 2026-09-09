# Chapter 6: teach the mechanism, then test transfer

**Created:** 2026-09-09 · **Edition:** v1 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

Implement the owned poll transaction: validate the bounded update batch and lease, admit only allowlisted human private messages with matching sender/chat identity, deduplicate origins, and advance the cursor after durable intake. Use the real poll function and SQLite cursor with a fixture bot; reopen the database and replay an unordered batch.

Unit A: **Construct private messaging**. Unit B: **Break, repair and transfer private messaging**. Allocate ninety minutes to each,
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

**Checking only the sender allows a group message into a private session.**

Ask the learner to name the exact field, predicate or event order responsible. Then keep every
other condition valid and change that one condition. Returning an error without preventing the
wrong effect, or producing a plausible summary without the right source row, does not settle
the question. Require one useful admitted case so refusing everything cannot pass.

## Progressive hints and worked reasoning

First ask for the authoritative inputs and expected invariant. Next point to the specific data
representation or callback boundary. Only then discuss control-flow structure. The notebook's
core hints are attached to its construction/repair cells, and the additional transfer task has
its own contract and visible feedback. Reveal instructor code only after collecting an attempt.

Inspect the lease before writes, validate identities by exact integer type, use the existing _enqueue helper, and persist the highest offset after the whole batch.

The additional task is **Plan private intake across accounts and replays**:

The origin is account plus update ID. Private-chat admission precedes creation of work. A replayed transport batch can contain both old and new eligible updates; neither blanket acceptance nor blanket refusal implements that distinction.

The instructor notebook replaces the original learner-owned definitions before the main path
runs, then executes additional core and transfer cases. Those cases include independently authored
expectations. Ask learners to explain why their implementation handles a new case, rather than
asking them to memorize the reference code. An alternative implementation is valid if it meets
the same behavioral contract. For a source-mutation exercise, an alternative form may require
an explicitly adapted, still-unique mutation anchor; do not silently mutate a different boundary.

## Changed-case prompt and remediation

Change account, actor, update order, chat kind and message length. A rejected batch must not partially move the cursor or create work.

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

**Surviving limitation:** Offline intake proves neither Telegram authentication nor phone delivery.

Keep live-model, phone, container and supported-host extensions separate from the offline core's
completion claim. The student can finish this notebook without those environments; the notebook
does not claim to have verified them.
