# Chapter 18: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v2 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Construct operating and restoring".** Learners construct restore from a separate, compatible backup. The restore must:

- verify integrity and schema;
- prepare a fresh epoch;
- clear old ownership and revoke approvals;
- pause, publish the authority marker, and copy into the same database inode.

They back up real queued work, restore it, and attempt a claim through the normal worker API before and after an explicit decision to reconcile and resume. The unit saves the learner's restore source, with its hash, as the handoff.

**Unit B, "Plan memory and latency from the architecture".** A colleague estimated the key-value cache using every attention head. Learners:

- derive the cache from a model's configuration, including grouped-query attention and a declared head dimension;
- predict each local model's decode rate after a 2,000-token prompt, from the cache and a bandwidth fitted on other runs, and check it against the recorded measurements, with the colleague's formula as the negative control;
- in the transfer, write a nearest-rank percentile that does not change its input, and read the recorded latency tail.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own. Unit A needs Pydantic 2; Unit B needs only the standard library, and embeds the chapter's recorded measurements. A learner who starts with Unit B uses a labeled reference handoff unless they explicitly select their own Unit A work. Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

For Unit A, use a Python 3.14 kernel with Pydantic 2; for Unit B, Google Colab or any Python 3.12+ kernel. Before class, restart and run each worked notebook on the teaching machine, and check the retained `practical-work/ch18-a` and `ch18-b` folders. Neither core makes a provider request or a network call.

The prerequisites are dictionaries, functions and loops. For Unit B, ask learners what happens to a model's memory use as a conversation grows. The share who answer "nothing, the model is fixed" tells you how long to spend on attention and the cache before the formula.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–10 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 10–30 | A: backups, epochs and authority. B: decode, the bandwidth fit and the cache | Values and corrected explanations |
| 30–60 | A: construct and connect restore. B: construct `kv_cache_bytes` | Source and grade table |
| 60–70 | A: save the handoff. B: predict long-context decode, with the negative control | Handoff; prediction table |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**"Pausing the old database is enough."** Not if the copied snapshot itself is unpaused. Ask which record carries the authority.

**"Every head stores keys and values."** Only KV heads do. The colleague's estimate is six times too large for `qwen2.5:1.5b`, and its prediction of the long-context decode rate misses by 11%.

**"One passing case validates a formula."** For `qwen3:0.6b`, the colleague's two errors cancel, so their per-token figure is right. Ask learners to find why before revealing it.

**"A fitted formula that matches its fitted runs is validated."** Two parameters always fit two runs. The evidence is the decode rate after a long prompt, which the fit never saw.

**"p99 of thirty requests is a tail estimate."** It is the maximum, one observation.

Ask the learner to name the exact quantity responsible for an observation. Then keep every other condition fixed and change only that one. Require one useful case, a successful restore or a prediction within tolerance, so that refusing or rejecting everything cannot pass.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the defining property: the authority epoch, which heads store keys and values, or the rank of a percentile.
2. Point to the single line or boundary that must change.
3. Only then discuss control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, validate every member of a restore manifest.** Checking only the observed files misses an absent member, and checking only the expected files misses an unexpected one. Exact set equality plus value comparison establishes this narrow integrity contract.
- **Unit B, report the latency tail.** `percentile(values, q)` sorts a copy, takes the value at rank $\lceil qn/100 \rceil$, and refuses empty input or a $q$ outside $(0, 100]$.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompts and remediation

- **Unit A:** retain backup hashes, repeat the restore, compare authority epochs, and test same-path or missing backups. A failed preflight must preserve live work.
- **Unit B:** with an 8-bit cache, how many 8,192-token sequences of `qwen3:0.6b` fit beside its weights in 16 GB? Compute it by hand, then with the function.

For a numerical error, compute the case by hand first. For a claim about a real server, ask which measurement the formula did not see, and check the formula against it. For a connection error, temporarily swap in a visibly different implementation and check whether the output changes.

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

**Surviving limitation:** Unit A's local exercise proves no host reboot or external supplier reconciliation. Unit B's measurements come from one machine, one server version and an idle afternoon: they show how the costs scale, not another machine's numbers or a loaded server's tail.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
