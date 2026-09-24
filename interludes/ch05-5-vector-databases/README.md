# Chapter 5.5: Vector databases from scratch

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

An interlude after Chapter 5, first taught live in the ITAM class of September 24, 2026. Chapter 5 selected memories by session, revision and word overlap, and it deliberately used no embeddings. This interlude builds the missing piece from scratch — words to vectors, learned embeddings, one vector per note, a store you can query — and then does the same with Chroma and real embeddings.

| Notebook | Open | What you do |
|---|---|---|
| [profrod-sovereign-agent-ch05-5-vector-databases-exercise.ipynb](profrod-sovereign-agent-ch05-5-vector-databases-exercise.ipynb) | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/interludes/ch05-5-vector-databases/profrod-sovereign-agent-ch05-5-vector-databases-exercise.ipynb) | Parts 1–4 run with nothing installed and no key. Part 4b installs Chroma and embeds with your own OpenAI key (the Colab secret `OPENAI_API_KEY`, never printed), or with Chroma's local default model when you have none. |

The notebook is generated from the class lab (`vector_db_lab.py`, Python standard library only), embedded in its setup cell and checked by SHA-256 `cad48ddf2b48…`. It sits outside `book/` because the book's nineteen-chapter layout is fixed; whether it becomes part of the book proper is decided later.

Back to [Chapter 5's exercises](../../book/exercises/ch05/profrod-sovereign-agent-ch05-durable-memory-exercise-guide.md).
