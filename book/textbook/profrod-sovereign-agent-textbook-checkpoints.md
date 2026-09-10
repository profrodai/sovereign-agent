# Runnable reference checkpoints

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Updated:** 2026-09-09 · **Status:** DRAFT

Run from the complete repository root using the [frozen environment](profrod-sovereign-agent-textbook-conventions.md). These demonstrations accompany the manuscript. The [ownership guide](profrod-sovereign-agent-textbook-ownership.md) distinguishes learner-built definitions from supplied runtime behavior. New Chapters 4, 7 and 13 have construction briefs, not completed checkpoints.

| Chapter | Manuscript | Checkpoint |
| --- | --- | --- |
| 1 | [Make the first model call for Lucy](ch01/profrod-sovereign-agent-ch01-first-model-call-chapter.md) | [ch01.py](checkpoints/profrod_sovereign_agent_ch01_first_model_call_checkpoint.py) |
| 2 | [Give the agent reliable shop tools](ch02/profrod-sovereign-agent-ch02-pydantic-shop-tools-chapter.md) | [ch02.py](checkpoints/profrod_sovereign_agent_ch02_pydantic_shop_tools_checkpoint.py) |
| 3 | [Build the model and tool loop](ch03/profrod-sovereign-agent-ch03-agent-loop-chapter.md) | [ch03.py](checkpoints/profrod_sovereign_agent_ch03_agent_loop_checkpoint.py) |
| 4 | [Build durable state with SQLite](ch04/profrod-sovereign-agent-ch04-sqlite-state-chapter.md) | PLANNED — no executable checkpoint |
| 5 | [Remember across conversations](ch05/profrod-sovereign-agent-ch05-durable-memory-chapter.md) | [ch05.py](checkpoints/profrod_sovereign_agent_ch05_durable_memory_checkpoint.py) |
| 6 | [Reuse a tested opening procedure](ch06/profrod-sovereign-agent-ch06-versioned-skills-chapter.md) | [ch06.py](checkpoints/profrod_sovereign_agent_ch06_versioned_skills_checkpoint.py) |
| 7 | [Build a durable work inbox and report outbox](ch07/profrod-sovereign-agent-ch07-durable-inbox-outbox-chapter.md) | PLANNED — no executable checkpoint |
| 8 | [Talk to the agent from your phone](ch08/profrod-sovereign-agent-ch08-telegram-messaging-chapter.md) | [ch08.py](checkpoints/profrod_sovereign_agent_ch08_telegram_messaging_checkpoint.py) |
| 9 | [Wake up for schedules and stock events](ch09/profrod-sovereign-agent-ch09-schedules-stock-events-chapter.md) | [ch09.py](checkpoints/profrod_sovereign_agent_ch09_schedules_stock_events_checkpoint.py) |
| 10 | [Ask permission before spending](ch10/profrod-sovereign-agent-ch10-spending-permissions-chapter.md) | [ch10.py](checkpoints/profrod_sovereign_agent_ch10_spending_permissions_checkpoint.py) |
| 11 | [Survive the ambiguous supplier order](ch11/profrod-sovereign-agent-ch11-ambiguous-supplier-order-chapter.md) | [ch11.py](checkpoints/profrod_sovereign_agent_ch11_ambiguous_supplier_order_checkpoint.py) |
| 12 | [Recover work after a process crash](ch12/profrod-sovereign-agent-ch12-worker-recovery-chapter.md) | [ch12.py](checkpoints/profrod_sovereign_agent_ch12_worker_recovery_checkpoint.py) |
| 13 | [Connect an external tool with MCP](ch13/profrod-sovereign-agent-ch13-mcp-tools-chapter.md) | PLANNED — no executable checkpoint |
| 14 | [Isolate tools and untrusted content](ch14/profrod-sovereign-agent-ch14-tool-isolation-chapter.md) | [ch14.py](checkpoints/profrod_sovereign_agent_ch14_tool_isolation_checkpoint.py) |
| 15 | [Measure whether the agent helps](ch15/profrod-sovereign-agent-ch15-agent-evaluation-chapter.md) | [ch15.py](checkpoints/profrod_sovereign_agent_ch15_agent_evaluation_checkpoint.py) |
| 16 | [Improve behavior with evaluated changes](ch16/profrod-sovereign-agent-ch16-controlled-improvement-chapter.md) | [ch16.py](checkpoints/profrod_sovereign_agent_ch16_controlled_improvement_checkpoint.py) |
| 17 | [Delegate one bounded task](ch17/profrod-sovereign-agent-ch17-bounded-delegation-chapter.md) | [ch17.py](checkpoints/profrod_sovereign_agent_ch17_bounded_delegation_checkpoint.py) |
| 18 | [Deploy and maintain the agent](ch18/profrod-sovereign-agent-ch18-deployment-restoration-chapter.md) | [ch18.py](checkpoints/profrod_sovereign_agent_ch18_deployment_restoration_checkpoint.py) |
| 19 | [Lucy leaves the shop for a day](ch19/profrod-sovereign-agent-ch19-integrated-shop-day-chapter.md) | [ch19.py](checkpoints/profrod_sovereign_agent_ch19_integrated_shop_day_checkpoint.py) |

The final accelerated day retains two databases, a readable report and JSON evidence:

```bash
uv run --python 3.14 python book/textbook/checkpoints/profrod_sovereign_agent_ch19_integrated_shop_day_checkpoint.py --output /tmp/lucy-day-first-run
```

Use a fresh output path for each retained run; the checkpoint refuses to overwrite it. The independently authored fixture expects two accepted orders totaling 2600 pence. Vanilla ends with eight physical tubs after one receiving event; strawberry has one physical tub and four pending; chocolate stays at twelve. These are fixture expectations, not a business forecast. Its Telegram and model exchanges are simulated. A successful day does not establish a live handset exchange or long-running uptime.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
