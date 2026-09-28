# Runnable reference checkpoints

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Updated:** 2026-09-09 · **Status:** DRAFT

Run from the complete repository root using the [frozen environment](profrod-sovereign-agent-textbook-conventions.md). These demonstrations accompany the manuscript. The [ownership guide](profrod-sovereign-agent-textbook-ownership.md) distinguishes learner-built definitions from supplied runtime behavior. Chapter 4's checkpoint runs the learner's own store, and Chapter 8's runs the learner's work queue on it. New Chapter 14 has a construction brief, not a completed checkpoint.

| Chapter | Manuscript | Checkpoint |
| --- | --- | --- |
| 1 | [What a model call is: tokens, probabilities and Lucy's first brief](ch01/profrod-sovereign-agent-ch01-first-model-call-chapter.md) | [ch01.py](checkpoints/profrod_sovereign_agent_ch01_first_model_call_checkpoint.py) |
| 2 | [Structured output and typed tools: what a schema guarantees](ch02/profrod-sovereign-agent-ch02-pydantic-shop-tools-chapter.md) | [ch02.py](checkpoints/profrod_sovereign_agent_ch02_pydantic_shop_tools_checkpoint.py) |
| 3 | [The agent loop: why reliability compounds, and a loop that stops](ch03/profrod-sovereign-agent-ch03-agent-loop-chapter.md) | [ch03.py](checkpoints/profrod_sovereign_agent_ch03_agent_loop_checkpoint.py) |
| 4 | [Build durable state with SQLite](ch04/profrod-sovereign-agent-ch04-sqlite-state-chapter.md) | [ch04.py](checkpoints/profrod_sovereign_agent_ch04_sqlite_state_checkpoint.py) |
| 5 | [Memory and retrieval: what the model sees, and a memory that forgets](ch05/profrod-sovereign-agent-ch05-durable-memory-chapter.md) | [ch05.py](checkpoints/profrod_sovereign_agent_ch05_durable_memory_checkpoint.py) |
| 6 | [Embeddings and vector search: when words are not enough](ch06/profrod-sovereign-agent-ch06-embeddings-vector-search-chapter.md) | [ch06.py](checkpoints/profrod_sovereign_agent_ch06_embeddings_vector_search_checkpoint.py) |
| 7 | [In-context learning: why a skill's exact words must be tested](ch07/profrod-sovereign-agent-ch07-versioned-skills-chapter.md) | [ch07.py](checkpoints/profrod_sovereign_agent_ch07_versioned_skills_checkpoint.py) |
| 8 | [Build a durable work inbox and report outbox](ch08/profrod-sovereign-agent-ch08-durable-inbox-outbox-chapter.md) | [ch08.py](checkpoints/profrod_sovereign_agent_ch08_durable_inbox_outbox_checkpoint.py) |
| 9 | [Where the wait goes: prefill, decode and a phone channel](ch09/profrod-sovereign-agent-ch09-telegram-messaging-chapter.md) | [ch09.py](checkpoints/profrod_sovereign_agent_ch09_telegram_messaging_checkpoint.py) |
| 10 | [Events at random: queues, utilization and scheduled work](ch10/profrod-sovereign-agent-ch10-schedules-stock-events-chapter.md) | [ch10.py](checkpoints/profrod_sovereign_agent_ch10_schedules_stock_events_checkpoint.py) |
| 11 | [When to ask: calibration, oversight and spending permission](ch11/profrod-sovereign-agent-ch11-spending-permissions-chapter.md) | [ch11.py](checkpoints/profrod_sovereign_agent_ch11_spending_permissions_checkpoint.py) |
| 12 | [Exactly one order: lost replies, retries and idempotency](ch12/profrod-sovereign-agent-ch12-ambiguous-supplier-order-chapter.md) | [ch12.py](checkpoints/profrod_sovereign_agent_ch12_ambiguous_supplier_order_checkpoint.py) |
| 13 | [Slow or dead: leases, fencing and crash recovery](ch13/profrod-sovereign-agent-ch13-worker-recovery-chapter.md) | [ch13.py](checkpoints/profrod_sovereign_agent_ch13_worker_recovery_checkpoint.py) |
| 14 | [Connect an external tool with MCP](ch14/profrod-sovereign-agent-ch14-mcp-tools-chapter.md) | PLANNED — no executable checkpoint |
| 15 | [Prompt injection and isolation: words steer the model, boundaries hold](ch15/profrod-sovereign-agent-ch15-tool-isolation-chapter.md) | [ch15.py](checkpoints/profrod_sovereign_agent_ch15_tool_isolation_checkpoint.py) |
| 16 | [Evaluation as measurement: error bars and paired comparisons](ch16/profrod-sovereign-agent-ch16-agent-evaluation-chapter.md) | [ch16.py](checkpoints/profrod_sovereign_agent_ch16_agent_evaluation_checkpoint.py) |
| 17 | [Optimizing against an evaluation: the winner's curse and preferences](ch17/profrod-sovereign-agent-ch17-controlled-improvement-chapter.md) | [ch17.py](checkpoints/profrod_sovereign_agent_ch17_controlled_improvement_checkpoint.py) |
| 18 | [When a second agent pays: parallelism, errors and bounded delegation](ch18/profrod-sovereign-agent-ch18-bounded-delegation-chapter.md) | [ch18.py](checkpoints/profrod_sovereign_agent_ch18_bounded_delegation_checkpoint.py) |
| 19 | [What a model call costs, and a deployment that survives](ch19/profrod-sovereign-agent-ch19-deployment-restoration-chapter.md) | [ch19.py](checkpoints/profrod_sovereign_agent_ch19_deployment_restoration_checkpoint.py) |
| 20 | [A whole day: reliability, honest reports and readiness](ch20/profrod-sovereign-agent-ch20-integrated-shop-day-chapter.md) | [ch20.py](checkpoints/profrod_sovereign_agent_ch20_integrated_shop_day_checkpoint.py) |

The final accelerated day retains two databases, a readable report and JSON evidence:

```bash
uv run --python 3.14 python book/textbook/checkpoints/profrod_sovereign_agent_ch20_integrated_shop_day_checkpoint.py --output /tmp/lucy-day-first-run
```

Use a fresh output path for each retained run; the checkpoint refuses to overwrite it. The independently authored fixture expects two accepted orders totaling 2600 cents. Vanilla ends with eight physical tubs after one receiving event; strawberry has one physical tub and four pending; chocolate stays at twelve. These are fixture expectations, not a business forecast. Its Telegram and model exchanges are simulated. A successful day does not establish a live handset exchange or long-running uptime.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
