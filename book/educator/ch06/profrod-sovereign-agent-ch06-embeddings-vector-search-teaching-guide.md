# Chapter 6: teach the mechanism, then test transfer

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).


**Created:** 2026-09-27 · **Edition:** v1 · **Review:** classroom outcomes unobserved

## Goals and the evidence to collect

**Unit A, "Build embeddings and a vector store".** It grew out of the vector-databases lab first taught live in the ITAM class of September 24, 2026. Learners:

- see that a word's index and a one-hot vector say nothing about meaning, and that the embedding lookup is a matrix product;
- follow one real training step of skip-gram with negative sampling, then train two numbers per word on Lucy's twelve notes;
- pool word vectors into one unit vector per note, and check that cosine, dot product and distance agree;
- build `search`, which ranks only current notes, refuses vectors from another model and returns the best first;
- search Lucy's index, including a delivery rule that has changed.

**Unit B, "Evaluate and repair retrieval".** Starting from Unit A's index, learners build `evaluate` (recall@k and reciprocal rank) and measure three retrievers on six direct questions and six paraphrases: BM25, their own vectors, and `all-minilm`, whose real vectors ship in the notebook. On paraphrases, `all-minilm` reached recall@2 0.917, BM25 0.333, and the learner's vectors 0: they could not rank any of the six, because they know only the notes' twenty-four words. The transfer task weights a fusion of rankings; on these questions no weight tried matched `all-minilm` alone on paraphrases.

Allocate ninety minutes to each unit; together they make the complete three-hour chapter practice. Each notebook runs on its own and includes all the introductions it needs.

A learner who starts with Unit B uses a labeled reference index unless they explicitly select their own Unit A work. Record that provenance. A reference start is useful study, not evidence of earlier construction.

## Prepare and rehearse

Use Google Colab or a local Python 3.12+ kernel. The notebooks need only the standard library: no model server, download or API key.

- Before class, restart and run the worked notebook on the teaching machine, and check the retained `practical-work/ch06-a` and `ch06-b` folders.
- Distribute the student notebook and Markdown files. The solutions folder adds answers and holdouts. Public answers are kept apart for teaching reasons; they are not secret examination material.
- For a live extension, the original class lab's optional Chroma section embeds the same notes with Chroma's default model, `all-MiniLM-L6-v2`, which is the model whose vectors Unit B ships. It needs `pip install chromadb` in Colab and a one-time download.

Chapter 5's BM25 and its ranking of notes are the prerequisite. Ask learners to say, before Unit A, why BM25 cannot find a note that uses different words.

## Ninety-minute sequence for each unit

| Clock | Facilitation | Observable evidence |
|---|---|---|
| 0–5 | Read the concrete goal; commit to a prediction | Prediction and proposed falsifier |
| 5–30 | A: one-hot, the lookup, a training step, pooling and distances. B: the two metrics by hand and one paraphrase per retriever | Values and corrected explanations |
| 30–60 | A: construct `search`. B: construct `evaluate` | Source and grade table |
| 60–70 | Build and search Lucy's index (A) or measure three retrievers (B) | Independent observation |
| 70–85 | Implement the transfer task | Function, positive case, refusal and novel input |
| 85–90 | Retrieve, save and explain | Evidence, exit ticket and remaining limit |

## Misconceptions to surface

**A close index means a close meaning.** "vanilla" and "vegan" are neighbors in the alphabet and nowhere else.

**A superseded note is a worse note.** It is a wrong one. The Monday delivery note stays near "supplier delivers tubs"; only the current flag keeps it out.

**A mismatched vector just scores low.** A cosine between two models' vectors is a number with no meaning, and it can be high. `search` must refuse.

**Recall is whether we found it.** With two relevant notes, one found is half the job. Reciprocal rank looks down the whole ranking, not only the top $k$.

**More training fixes the paraphrases.** The learner's vectors failed on paraphrases because the words were never seen. More epochs on twelve notes cannot add a word; a model trained on a billion pairs can.

## Progressive hints and worked reasoning

Give help in this order:

1. Ask which rows or questions take part, before any arithmetic.
2. Ask what the function must refuse, and what it must never change.
3. Only then discuss sorting and ties.

The transfer tasks change one constraint:

- **Unit A, reciprocal rank fusion.** Combining rankings by rank, not score, because two scorers' scales are unrelated. The case "top of one beats middle of both" is deliberate: $1/61 + 1/63$ is slightly more than $2/62$.
- **Unit B, weighted fusion.** Weights let a weak ranker count for less. The exploration is a lesson in honesty: a weight chosen on twelve questions is a result on twelve questions.

An alternative implementation is valid if it meets the same behavioural contract.

## Changed-case prompt and remediation

- **Unit A:** the embedding model changes to `all-minilm`. What must happen to every row before `search` answers again? (Every note is embedded again with the new model.)
- **Unit B:** add a seventh paraphrase that shares one ordinary word with the wrong note. Predict what BM25 and fusion do.

For a ranking error, print the scores beside the ids before and after the change. For a metric error, compute one question by hand and compare. Keep the negative observation as evidence, then restore the learner's implementation.

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
| Connection | Traces the observed ranking or table back through the invoked learner code |
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

**Surviving limitation:** Unit A's vectors have two numbers per word and were trained on twelve notes; they show the mechanism, not a model of meaning. Unit B's questions are twelve, so one question moves a recall by 0.167. The chapter's experiment measures a real model on Chapter 5's forty notes, and its Part B stores vectors in SQLite.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
