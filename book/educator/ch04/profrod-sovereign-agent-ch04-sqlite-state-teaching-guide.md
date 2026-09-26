# Chapter 4: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v1 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

Unit A builds `apply_event`: an event and its stock change in one transaction, a replay treated as a duplicate, a reused identity refused, and nothing left behind when anything raises. Learners connect it to a day of the shop and check the invariant, stock equals the sum of events, with an independent reader. Unit B reproduces a schema migration that stops half-way, shows why the rerun fails, and builds `migrate`, which commits every missing migration together with its version and refuses a newer file first.

Unit A: **Construct a durable state store**. Unit B: **Diagnose an interrupted migration and repair it**. Allocate ninety minutes to each. Use both for the complete three-hour chapter practice. Each notebook is independently runnable and includes all required introductions. A learner who starts with Unit B uses a labeled reference artifact unless they explicitly select their Unit A work. Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

Use Google Colab or a local Python 3.12+ kernel; the notebooks need only the standard library. Restart and run the worked notebook on the teaching machine before class, and check the retained `practical-work/ch04-a` and `ch04-b` folders. Distribute the student notebook and Markdown files. The solutions folder adds answers and holdouts; public answers are pedagogically separated, not secret examination material.

Ask learners whether they can explain a dictionary, a function call and an exception. Those are the baseline prerequisites. Do not ask whether they have "used SQL" and skip the introduction on a vague yes. Have them predict one actual result instead: what a second connection finds after a stop between two writes.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–5 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 5–25 | SQLite, constraints, transactions and `with` | Values and corrected explanations |
| 25–35 | Trace the supplied observer and the caller | Input → learner code → observed file |
| 35–60 | A: construct/connect; B: reproduce/repair | Source and independent observations |
| 60–80 | Implement the transfer task | Function, positive case, refusal and novel input |
| 80–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

Unit B revisits Unit A's transaction rule as retrieval before repair. This is deliberate reinforcement, not a claim that rerunning examples demonstrates understanding. If a learner needs the worked answer during the timebox, retain their first attempt and distinguish supported repair from independent construction.

## Misconceptions to surface

**A rollback is not recovery.** It makes an unfinished group invisible; the failure still reaches the caller, who must still learn that the delivery was not recorded. Ask: after the rollback, who knows the delivery happened?

**A duplicate is not harmless because "the row already exists".** Idempotence comes from the identity the caller chose before the first attempt. The same delivery reported with a fresh identity would double the stock.

**A half-applied migration cannot be resumed from its error.** After the hasty version stops, the file's version and its structure disagree, and no rule in the program can tell which statements ran. The repair makes that state impossible.

Ask the learner to name the exact statement, row or version responsible. Then keep every other condition valid and change that one condition.

## Progressive hints and worked reasoning

First ask for the invariant and which rows must agree. Next point to the transaction boundary: where does it begin and where must every exception go? Only then discuss control-flow structure. The notebook's hints are attached to the construction and repair cells, and the transfer task has its own contract and visible feedback. Reveal instructor code only after collecting an attempt.

The transfer tasks isolate the decision from the storage. Unit A's **decide an append without a database** is the chapter's append function: look up the identity, then compare content. Unit B's **plan migrations for any owner** is the version line: refuse a newer file, do nothing when equal, otherwise every version after the current one. Ask learners to explain why their implementation handles a new case rather than memorizing the reference code. An alternative implementation is valid if it meets the same behavioural contract.

## Changed-case prompt and remediation

Unit A: a delivery for a product the shop has never stocked, reported twice, the second time with a stop between the writes. What does the observer find? Unit B: a second owner, `memory`, with its own two migrations, on a file whose stock tables are already version 2.

For a state error, draw before and after rows for both tables, including an interrupted change. For a connection error, replace the candidate temporarily with a visibly different implementation and inspect whether the observer's output changes. Keep the negative observation as evidence, then restore the learner's implementation.

## Assessment rubric

Score each dimension 0, 1 or 2: absent or incorrect, correct with specific assistance, or independently supported by execution and explanation. The following 8/10 readiness suggestion is a teaching choice, not a validated measurement scale.

| Dimension | Evidence for two points |
|---|---|
| Prediction and revision | Prior prediction, actual observation and a causal revision |
| Construction or repair | Learner-owned code satisfies the declared positive and negative cases |
| Connection | Traces the observer's output back through the invoked learner code |
| Transfer | Handles a changed constraint and explains an independent new case |
| Evidence and limits | Retains provenance and distinguishes observations from stronger claims |

Untouched student notebooks intentionally contain unfinished work. Run All passing means the artifact executes, not that the learner passes. The rubric needs a human assessment of the explanation.

## Record actual classroom evidence

Record anonymous counts for setup success, first successful connection, highest hint used, independent versus revealed-answer repair, novel transfer and recurring misconceptions. Record actual minutes per stage and where learners needed prerequisite remediation. Keep unknown values unknown.

**Surviving limitation:** these units raise an exception inside one process. They do not stop the process, cut power or test a disk that acknowledges a flush it has not performed; the chapter's experiment adds a real process death, and the rest rests on SQLite's documentation.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
