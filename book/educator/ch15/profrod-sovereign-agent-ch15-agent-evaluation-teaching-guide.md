# Chapter 15: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v2 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Construct evaluation".** Learners construct the independent replenishment baseline over a `Case`. It must:

- use physical minus reserved stock;
- include only actual deficits;
- retain product identity;
- make no model call.

They then feed the same case through `evaluate` with `OfflineShopModel`, and compare the authored expected quantities with both the baseline and the real tool observations. The unit saves the learner's baseline source, with its hash, as the handoff.

**Unit B, "Put error bars on an evaluation".** A colleague claims that 16 of 16 means "100% reliable", and that 12 of 14 against 10 of 14 is a 14-point improvement. Learners:

- construct the Wilson interval from the score test;
- check its exact coverage against Wald's, with Wald as the negative control the check must reject;
- run their Unit A baseline on 200 generated cases, and state what 200 clean runs can claim;
- in the transfer, implement McNemar's exact paired test, and measure how little a fourteen-case suite can detect.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own. Unit A needs Pydantic 2; Unit B needs only the standard library. A learner who starts with Unit B uses a labeled reference baseline unless they explicitly select their own Unit A handoff. Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

For Unit A, use a Python 3.14 kernel with Pydantic 2; for Unit B, Google Colab or any Python 3.12+ kernel. Before class, restart and run each worked notebook on the teaching machine, and check the retained `practical-work/ch15-a` and `ch15-b` folders. Neither core makes a provider request.

The prerequisites are dictionaries, functions and loops. For Unit B, learners also need to know what a probability and an average are. Before Unit B, ask learners what 16 of 16 proves. The share who answer "that it never fails" tells you how long to spend on the rule of three before the Wilson derivation.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–10 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 10–30 | A: authored answers and the harness. B: standard error, Wald, the rule of three | Values and corrected explanations |
| 30–60 | A: construct and connect the baseline. B: construct `wilson_interval` | Source and grade table |
| 60–70 | A: save the handoff. B: exact coverage, with the negative control | Handoff; coverage table |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**"The baseline is obviously right."** Ignoring reservations makes the supposedly simpler baseline wrong, while the agent can still be right. Ask which field is responsible.

**"16 of 16 means 100%."** It means the failure rate is probably below about 19%. Error bars are widest, relative to what is left to improve, exactly when a system looks perfect.

**"A 95% interval is right 95% of the time."** Only if it keeps its promise. At sixteen cases and a true rate of 95%, the Wald interval contains the truth 56% of the time; the learner's own coverage table shows it.

**"Subtract the two scores."** Two candidates on the same cases should be compared case by case. Only the disagreements carry evidence, and three disagreements to one gives $p = 0.625$.

**"Repeat each case to get a bigger n."** Repeats measure variability on a case; they do not add cases.

Ask the learner to name the exact quantity responsible for an observation. Then keep every other condition fixed and change only that one. Require one useful case: an admitted deficit in Unit A, or a rejected Wald interval in Unit B. Otherwise an implementation that refuses or rejects everything could pass.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the defining property: the authored answer, the score-test inequality, or which cases are discordant.
2. Point to the single line or boundary that must change.
3. Only then discuss control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, build an oracle that cannot copy the expected answer.** Expected values are authored before candidate execution. Removing the expected-answer field from the candidate interface makes that shortcut unavailable, while changed identities challenge fixture lookup.
- **Unit B, compare two candidates on the same cases.** `mcnemar(first, second)` counts discordant cases and sums the exact binomial tail, and refuses unpaired input.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompts and remediation

- **Unit A:** use an empty catalog, an exact threshold, renamed products and high reservations. A visible-case lookup and an implementation returning `case.expected` must fail.
- **Unit B:** how many clean runs are needed before the Wilson interval excludes a failure rate of 1%? Estimate it with the rule of three first, then find it with the function.

For a numerical error, compute the case by hand first. For a statistical claim, ask what a broken implementation would have shown, and run it. For a connection error, temporarily swap in a visibly different implementation and check whether the output changes.

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

**Surviving limitation:** A passing finite scenario suite is not proof of arbitrary language faithfulness. Unit B's intervals assume independent cases drawn from the population of interest. A suite of hand-written cases is not a random sample of Lucy's future requests, and no interval corrects for that.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
