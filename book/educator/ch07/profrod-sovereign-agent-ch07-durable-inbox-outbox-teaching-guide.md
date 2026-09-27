# Chapter 7: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v1 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Build a durable work inbox".** Learners build `admit`. It works in one transaction and asks about identity first:

- a repeat of a known occurrence is a duplicate or a conflict, whatever the inbox holds;
- a new occurrence is refused, with nothing stored, once the open work reaches the capacity.

They connect `admit` to a morning of requests and a supplied worker. They then watch the database refuse finished work that tries to go back to pending.

**Unit B, "Finish with a report, and send across a lost reply".** Unit B starts from Unit A's file, in which the supplied worker finished Lucy's brief without keeping its answer. Learners:

- reproduce finished work with no report;
- build `finish`, which records the work and its report together and refuses any worker or state that the state machine does not allow;
- send the reports through a service that loses one reply.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own and includes all the introductions it needs.

A learner who starts with Unit B uses a labeled reference artifact unless they explicitly select their own Unit A work. Record that provenance. A reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

Use Google Colab or a local Python 3.12+ kernel. The notebooks need only the standard library.

- Before class, restart and run the worked notebook on the teaching machine, and check the retained `practical-work/ch07-a` and `ch07-b` folders.
- Distribute the student notebook and Markdown files. The solutions folder adds answers and holdouts. Public answers are kept apart for teaching reasons; they are not secret examination material.

Chapter 4's transaction pattern is the prerequisite: `BEGIN IMMEDIATE`, then `try`, then `ROLLBACK` on any exception, then `COMMIT`. Ask learners to write it from memory before Unit A's construction. Anyone who cannot should rerun Chapter 4, Unit A's transaction example first.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–5 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 5–25 | A: occurrences, triggers, Little's law. B: the two invariants and the network boundary | Values and corrected explanations |
| 25–35 | Trace the supplied observer and the caller | Input → learner code → observed file |
| 35–60 | A: construct `admit`. B: construct `finish` | Source and grade table |
| 60–70 | Connect to the morning (A) or drain and send (B) | Independent observation |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**Text is not identity.** "Count vanilla" at 9:00 and at 11:00 are two counts. Ask what the till should do after a restart that resets its counter, as in the chapter's Exercise 4.

**`INSERT OR IGNORE` is not duplicate handling.** It drops a conflicting request as silently as it drops a repeat. Ask the learner which of the two was a fault.

**Capacity before identity is backwards.** A full inbox that answers "refused" to Lucy's second tap has told her that queued work was not accepted.

**A transaction cannot include the network.** It can only roll back the shop's record of a send. The service keeps the message.

**Unknown is not failed.** It means "possibly delivered". Resending trades a missing report for a duplicate one, and Unit B's transfer task prices that trade.

Ask the learner to name the exact row, state or report responsible for an observation. Then keep every other condition valid and change only that one.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the invariant, and which rows must agree.
2. Point to the transaction boundary: where does it begin, and where must every exception go?
3. Only then discuss the structure of the control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, admit by promised minutes.** This keeps the identity rule, but the capacity becomes a size. The request's own minutes now count, and a request exactly at the budget fits.
- **Unit B, price a resend policy.** This is the chapter's derivation, which learners implement and check against cases enumerated by hand. The hint about $r = 1$ is deliberate: the closed form $(1 - r^k)/(1 - r)$ fails for an unreachable service, and the sum does not.

An alternative implementation is valid if it meets the same behavioural contract.

## Changed-case prompt and remediation

- **Unit A:** a request whose identity belongs to *finished* work arrives with different text. Is it a conflict? (Yes. Identity outlives the work.)
- **Unit B:** Chapter 12's recovery produces a second terminal result for work 3. What is the new report's identity, and why must `r3.1` not change?

For a state error, draw the before and after rows of both tables, including an interrupted change. For a connection error, temporarily replace the candidate with a visibly different implementation and check whether the observer's output changes. Keep the negative observation as evidence, then restore the learner's implementation.

## Assessment rubric

Score each dimension 0, 1 or 2:

- **0:** absent or incorrect;
- **1:** correct with specific assistance;
- **2:** independently supported by execution and explanation.

The suggested readiness threshold of 8/10 is a teaching choice, not a validated measurement scale.

| Dimension | Evidence for two points |
|---|---|
| Prediction and revision | Prior prediction, actual observation and a causal revision |
| Construction or repair | Learner-owned code satisfies the declared positive and negative cases |
| Connection | Traces the observer's output back through the invoked learner code |
| Transfer | Handles a changed constraint and explains an independent new case |
| Evidence and limits | Retains provenance and distinguishes observations from stronger claims |

Untouched student notebooks intentionally contain unfinished work. A passing Run All means the notebook executes, not that the learner passes. The rubric needs a human assessment of the explanation.

## Record actual classroom evidence

Record anonymous counts for:

- setup success;
- first successful connection;
- the highest hint used;
- independent versus revealed-answer construction;
- novel transfer;
- recurring misconceptions.

Also record the actual minutes spent per stage, and where learners needed prerequisite remediation. Keep unknown values unknown.

**Surviving limitation:** these units raise an exception inside one process and simulate the network. They do not kill the process, run two producers at once, or send to a real phone. The chapter's experiment measures Little's law on a real queue; Chapter 8 connects the real messaging service.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
