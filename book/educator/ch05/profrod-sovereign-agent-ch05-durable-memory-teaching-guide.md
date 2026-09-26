# Chapter 5: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Created:** 2026-09-26 · **Edition:** v2 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Construct durable memory".** Learners build bounded retrieval from `assistant_preferences`. It must:

- select only this session and active revisions;
- rank by case-insensitive word overlap, breaking ties by newest identity;
- preserve provenance.

They remember, correct, close and reopen SQLite, invoke `context`, and inspect the actual system message the model sees. The unit saves the learner's source, with its hash, as the handoff.

**Unit B, "Measure a retriever before trusting it".** The colleague's search in Unit B is Unit A's ranker: word overlap. Learners:

- construct BM25 from its three ideas: inverse document frequency, saturation, and length normalization;
- evaluate BM25, word overlap and newest-first on the chapter's forty notes and sixteen labeled questions, with newest-first as the negative control, and separate direct questions from paraphrases;
- in the transfer, implement mean reciprocal rank, and reconcile BM25's better recall with overlap's slightly better MRR.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own. Unit A needs Pydantic 2; Unit B needs only the standard library. A learner who starts with Unit B uses a labeled reference handoff unless they explicitly select their own Unit A work. Record that provenance; a reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

For Unit A, use a Python 3.14 kernel with Pydantic 2; for Unit B, Google Colab or any Python 3.12+ kernel. Before class, restart and run each worked notebook on the teaching machine, and check the retained `practical-work/ch05-a` and `ch05-b` folders. Neither core makes a provider request.

The prerequisites are dictionaries, functions and loops, plus a logarithm for Unit B. Before Unit B, show learners one paraphrase: "At what hour should the supplier's van turn up?" Ask which of Lucy's notes answers it, and how a program could know. The answers tell you whether to spend time on why words are not meanings.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–10 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 10–30 | A: preferences, provenance and budgets. B: ranking metrics and BM25's three ideas | Values and corrected explanations |
| 30–60 | A: construct and connect retrieval. B: construct `bm25_scores` | Source and grade table |
| 60–70 | A: save the handoff. B: evaluate three rankers, with the negative control | Handoff; recall table |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**"Putting the new preference first removes the old guidance."** It does not remove contradictory old guidance. Ask which record the model still sees.

**"It worked on every question I tried."** The questions a developer thinks of share words with the notes, because the developer wrote both. Only labeled questions that include paraphrases test a retriever honestly.

**"BM25 understands the request."** It weights rare words and discounts long notes; it does not match meaning. No lexical ranker finds a paraphrase that shares no useful word.

**"Better MRR means a better retriever."** For an agent that sends three notes, whether the note is among them matters more than its order. Choose the metric by how the ranking is used.

Ask the learner to name the exact quantity responsible for an observation. Then keep every other condition fixed and change only that one. Require one useful case, a retrieved preference or a found note, so that an implementation that returns nothing cannot pass.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask for the defining property: the session boundary, the idf of a term in every note, or the position of the first relevant note.
2. Point to the single line or boundary that must change.
3. Only then discuss control flow.

The notebook's hints sit with the construction cells. Reveal instructor code only after collecting an attempt.

The transfer tasks change one constraint:

- **Unit A, retrieve the newest eligible memory under a limit.** Filtering excludes foreign and superseded rows before the budget is spent. A valid empty result differs from an invalid requested limit, and deterministic ordering makes a repeated retrieval explainable.
- **Unit B, mean reciprocal rank.** `mean_reciprocal_rank(rankings, relevant_sets)` averages one over the first relevant position, and refuses unpaired or empty input.

An alternative implementation is valid if it meets the same behavioral contract.

## Changed-case prompts and remediation

- **Unit A:** correct twice, forget one key and introduce another session with the same preference name. Prove that no stale or foreign value reaches the context.
- **Unit B:** with $b = 0$, which of the visible cases changes, and why? Predict it from the formula, then run it.

For a numerical error, compute the case by hand first. For a claim about retrieval, ask which labeled question would have shown the failure, and run it. For a connection error, temporarily swap in a visibly different implementation and check whether the output changes.

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

**Surviving limitation:** Forgetting future context is not secure erasure of backups or past provider requests. Unit B's sixteen labeled questions show how lexical ranking fails, not how often it would fail on Lucy's real requests.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
