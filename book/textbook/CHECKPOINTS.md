# Runnable reference checkpoints

**Updated:** 2026-09-09 · **Status:** DRAFT

Run from the complete repository root using the [frozen environment](CONVENTIONS.md). These demonstrations accompany the manuscript. The [ownership guide](OWNERSHIP.md) distinguishes learner-built definitions from supplied runtime behavior. New Chapters 4, 7 and 13 have construction briefs, not completed checkpoints.

| Chapter | Manuscript | Checkpoint |
| --- | --- | --- |
| 1 | [Make the first model call for Lucy](ch01/README.md) | [ch01.py](checkpoints/ch01.py) |
| 2 | [Give the agent reliable shop tools](ch02/README.md) | [ch02.py](checkpoints/ch02.py) |
| 3 | [Build the model and tool loop](ch03/README.md) | [ch03.py](checkpoints/ch03.py) |
| 4 | [Build durable state with SQLite](ch04/README.md) | PLANNED — no executable checkpoint |
| 5 | [Remember across conversations](ch05/README.md) | [ch05.py](checkpoints/ch05.py) |
| 6 | [Reuse a tested opening procedure](ch06/README.md) | [ch06.py](checkpoints/ch06.py) |
| 7 | [Build a durable work inbox and report outbox](ch07/README.md) | PLANNED — no executable checkpoint |
| 8 | [Talk to the agent from your phone](ch08/README.md) | [ch08.py](checkpoints/ch08.py) |
| 9 | [Wake up for schedules and stock events](ch09/README.md) | [ch09.py](checkpoints/ch09.py) |
| 10 | [Ask permission before spending](ch10/README.md) | [ch10.py](checkpoints/ch10.py) |
| 11 | [Survive the ambiguous supplier order](ch11/README.md) | [ch11.py](checkpoints/ch11.py) |
| 12 | [Recover work after a process crash](ch12/README.md) | [ch12.py](checkpoints/ch12.py) |
| 13 | [Connect an external tool with MCP](ch13/README.md) | PLANNED — no executable checkpoint |
| 14 | [Isolate tools and untrusted content](ch14/README.md) | [ch14.py](checkpoints/ch14.py) |
| 15 | [Measure whether the agent helps](ch15/README.md) | [ch15.py](checkpoints/ch15.py) |
| 16 | [Improve behavior with evaluated changes](ch16/README.md) | [ch16.py](checkpoints/ch16.py) |
| 17 | [Delegate one bounded task](ch17/README.md) | [ch17.py](checkpoints/ch17.py) |
| 18 | [Deploy and maintain the agent](ch18/README.md) | [ch18.py](checkpoints/ch18.py) |
| 19 | [Lucy leaves the shop for a day](ch19/README.md) | [ch19.py](checkpoints/ch19.py) |

The final accelerated day retains two databases, a readable report and JSON evidence:

```bash
uv run --python 3.14 python book/textbook/checkpoints/ch19.py --output /tmp/lucy-day-first-run
```

Use a fresh output path for each retained run; the checkpoint refuses to overwrite it. The independently authored fixture expects two accepted orders totaling 2600 pence. Vanilla ends with eight physical tubs after one receiving event; strawberry has one physical tub and four pending; chocolate stays at twelve. These are fixture expectations, not a business forecast. Its Telegram and model exchanges are simulated. A successful day does not establish a live handset exchange or long-running uptime.
