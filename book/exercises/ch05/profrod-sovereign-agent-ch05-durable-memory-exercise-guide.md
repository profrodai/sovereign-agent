# Chapter 5: Remember across conversations

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Available draft · two ninety-minute units · nineteen-chapter edition**

Attempt the student work before consulting the solutions. Untouched exercises intentionally report NEEDS_WORK.

| Session | Notebook | Matching text | Purpose |
|---|---|---|---|
| A · 90 minutes | [A: durable memory](profrod-sovereign-agent-ch05-a-durable-memory-exercise.ipynb) | [Markdown](profrod-sovereign-agent-ch05-a-durable-memory-exercise.md) | Construct, connect and explain |
| B · 90 minutes | [B: retrieval and recall](profrod-sovereign-agent-ch05-b-retrieval-and-recall-exercise.ipynb) | [Markdown](profrod-sovereign-agent-ch05-b-retrieval-and-recall-exercise.md) | Derive, evaluate against labeled questions and transfer |

Each notebook includes its own setup, first-principles introductions and supplied teaching runtime. Open either notebook in Google Colab with its badge, or use a local Python 3.12+ Jupyter kernel; Unit A also needs Pydantic 2, and Unit B only the standard library. No repository checkout, previous notebook kernel or live account is needed. Unit A closes with an extension that puts a language model behind the chapter's own tools: a recorded transcript runs everywhere, and an OpenAI key in Colab's Secrets pane switches the same loop to a live `gpt-5.1` run. Unit B builds BM25 and measures it, with recall@3, against Lucy's labeled questions. Unit B can use an explicitly selected successful Unit A handoff; an invalid selected file refuses rather than substituting an answer.

Ninety minutes is the planned work allowance per unit, excluding installation. Actual completion time and understanding require classroom observation.

[Setup](../profrod-sovereign-agent-exercises-setup.md) · [Back to this asset](../profrod-sovereign-agent-exercises-start-here.md)

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
