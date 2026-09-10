# Chapter 7: Build a durable work inbox and report outbox

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**PLANNED — construction brief; no completed notebook or solution is published for this chapter.**

This slot belongs to the single nineteen-chapter edition. Read the detailed chapter scope in the textbook's Chapter 7. The existing course material for later chapters remains available using its supplied reference runtime; completing it does not demonstrate construction of this missing foundation.

The planned exercises are two independent ninety-minute units. Unit A builds and connects the component from its first principles. Unit B introduces a failure, requires a repair, and tests a changed case. Both will introduce every new library and concept where used, include predictions and progressive hints, and retain the learner's implementation and evidence.

The solutions volume will explain each design decision, show the failed approach and repair, and include independently calculated expectations. The educator materials will include local student and worked copies, preparation instructions, misconception prompts, timing observations and an assessment rubric. These are requirements, not claims of delivery.

## Planned learning contract: Durable work inbox and report outbox

**Starting knowledge and new concepts:** The SQLite construction and memory chapters. Introduce work identity, state transitions, idempotency, claims, leases, cursors and an outbox before combining them.

**Unit A construction:** Admit a request and advance its input cursor in one transaction; have a worker claim and finish the request and create one report atomically.

| Minutes | Work |
|---|---|
| 0–10 | Predict duplicate-request behavior |
| 10–30 | Draw rows, identities and allowed transitions |
| 30–60 | Construct admission and claim operations |
| 60–80 | Connect finish to report creation and test duplicate input |
| 80–90 | Retain the work and report ledger |

**Unit B diagnosis and transfer:** Inject a failure after admission and before cursor advancement, then a lost acknowledgement after report delivery. Separate known failure from unknown delivery.

| Minutes | Work |
|---|---|
| 0–15 | Retrieve transaction and identity invariants |
| 15–35 | Inject a crash between admission and cursor write |
| 35–60 | Repair the transaction and demonstrate restart |
| 60–80 | Handle a lost delivery acknowledgement without guessing |
| 80–90 | Explain pending, sent and unknown reports |

**Independent acceptance examples:** Two deliveries of request ID 42 create one work row. An admission exception advances no cursor. One terminal result creates one report. A lost send acknowledgement becomes UNKNOWN and does not authorize an automatic duplicate send.

The worked chapter must show the first failing implementation, the specific observation that invalidates it, the repair and a new independently calculated case. It must explain each new library call before relying on it. No answer implementation is supplied yet.

[Back to this asset](../profrod-sovereign-agent-solutions-start-here.md)

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
