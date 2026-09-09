# Chapter 4: Build durable SQLite state

**PLANNED — construction brief; no completed notebook or solution is published for this chapter.**

This slot belongs to the single nineteen-chapter edition. Read the detailed chapter scope in the textbook's Chapter 4. The existing course material for later chapters remains available using its supplied reference runtime; completing it does not demonstrate construction of this missing foundation.

The planned exercises are two independent ninety-minute units. Unit A builds and connects the component from its first principles. Unit B introduces a failure, requires a repair, and tests a changed case. Both will introduce every new library and concept where used, include predictions and progressive hints, and retain the learner's implementation and evidence.

The solutions volume will explain each design decision, show the failed approach and repair, and include independently calculated expectations. The educator materials will include local student and worked copies, preparation instructions, misconception prompts, timing observations and an assessment rubric. These are requirements, not claims of delivery.

## Planned learning contract: Durable SQLite state

**Starting knowledge and new concepts:** Python values, functions and exceptions. Introduce tables, primary keys, SQL, parameter binding, transactions, commits, rollback and reopening a database before using them.

**Unit A construction:** Build a small StateStore wrapper that opens a file, returns named rows and performs one atomic change. Keep SQL and transaction boundaries visible.

| Minutes | Work |
|---|---|
| 0–10 | Predict what survives a process exit |
| 10–30 | Create, insert and select a row with bound parameters |
| 30–60 | Construct the wrapper and transaction boundary |
| 60–80 | Reopen and test an independent changed case |
| 80–90 | Explain and retain the observed rows |

**Unit B diagnosis and transfer:** Interrupt an update between changing a balance and recording its event. Prove rollback preserves both old values, then repair and reopen the database.

| Minutes | Work |
|---|---|
| 0–15 | Retrieve commit versus rollback from memory |
| 15–35 | Reproduce the interrupted two-write failure |
| 35–60 | Repair atomicity without swallowing the error |
| 60–80 | Test empty state, duplicate identity and reopen |
| 80–90 | Explain why local rollback says nothing about a remote supplier |

**Independent acceptance examples:** A new empty database has zero events. Record a stock count of 8 and reopen: the count remains 8. An injected exception between two writes leaves neither write. Replaying an identical event identity and payload retains one event; conflicting content is refused without changing the original event. A duplicate stock primary key is refused.

[Back to this asset](../README.md)
