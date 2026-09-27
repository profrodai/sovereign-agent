# Chapter 2: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v2 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Construct typed shop tools".** Learners construct the complete tool factory. It must:

- reject duplicate product identities;
- isolate a copied stock snapshot;
- expose stock and supplier tools;
- make the draft quantity equal the current need.

It keeps strict Pydantic argument validation and USD integer-cents arithmetic. Learners compare a schema refusal, a business-rule refusal and a successful calculation, and connect `build_tools` to the same dispatcher the Chapter 3 loop uses. The unit saves the learner's source, with its hash, as the handoff.

**Unit B, "See what constrained decoding does to a distribution".** A colleague believes that a schema makes the model sample from its own distribution restricted to valid answers. Learners:

- construct token-by-token masked decoding on toy models small enough to enumerate;
- measure the gap between masking and conditioning as a trap strengthens, check conditioning against rejection sampling, and use a model with no trap as the negative control;
- in the transfer, compute the chance that retried unconstrained output is valid, and compare the two strategies.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own. Unit A needs Pydantic 2; Unit B needs only the standard library. A learner who starts with Unit B uses a labeled reference handoff unless they explicitly select their own Unit A work. Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

For Unit A, use a Python 3.14 kernel with Pydantic 2; for Unit B, Google Colab or any Python 3.12+ kernel. Before class, restart and run each worked notebook on the teaching machine, and check the retained `practical-work/ch02-a` and `ch02-b` folders. Neither core makes a provider request.

The prerequisites are dictionaries, functions and loops, plus Chapter 1's softmax for Unit B. Before Unit B, ask learners what a JSON schema changes about how a model writes. The share who say "the model checks its answer against the schema" tells you how long to spend on masking one token at a time.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–10 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 10–30 | A: Pydantic, strictness and refusals. B: masked softmax, conditioning and the trap model | Values and corrected explanations |
| 30–60 | A: construct and connect the tool factory. B: construct `masked` | Source and grade table |
| 60–70 | A: save the handoff. B: the gap against trap strength, with the negative control | Handoff; distance table |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**"An integer quantity is a correct quantity."** It can be schema-valid and still over-order. Ask which check refuses it, and where that check lives.

**"A schema makes the model sample from its own distribution, restricted to valid answers."** Masking commits one token at a time, so a likely prefix with mostly invalid continuations keeps its probability. In the trap model, masking gives "ay" 0.9 whatever the trap's strength.

**"Retrying is as good as constraining."** Only if failures are independent. The chapter's real failures were a habit, a code fence around every answer, which retries repeat.

**"Valid means right."** The chapter measured valid, schema-conforming answers with the wrong product or quantity. Unit A's checks and Chapter 15's evaluation catch those; the schema cannot.

Ask the learner to name the exact quantity responsible for an observation. Then keep every other condition fixed and change only that one. Require one useful case, a successful draft or a correct masked distribution, so that an implementation that refuses everything cannot pass.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the defining property: the key set and bounds, or which tokens may finish and which may continue.
2. Point to the single line or boundary that must change.
3. Only then discuss control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, use one reservation rule in reporting and drafting.** Available stock is on hand minus reserved. Substitute that into target minus available, then clamp at zero. Reusing the function stops a report from saying six while a draft validator demands four.
- **Unit B, retry instead of constraining.** `valid_within(per_token_error, tokens, attempts)` combines one attempt's validity over independent attempts, and refuses impossible inputs.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompts and remediation

- **Unit A:** try a changed stock snapshot, an empty catalog, duplicated identities and a `True` quantity. Record which boundary refuses each.
- **Unit B:** make a model in which masking and conditioning agree although some sequences are invalid. What property must it have?

For a numerical error, compute the case by hand first. For a claim about a distribution, ask which simulation would have shown it, and run it. For a connection error, temporarily swap in a visibly different implementation and check whether the output changes.

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
| Connection | Traces the measured table back through the invoked learner code |
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

**Surviving limitation:** Unit A's tools check the requests they receive, not whether the model chose the right tool. Unit B's toy models are small enough to enumerate; a real grammar allows thousands of tokens per step, and how much its distortion matters depends on the model and the schema.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
