# Chapter 13: Build an MCP client and tool server

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**PLANNED — construction brief; no completed notebook or solution is published for this chapter.**

This slot belongs to the single nineteen-chapter edition. Read the detailed chapter scope in the textbook's Chapter 13. The existing course material for later chapters remains available using its supplied reference runtime; completing it does not demonstrate construction of this missing foundation.

The planned exercises are two independent ninety-minute units. Unit A builds and connects the component from its first principles. Unit B introduces a failure, requires a repair, and tests a changed case. Both will introduce every new library and concept where used, include predictions and progressive hints, and retain the learner's implementation and evidence.

The solutions volume will explain each design decision, show the failed approach and repair, and include independently calculated expectations. The educator materials will include local student and worked copies, preparation instructions, misconception prompts, timing observations and an assessment rubric. These are requirements, not claims of delivery.

## Planned learning contract: MCP protocol construction

**Starting knowledge and new concepts:** The agent/tool loop, durable work and recovery chapters. Introduce client/server, JSON-RPC messages, request IDs, newline framing, protocol negotiation, capabilities, subprocess pipes and timeouts.

**Unit A construction:** Build a stdio client and a tiny tool server, initialize the connection, discover a read-only tool, validate arguments and invoke it through the existing dispatcher.

| Minutes | Work |
|---|---|
| 0–10 | Predict a request and response exchange |
| 10–30 | Read and write one framed JSON-RPC message |
| 30–60 | Construct initialization and tool discovery |
| 60–80 | Connect one validated tool call to the dispatcher |
| 80–90 | Retain messages and explain capability versus permission |

**Unit B diagnosis and transfer:** Send a mismatched response ID, malformed JSON, a timeout and an unauthorized advertised tool. Repair protocol handling while keeping authority in the dispatcher.

| Minutes | Work |
|---|---|
| 0–15 | Retrieve framing and request-correlation rules |
| 15–35 | Reproduce malformed and mismatched responses |
| 35–60 | Repair bounded error handling and timeout cleanup |
| 60–80 | Reject an advertised but unauthorized tool |
| 80–90 | Explain why MCP does not provide OS containment |

**Independent acceptance examples:** The matching request receives its own result. An unsolicited or mismatched ID cannot satisfy it. A tool advertised by the server does not become authorized by discovery. A timeout leaves an explicit failure and the child process is reaped.

[Back to this asset](../profrod-sovereign-agent-exercises-start-here.md)

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
