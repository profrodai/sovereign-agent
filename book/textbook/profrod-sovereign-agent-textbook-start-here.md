# The Teaching Book

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Edition:** twenty-chapter construction · **Updated:** 2026-09-09

Build Your Always-On AI Agent From Scratch follows one Python agent from its first model call to an unattended day in Lucy's ice cream shop. Read the chapters in order. Each introduces a problem, constructs a mechanism, reproduces a failure and explains the repair.

Start with the [preface](profrod-sovereign-agent-textbook-preface.md) and [setup and reader conventions](profrod-sovereign-agent-textbook-conventions.md), then [Chapter 1](ch01/profrod-sovereign-agent-ch01-first-model-call-chapter.md). This directory contains the manuscript and its accompanying code. The [Exercise Book](../exercises/profrod-sovereign-agent-exercises-start-here.md) holds learner assignments, the [Solutions Book](../solutions/profrod-sovereign-agent-solutions-start-here.md) holds worked answers, and the [Educator Guide](../educator/profrod-sovereign-agent-educator-start-here.md) holds classroom material. Chapter numbers and topics match across all four assets.

## What is available

There is one twenty-chapter sequence. Eighteen chapters contain substantial **DRAFT** manuscripts and executable checkpoints; Chapter 4's runs the learner's own store, and Chapter 8's the learner's own work queue on it. Chapters **6** and **14** contain **PLANNED construction briefs**: their goals, interfaces, two ninety-minute practical plans and acceptance cases are documented, but their complete lessons, notebooks and new learner implementations are not yet delivered. A planned chapter is not an executable lesson. The [construction roadmap](profrod-sovereign-agent-textbook-expansion.md) records the remaining work and the integration commitments.

You can read the drafted chapters and run their supplied reference checkpoints now. Building the entire twenty-chapter system solely from your own preceding chapter code remains a release requirement. The [code ownership guide](profrod-sovereign-agent-textbook-ownership.md) names the supplied components so a working demonstration cannot be mistaken for a completed from-scratch construction.

## Contents

| Chapter | Read | Status |
| --- | --- | --- |
| 1 | [What a model call is: tokens, probabilities and Lucy's first brief](ch01/profrod-sovereign-agent-ch01-first-model-call-chapter.md) | DRAFT |
| 2 | [Structured output and typed tools: what a schema guarantees](ch02/profrod-sovereign-agent-ch02-pydantic-shop-tools-chapter.md) | DRAFT |
| 3 | [The agent loop: why reliability compounds, and a loop that stops](ch03/profrod-sovereign-agent-ch03-agent-loop-chapter.md) | DRAFT |
| 4 | [Build durable state with SQLite](ch04/profrod-sovereign-agent-ch04-sqlite-state-chapter.md) | DRAFT |
| 5 | [Memory and retrieval: what the model sees, and a memory that forgets](ch05/profrod-sovereign-agent-ch05-durable-memory-chapter.md) | DRAFT |
| 6 | [Embeddings and vector search: when words are not enough](ch06/profrod-sovereign-agent-ch06-embeddings-vector-search-chapter.md) | PLANNED, manuscript drafted |
| 7 | [In-context learning: why a skill's exact words must be tested](ch07/profrod-sovereign-agent-ch07-versioned-skills-chapter.md) | DRAFT |
| 8 | [Build a durable work inbox and report outbox](ch08/profrod-sovereign-agent-ch08-durable-inbox-outbox-chapter.md) | DRAFT |
| 9 | [Where the wait goes: prefill, decode and a phone channel](ch09/profrod-sovereign-agent-ch09-telegram-messaging-chapter.md) | DRAFT |
| 10 | [Events at random: queues, utilization and scheduled work](ch10/profrod-sovereign-agent-ch10-schedules-stock-events-chapter.md) | DRAFT |
| 11 | [When to ask: calibration, oversight and spending permission](ch11/profrod-sovereign-agent-ch11-spending-permissions-chapter.md) | DRAFT |
| 12 | [Exactly one order: lost replies, retries and idempotency](ch12/profrod-sovereign-agent-ch12-ambiguous-supplier-order-chapter.md) | DRAFT |
| 13 | [Slow or dead: leases, fencing and crash recovery](ch13/profrod-sovereign-agent-ch13-worker-recovery-chapter.md) | DRAFT |
| 14 | [Connect an external tool with MCP](ch14/profrod-sovereign-agent-ch14-mcp-tools-chapter.md) | PLANNED |
| 15 | [Prompt injection and isolation: words steer the model, boundaries hold](ch15/profrod-sovereign-agent-ch15-tool-isolation-chapter.md) | DRAFT |
| 16 | [Evaluation as measurement: error bars and paired comparisons](ch16/profrod-sovereign-agent-ch16-agent-evaluation-chapter.md) | DRAFT |
| 17 | [Optimizing against an evaluation: the winner's curse and preferences](ch17/profrod-sovereign-agent-ch17-controlled-improvement-chapter.md) | DRAFT |
| 18 | [When a second agent pays: parallelism, errors and bounded delegation](ch18/profrod-sovereign-agent-ch18-bounded-delegation-chapter.md) | DRAFT |
| 19 | [What a model call costs, and a deployment that survives](ch19/profrod-sovereign-agent-ch19-deployment-restoration-chapter.md) | DRAFT |
| 20 | [A whole day: reliability, honest reports and readiness](ch20/profrod-sovereign-agent-ch20-integrated-shop-day-chapter.md) | DRAFT |

The four parts are: **1–4, First useful construction**; **5–9, Continuity and initiative**; **10–14, Permission and external boundaries**; and **15–19, Evaluate and operate**.

## Working beside the manuscript

Use [runnable checkpoints](profrod-sovereign-agent-textbook-checkpoints.md) to reproduce the recorded mechanisms. Save chapter-built tools and the loop under [learner/](learner/profrod-sovereign-agent-textbook-learner-guide.md); the included completed files provide a comparison. The optional field appendices explain [Telegram identity setup](appendices/profrod-sovereign-agent-textbook-telegram-setup.md), [Linux maintenance](appendices/profrod-sovereign-agent-textbook-linux-maintenance-v1.md), [ZeoCore interoperability](appendices/profrod-sovereign-agent-textbook-zeocore-interop-v2.md), [reproducibility](appendices/profrod-sovereign-agent-textbook-reproducibility-v1.md), and [dated architectural comparisons](appendices/profrod-sovereign-agent-textbook-project-comparisons-v1.md).

The book uses a frozen Python environment from the repository root. Offline checkpoints need no model credentials, Telegram account, real purchasing account or private organizational service. Optional live exercises identify their extra facilities and keep their evidence separate. [Return to the four teaching assets](../README.md).

## Find and share a file

Every teaching file starts with `profrod-sovereign-agent`, followed by its chapter, topic and role. Search for `ch02` to find Chapter 2 or `pydantic` to find its typed-tool material. For example: `profrod-sovereign-agent-ch02-a-pydantic-shop-tools-exercise.ipynb`. The `exercise`, `solution`, `educator-exercise` and `educator-solution` endings distinguish files even when copied into one folder. Keep the original filename and source links when sharing. The matching Markdown uses the same filename with `.md`.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
