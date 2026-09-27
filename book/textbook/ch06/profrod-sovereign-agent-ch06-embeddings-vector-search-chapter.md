# Chapter 6 — Embeddings and vector search: when words are not enough

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Status: PLANNED.** This is the construction brief for a dedicated chapter on embeddings and vector search. Its complete manuscript, learner implementation, experiment and receipt, two runnable notebooks and checkpoint remain to be authored. The [vector databases interlude](https://github.com/profrodai/sovereign-agent/pull/104), first taught live on September 24, 2026, supplies the starting material for Unit A.

## Why Lucy needs this chapter

[Chapter 5](../ch05/profrod-sovereign-agent-ch05-durable-memory-chapter.md) chose which of Lucy's notes the model sees, by counting shared words with BM25. It measured the limit of that choice. The right note came back for almost every question asked in the note's own words, and for only half of the paraphrases. "At what hour should the supplier's van turn up?" shares no content word with the note that answers it: "Lucy asked for deliveries in the afternoon, because she opens the shop alone in the morning."

An embedding places a text as a vector, so that texts with similar meanings land near each other, whatever words they use. Nearest-neighbor search over those vectors finds the paraphrased note. It also brings new failures: a close note that is out of date, an exact code that a lexical search would have matched, a negation that barely moves the vector, and a search whose cost grows with every note. This chapter measures both the gain and the failures, and then gives Lucy's agent a vector index it can trust.

This chapter follows [durable memory and retrieval](../ch05/profrod-sovereign-agent-ch05-durable-memory-chapter.md) and precedes [versioned skills](../ch07/profrod-sovereign-agent-ch07-versioned-skills-chapter.md).

## Goals and prerequisites

Bring Chapter 5's BM25 retriever, its labeled questions and its ranking metrics, and Chapter 4's SQLite store. No linear algebra beyond the dot product is assumed; every operation is computed by hand on small vectors before it is used at scale.

By the end you will be able to:

1. Explain why a word's index carries no meaning, and how an embedding lookup is a matrix product.
2. Explain how embedding models are trained to place related texts together, from skip-gram with negative sampling to contrastive sentence encoders.
3. Compare cosine similarity, dot product and Euclidean distance, and explain why they agree on normalized vectors.
4. Measure dense retrieval against BM25 on labeled questions, and combine them with reciprocal rank fusion.
5. Explain exact and approximate nearest-neighbor search, and measure an approximate index's recall against its cost.
6. Store embeddings with their model and version, filter out stale memories, and refuse to compare vectors from different models.

## Concepts introduced before their use

A **vector** is a list of numbers; the **dot product** of two vectors sums their pairwise products. **Cosine similarity** divides it by both lengths, so it compares directions. A **one-hot** vector marks one word in a vocabulary; any two different words have dot product zero, so it carries no notion of similarity.

An **embedding** is a learned vector for a token or a text. Skip-gram with negative sampling learns word vectors by predicting which words appear near each other. Modern sentence encoders are trained **contrastively**: matching pairs are pulled together and mismatched pairs pushed apart, with the InfoNCE loss. A text's vector is **pooled** from its token vectors, usually by averaging, and **normalized** to length one.

**Nearest-neighbor search** returns the stored vectors closest to a query. Exact search compares the query with every vector: $n \cdot d$ multiplications for $n$ vectors of $d$ dimensions. **Approximate** indexes trade a little recall for far fewer comparisons: a navigable small-world graph (HNSW), clustering into inverted lists (IVF), or compressed codes (product quantization). A **vector database** stores vectors with their text and metadata, and answers queries with filters, updates and deletes.

**Hybrid retrieval** combines a lexical and a dense ranking; **reciprocal rank fusion** scores each note by the sum of $1/(k + \text{rank})$ across the rankings.

## Part A — measured, planned

| Step | Derive | Measure |
| --- | --- | --- |
| 1 | One-hot vectors, and the embedding lookup as a matrix product | By hand on a five-word vocabulary |
| 2 | Skip-gram with negative sampling; the contrastive objective | Train two-dimensional word vectors on Lucy's notes and watch them move |
| 3 | Cosine, dot product and squared Euclidean distance on normalized vectors | The three orderings agree after normalization |
| 4 | Recall@k and reciprocal rank for dense, lexical and fused retrieval | Chapter 5's labeled questions, direct and paraphrased, on a local embedding model, with a generative model's raw hidden states as a negative control |
| 5 | Exact search cost $n \cdot d$; how a graph index skips most comparisons | Recall of a from-scratch small-world graph against exact search, per comparison budget |
| 6 | Where dense retrieval fails | A stale note, an exact product code, and a negation, each against BM25 |

Every measured claim goes into a receipt with its model, dimensions and graded answers, like the other chapters. The embedding model is served locally, so the chapter runs offline after setup; the choice of model is recorded as an open decision below.

## Part B — Lucy's vector index, planned

The learner owns an embedding store in SQLite: one row per note with its vector as float32 bytes, the embedding model's name and dimension, and the note's revision. The store refuses to compare vectors from different models, re-embeds when the model changes, and filters on the current revision before ranking. Retrieval combines BM25 and dense rankings with reciprocal rank fusion, and Chapter 5's memory selection uses it through the same interface.

## Build, fail and repair

| Step | Build | Predict or break |
| --- | --- | --- |
| 1 | Store one normalized vector per note with model and revision | A query embedded with another model must be refused, not ranked |
| 2 | Exact cosine search over the store | The paraphrased question now finds its note |
| 3 | A superseded note ranks first for its old question | Filtering on the current revision removes it without deleting history |
| 4 | Search for a product code such as SKU-VANILLA | Dense retrieval misses what BM25 finds; fusion recovers it |
| 5 | Grow the store and bound the comparisons | An approximate index keeps most of exact search's recall at a fraction of the cost |

## Ownership and handoff interfaces

The learner owns the vector encoding, the store schema, exact search, the fusion function and the evaluation. The minimal interface is `embed(texts) -> vectors`, `add(note_id, text, revision)`, `search(query, k, current_only=True)` and `evaluate(questions) -> recall and reciprocal rank`. The embedding model is a supplied dependency called through `embed`; nothing else in the chapter depends on its internals.

Chapter 7 consumes the retriever when a skill needs the relevant notes; later chapters use it through Chapter 5's memory selection.

## Unit A — Build embeddings and a vector store, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict whether "vanilla" is closer to "vegan" or "chocolate" by index | Written prediction |
| 10–30 | One-hot vectors and the embedding lookup as a matrix product | By-hand results |
| 30–50 | Train word vectors with negative sampling on Lucy's notes | Loss and vector snapshots |
| 50–70 | Pool and normalize one vector per note; compare three distances | Note vectors and orderings |
| 70–85 | Build a store with add, query, filter and delete | Retrieval of a note that never says "vegan" |
| 85–90 | Explain what a trained encoder adds | Recall response |

## Unit B — Evaluate and repair retrieval, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict recall for BM25, dense and fused retrieval | Written predictions |
| 10–30 | Measure recall@k and reciprocal rank on labeled questions | Metric table |
| 30–45 | Reproduce the stale-note failure and repair it with a revision filter | Before and after rankings |
| 45–60 | Reproduce the product-code failure and repair it with fusion | Fused ranking |
| 60–80 | Build a small graph index and measure recall against comparisons | Recall-cost curve |
| 80–90 | State when a vector index is and is not worth it | Written decision |

## Independent acceptance examples

| Given and action | Expected observation |
| --- | --- |
| Query "a vegan treat" over Lucy's notes | The note about a dairy-free chocolate, which never says "vegan", ranks in the top three |
| Vectors stored with one model, query embedded with another | Refusal; no ranking |
| Delivery moved from Monday to Friday; query "when does the supplier deliver" | Only the current note is eligible |
| Query "SKU-VANILLA" | The note naming the code ranks first after fusion |
| Graph index with a small comparison budget | Recall below exact search, reported with its comparison count |

Completion requires the dedicated chapter, both notebook and Markdown pairs, worked answers, the educator guide, the learner-owned checkpoint and a measured receipt.

## Open decision

Part A measures dense retrieval on a local embedding model. The candidates are small Ollama embedding models such as `nomic-embed-text` or `all-minilm`; adding one is a new download for every reader and needs the maintainers' approval before the chapter depends on it. The interlude's optional Chroma section stays optional and runs only in Colab.

Continue to [Chapter 7: versioned skills](../ch07/profrod-sovereign-agent-ch07-versioned-skills-chapter.md). [Exercise Book](../../exercises/ch06/profrod-sovereign-agent-ch06-embeddings-vector-search-exercise-guide.md) · [Solutions Book](../../solutions/ch06/profrod-sovereign-agent-ch06-embeddings-vector-search-solutions-guide.md) · [Textbook contents](../profrod-sovereign-agent-textbook-start-here.md).

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
