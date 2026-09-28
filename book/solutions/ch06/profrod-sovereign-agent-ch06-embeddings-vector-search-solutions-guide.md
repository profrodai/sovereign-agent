# Chapter 6: Embeddings and vector search

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**PLANNED — construction brief; no completed notebook or solution is published for this chapter.**

This slot belongs to the single twenty-chapter edition. Read the detailed chapter scope in the textbook's Chapter 6. The existing course material for later chapters remains available using its supplied reference runtime; completing it does not demonstrate construction of this missing foundation.

The planned exercises are two independent ninety-minute units. Unit A builds and connects the component from its first principles. Unit B introduces a failure, requires a repair, and tests a changed case. Both will introduce every new library and concept where used, include predictions and progressive hints, and retain the learner's implementation and evidence.

The solutions volume will explain each design decision, show the failed approach and repair, and include independently calculated expectations. The educator materials will include local student and worked copies, preparation instructions, misconception prompts, timing observations and an assessment rubric. These are requirements, not claims of delivery.

## Planned learning contract: embeddings and vector search

**Starting knowledge and new concepts:** Chapter 5's BM25 retriever, its labeled questions and ranking metrics, and Chapter 4's SQLite store. Introduce one-hot vectors, the embedding lookup as a matrix product, negative sampling and the contrastive objective, pooling and normalization, cosine and Euclidean distance, nearest-neighbor search, approximate indexes and reciprocal rank fusion.

**Unit A construction:** Build word vectors and one vector per note from scratch, then a store with add, query, filter and delete, and retrieve a note that never uses the query's words.

| Minutes | Work |
|---|---|
| 0–10 | Predict similarity from word indexes, then from one-hot vectors |
| 10–30 | Compute the embedding lookup as a matrix product by hand |
| 30–50 | Train word vectors with negative sampling on Lucy's notes |
| 50–70 | Pool and normalize note vectors; compare three distances |
| 70–90 | Build and query a store with filters and deletes |

**Unit B diagnosis and transfer:** Measure dense, lexical and fused retrieval on labeled questions, reproduce a stale-note and a product-code failure, repair both, and measure an approximate index's recall against its comparisons.

| Minutes | Work |
|---|---|
| 0–10 | Predict recall for three retrievers |
| 10–30 | Measure recall@k and reciprocal rank |
| 30–45 | Repair a stale note with a revision filter |
| 45–60 | Repair a product-code miss with reciprocal rank fusion |
| 60–80 | Measure a small graph index's recall against exact search |
| 80–90 | State when a vector index is worth it |

**Independent acceptance examples:** A paraphrased question that shares no word with its note retrieves it. A query embedded with a different model is refused. Only the current revision of a changed note is eligible. A product code ranks first after fusion. An approximate index reports its recall with its comparison count.

The worked chapter must show the first failing implementation, the specific observation that invalidates it, the repair and a new independently calculated case. It must explain each new library call before relying on it. No answer implementation is supplied yet.

[Back to this asset](../profrod-sovereign-agent-solutions-start-here.md)

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
