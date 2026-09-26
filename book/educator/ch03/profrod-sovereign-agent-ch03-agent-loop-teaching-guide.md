# Chapter 3: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v2 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Build a bounded model and tool loop".** Learners implement the admission decision that governs every model call and connect it to the chapter's loop and a real Chapter 2 tool dispatcher. The evidence is a trace of model admission, actual tool observations and terminal counters. A failed admitted attempt is still charged, and a repeated call identity is refused. The unit saves the bounded transcript as its handoff.

**Unit B, "Test a reliability claim against simulation".** A colleague estimated the agent's reliability as $p^{n}$ and assumed independent retries. Learners:

- derive the success probability of a loop that recovers from errors, as a two-state Markov chain, and implement its closed form;
- test the formula against 20,000 simulated agents per setting with a z-score, and use the colleague's $p^{n}$ as a negative control that the test must reject;
- in the transfer, measure from retry data whether retries are independent: the retry-after-failure rate, compared with the first-attempt rate.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own. Unit A needs Pydantic 2; Unit B needs only the standard library. A learner who starts with Unit B uses a labeled reference transcript unless they explicitly select their own Unit A handoff. Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

For Unit A, use a Python 3.14 kernel with Pydantic 2; for Unit B, Google Colab or any Python 3.12+ kernel. Before class, restart and run each worked notebook on the teaching machine, and check the retained `practical-work/ch03-a` and `ch03-b` folders. Neither core makes a provider request.

The prerequisites are dictionaries, functions and loops. Unit B adds two facts about probability: the probabilities of disjoint events add, and those of independent events multiply. Before Unit B, ask learners to compute $0.95^{20}$ with a calculator and say what it means. Then ask what changes if an error can be repaired on the next step. The share who answer the second question in terms of states rather than retries tells you how long to spend on the Markov chain.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–10 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 10–30 | A: transcripts and admission. B: compounding, half-life and the recovery chain | Values and corrected explanations |
| 30–60 | A: construct and connect admission. B: construct `success_with_recovery` | Source and grade table |
| 60–70 | A: save the bounded transcript. B: test against simulation, with the negative control | Handoff; z-score table |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**"A provider failure costs nothing."** A failed admitted attempt still consumes a call and its configured exposure. Otherwise a repeatedly failing provider appears free and can evade the bound.

**"95% per step means 36% over 20 steps."** Only if one error ends the task. With recovery rate $r$, success levels off at $\pi = r/(1 - p + r)$ instead of falling to zero. The loop, not the model, sets $r$. A clear refusal shown to the model raises it; a silent failure keeps it at zero. This is what connects the two units: Unit A's statuses and observations are what make $r > 0$ possible.

**"The simulation agreed, so the formula is true."** The agreement shows only that the formula describes the simulator, whose steps are identical and memoryless. The chapter's measured run found a real model's errors concentrated in one step whose difficulty grows with $n$. Ask what observation would distinguish the two.

**"More retries converge to certainty."** Only when no task is hard for the model. The signature of a hard fraction is a retry-after-failure rate below the first-attempt rate. The chapter's run measured 4/26 against 14/40.

Ask the learner to name the exact quantity responsible for an observation. Then keep every other condition fixed and change only that one. Require either one useful admitted case or one setting with $r = 0$, so that an implementation that refuses or rejects everything cannot pass.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the defining property: the invariant, the fixed point, or which tasks count.
2. Point to the single line or boundary that must change.
3. Only then discuss control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, admit a variable-cost next model attempt.** `transfer_check(state)` returns:
  - CALL_LIMIT first, when `calls >= max_calls`;
  - otherwise COST_LIMIT, when `spent + next_cost > budget`;
  - otherwise CALL.

  Equality at the money boundary is allowed, and the next-cost estimate can differ on every attempt.
- **Unit B, are retries independent?** `retry_after_failure(outcomes)` conditions on a failed first attempt that was retried, and refuses data that cannot answer the question.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompts and remediation

- **Unit A:** with calls and budget both exhausted, which refusal does the loop report, and why must that precedence be declared?
- **Unit B:** at $p = 0.9$, what recovery rate $r$ keeps a 50-step task above 80%? Solve $\pi \ge 0.8$ by hand, then check with the formula.

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

**Surviving limitation:** Unit A's authored replay demonstrates loop behavior, not how often a live model chooses that sequence. Unit B's simulators have memoryless, identical steps. The chapter's experiment measures a real model; the units do not run one.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
