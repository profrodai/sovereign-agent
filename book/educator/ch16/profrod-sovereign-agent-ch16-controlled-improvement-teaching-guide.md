# Chapter 16: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v2 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Construct controlled improvement".** Learners build the activation of a staged, immutable skill. It must:

- require named positive cases;
- detect candidate mutation;
- compare the active configuration after evaluation;
- atomically activate the intended version.

They evaluate outside the write transaction, deliberately activate another skill inside the callback, then inspect the active snapshot. The unit saves the learner's source, with its hash, as the handoff.

**Unit B, "Predict the winner's curse, then learn from preferences".** A colleague kept the best of sixteen procedures on a thirty-case evaluation and reported its score as the expected production score. Learners:

- construct the expected maximum of $k$ normal draws by numerical integration, checked against the closed forms for $k = 2$ and $k = 3$;
- predict the colleague's inflation as $\sigma \cdot \mathbb{E}[\max_{16}]$ and check it against simulation, with a single candidate as the negative control;
- in the transfer, implement the Bradley–Terry gradient, wins minus expected wins, which is the signal a reward model is trained on.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own. Unit A needs Pydantic 2; Unit B needs only the standard library. A learner who starts with Unit B uses a labeled reference handoff unless they explicitly select their own Unit A work. Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

For Unit A, use a Python 3.14 kernel with Pydantic 2; for Unit B, Google Colab or any Python 3.12+ kernel. Before class, restart and run each worked notebook on the teaching machine, and check the retained `practical-work/ch16-a` and `ch16-b` folders. Neither core makes a provider request.

The prerequisites are dictionaries, functions and loops, plus Chapter 15's standard error for Unit B. Before Unit B, ask learners what score they would expect from the best of sixteen coin-flipping candidates. The share who answer "0.5" tells you how long to spend on selection as a maximum.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–10 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 10–30 | A: proposals, evaluation and activation. B: the maximum of $k$ draws | Values and corrected explanations |
| 30–60 | A: construct and connect activation. B: construct `expected_max_normal` | Source and grade table |
| 60–70 | A: save the handoff. B: predicted and simulated inflation, with the negative control | Handoff; prediction table |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**"A passing callback describes the current configuration."** It can describe an obsolete one. Ask which comparison belongs inside the activation transaction.

**"The best score is our best estimate."** It is the best estimate of the luckiest candidate. Sixteen equal candidates on thirty cases produce a winner reporting about 0.66 for a true 0.5.

**"More cases remove the curse."** They shrink it as $1/\sqrt{n}$; more candidates grow it again. Only a holdout removes it.

**"A reward model is the truth."** It is a Bradley–Terry fit to finite, noisy preferences, and optimizing against it is selection against a measurement. That is reward hacking.

Ask the learner to name the exact quantity responsible for an observation. Then keep every other condition fixed and change only that one. Require one useful case, a valid activation or a matched prediction, so that an implementation that refuses everything cannot pass.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the defining property: complete current evidence, the density of the maximum, or wins minus expected wins.
2. Point to the single line or boundary that must change.
3. Only then discuss control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, admit activation only against complete current evidence.** Empty coverage and truthy non-booleans are not positive evidence. A complete positive evaluation can still be stale, and the final equality belongs in the activation transaction.
- **Unit B, the Bradley–Terry gradient.** `bt_gradient(comparisons, ratings)` adds each comparison's surprise to its winner and subtracts it from its loser, and refuses impossible pairs.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompts and remediation

- **Unit A:** try missing cases, `False` and integer one, candidate mutation, explicit stale state and a concurrent activation. Preserve the valid uncontended case.
- **Unit B:** make one of the sixteen candidates truly better, at 0.6. How many cases before it is chosen more than 80% of the time? Predict with Chapter 15's sample-size reasoning, then simulate.

For a numerical error, compute the case by hand first. For a statistical claim, ask which simulation would have shown it, and run it. For a connection error, temporarily swap in a visibly different implementation and check whether the output changes.

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

**Surviving limitation:** Unit A's authored callbacks exercise state control; they are not a substitute for live regression evidence. Unit B's simulations assume equally good candidates and independent cases; when one candidate is truly much better, the curse is smaller, as the chapter's measured prompt search shows.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
