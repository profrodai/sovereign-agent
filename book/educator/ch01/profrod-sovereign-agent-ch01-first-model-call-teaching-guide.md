# Chapter 1: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v2 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Build softmax and a sampler from scratch".** Learners implement two functions:

- a numerically stable softmax with temperature, greedy at $T = 0$;
- an inverse-transform sampler.

They test the sampler the way a statistician would: a chi-square statistic over thousands of draws, plus a negative control that must fail. Then they generate Lucy's notes at three temperatures and check the derived $dH/dT = \mathrm{Var}(z)/T^3$ against a numerical derivative of their own softmax.

**Unit B, "Diagnose a misleading model comparison".** It starts from Unit A's tokenizer. A colleague chose a tokenizer by per-token perplexity on training text. Learners:

- reproduce that choice;
- build `bits_per_character`;
- show that held-out bits per character choose differently: the tokenizer with the most merges wins on training text and loses on held-out text.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own, with the standard library only. A learner who starts with Unit B uses a labeled reference tokenizer unless they explicitly select their own Unit A handoff. Record that provenance.

## Prepare and rehearse

Use Google Colab or a local Python 3.12+ kernel. Before class, restart and run the worked notebook on the teaching machine, and check the retained `practical-work/ch01-a` and `ch01-b` folders.

The prerequisites are functions, lists, dictionaries and loops. No probability beyond "probabilities are nonnegative and sum to one" is assumed. Ask learners to compute softmax of three small logits with a calculator before they write any code. The number of learners who get $e^{z}$ normalization right unaided tells you how long to spend on the derivation.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–10 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 10–30 | A: tokens, logits, entropy. B: likelihood, cross-entropy and the colleague's comparison | Values and corrected explanations |
| 30–60 | A: construct `softmax` and `sample`. B: construct `bits_per_character` | Source and grade table |
| 60–70 | A: generate and measure. B: choose a tokenizer fairly | Measured table |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**"Softmax is just normalizing."** Dividing logits by their sum fails for negative logits. The exponential is what turns a difference of scores into a ratio of probabilities. Ask the learner to derive softmax from "logit differences are log-odds".

**"Temperature 0 makes a model deterministic."** It does in the notebook. On a real server, batching and parallel reductions reorder floating-point additions, and the chapter's receipt shows two greedy runs of the same model and prompt disagreeing.

**"The sampler looks right."** A uniform sampler produces plausible-looking text too. Only a statistical test with a negative control separates correct from plausible. Also point out the multiple-comparisons trap. Among hundreds of tokens, one will deviate by more than three standard errors by chance, which is why the chi-square test considers them together.

**"Lower perplexity is better."** Only on the same text with the same tokenizer. Across tokenizers, compare bits per character; across training and held-out text, trust only held-out.

Ask the learner to name the exact quantity responsible for an observation. Then keep every other condition fixed and change only that one.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the defining property: sums to one, invariant to a shift, the probability of each index.
2. Point to the single line that must change.
3. Only then discuss control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, min-p sampling.** A truncation rule whose threshold moves with the top probability, unlike top-p's fixed mass.
- **Unit B, bits per character from a real model.** Natural-log log-probabilities, with no access to weights, which is how lab evaluations of closed models work.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompts and remediation

- **Unit A:** at what temperature does min-p with ratio 0.1 keep exactly one token after "."? Compute it before running it.
- **Unit B:** take the chapter's live receipt and compute the real model's bits per character on its own answer. Then explain why it still cannot be compared with the bigram model: the texts differ.

For a numerical error, compute the case by hand first. For a statistical claim, ask what a broken implementation would have shown, and run it.

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

**Surviving limitation:** the units measure a model the learner can read completely. The chapter's experiment adds a real model through its log-probabilities; the units do not run one.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
