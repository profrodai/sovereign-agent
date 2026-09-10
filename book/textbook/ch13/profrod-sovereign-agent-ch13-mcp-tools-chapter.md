# Chapter 13 — Connect an external tool with MCP

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Status: PLANNED.** This is the construction brief for a dedicated protocol lesson. Its complete manuscript, learner implementation, two runnable notebooks and checkpoint remain to be authored. The current [Chapter 14](../ch14/profrod-sovereign-agent-ch14-tool-isolation-chapter.md) retains the existing MCP construction alongside containment until the protocol material is expanded and separated without losing teaching content.

## Why Lucy needs this chapter

The dispatcher can already call a Python function. Now a useful text-analysis tool runs in another process maintained independently. We need an agreed request/response format and a bounded connection, while preserving the application's own tool permissions. A server advertising a tool cannot grant itself permission to run it.

This chapter follows [worker recovery](../ch12/profrod-sovereign-agent-ch12-worker-recovery-chapter.md) and precedes [tool isolation](../ch14/profrod-sovereign-agent-ch14-tool-isolation-chapter.md). MCP supplies a protocol boundary; the next chapter supplies a separately configured operating-system boundary. Starting an MCP child executable does not sandbox it.

## Goals and prerequisites

Bring JSON values, exceptions, time budgets, the typed dispatcher and worker ownership from preceding chapters. No JSON-RPC, subprocess, standard-stream or MCP knowledge is assumed. Start with a dictionary and a child process that echoes one controlled response before introducing the full exchange.

By the end you will be able to:

1. Explain how request IDs associate a response with a particular outstanding call.
2. Exchange newline-framed JSON between a parent and a controlled child process without mixing logs into protocol output.
3. Construct initialization, explicit supported-version negotiation, tool discovery and one allowed invocation.
4. Validate discovered schemas and returned messages before exposing their content to the model.
5. Enforce byte, time and tool-allowlist limits, then clean up the child on success and failure.
6. Explain exactly what the narrow stdio client supports and why protocol success proves neither authorization nor containment.

## Concepts introduced before their use

**JSON-RPC** gives a request a method, parameters and an identity so a reply can refer to it. A **notification** has no request identity and expects no response. The lesson begins with printed request/reply dictionaries and deliberately swaps two IDs before using a subprocess.

A child process has **stdin**, **stdout** and **stderr** streams. The parent writes protocol input to stdin and reads protocol output from stdout; diagnostic logs belong on stderr. **Framing** separates one message from the next in a byte stream. Explain text encoding, the newline boundary and buffering with one short exchange before adding asynchronous reading or deadline enforcement.

**Initialization** establishes the supported protocol and capabilities before ordinary operations. **Discovery** describes available tools. **Local authorization** chooses which discovered tools our application may invoke. The adapter must not collapse those three decisions into “the server responded, therefore execute anything it lists.”

The initial scope is the pinned MCP `2025-06-18` stdio transport. The [transport specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) also defines Streamable HTTP; implementing stdio is not a claim to implement that transport or every MCP feature. Unknown or unsupported version/capability combinations must produce a clear refusal. No new runtime SDK is necessary for the controlled teaching server.

## Build, fail and repair

| Step | Build | Predict or break |
| --- | --- | --- |
| 1 | Author one request/reply pair as JSON values | A reply for a different ID must not satisfy the request |
| 2 | Start a controlled child and exchange one framed message | Missing flush or missing newline exposes the need for a deadline |
| 3 | Separate protocol output from diagnostics | A log line on stdout is a malformed protocol message |
| 4 | Implement initialization and supported-version checks | An unsupported server must not reach tool invocation |
| 5 | Discover a bounded set of tool descriptions | Discovery alone leaves local permission unchanged |
| 6 | Register one validated, explicitly allowed tool | A second advertised but forbidden tool remains uncallable |
| 7 | Invoke through the learner's typed dispatcher | Returned evidence must be associated with the correct request |
| 8 | Bound frames, elapsed time and child lifetime | Wrong IDs, oversized output and hanging children leave no success result |

Use an independently scripted server with known responses. Later replace it with the optional ZeoCore word-count adapter to compare the same protocol boundary with a maintained implementation. ZeoCore remains an optional separate environment; it must not become a prerequisite for building or understanding this client.

## Ownership and handoff interfaces

The learner owns the transport framing, request-ID tracking, initializer, discovery validator and bounded call adapter. The minimal conceptual interface is `initialize()`, `list_tools()` and `call_tool(name, arguments)` with explicit configuration for executable, deadline, frame limit and allowed tool names. Do not implement these by importing the finished `sovereign_agent.mcp_client` client.

The caller supplies a trusted executable configuration. The model may select an allowed tool name and typed arguments; it cannot select a new executable or extend the allowlist. The dispatcher retains application permission and the caller retains work ownership. A late response after timeout is not allowed to revive a completed request or authorize new effects.

Chapter 14 consumes this bounded adapter and adds container enforcement for generated code. Keep process lifecycle responsibilities explicit: the client reaps the child it started, bounds diagnostic collection and explains the limits of its cleanup mechanism. Environment-specific process-tree guarantees need measured evidence rather than a successful `wait()` on the immediate child alone.

## Unit A — Construct and connect, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Match printed requests and responses by identity | Written associations |
| 10–25 | Exchange one JSON line with a controlled subprocess | Captured protocol trace |
| 25–40 | Introduce initialization and version/capability checks | Successful and refused handshakes |
| 40–55 | Discover and validate one tool description | Typed local registration |
| 55–75 | Connect one permitted call through the learner dispatcher | Input-to-observation trace |
| 75–85 | Advertise a second forbidden tool and prove no invocation | Independent server call log |
| 85–90 | Explain protocol versus permission | Recall response |

## Unit B — Diagnose and transfer, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict wrong-ID, oversized and hung-child outcomes | Failure table |
| 10–25 | Reproduce a client that accepts the wrong response | Failing independent observation |
| 25–45 | Repair association and frame validation | Passing adversarial traces |
| 45–60 | Add timeout and cleanup with a controlled hanging server | Deadline and process-exit evidence |
| 60–75 | Transfer to another tool schema and noisy stderr | Correct result without log confusion |
| 75–85 | Remove learner allowlist checking and prove the integrated checker fails | Negative-control result |
| 85–90 | State supported features and containment limits | Written interface contract |

## Independent acceptance examples

| Given and action | Expected observation |
| --- | --- |
| Server initializes with the supported pinned version | Ready for discovery only after the complete handshake |
| Server returns an unsupported version | Clear refusal; zero tool calls |
| Request 41 receives a result labeled 42 | No successful observation accepted for request 41 |
| Server advertises word_count and forbidden purchase | Only configured word_count can enter local dispatch |
| Invoke word_count on `vanilla stock needs review` | Independently authored result: four words |
| Server sends a frame beyond the configured bound | Refusal before parsing an unbounded payload into the model path |
| Server never completes the expected response | Bounded failure and recorded cleanup of the controlled child |
| Server writes a diagnostic on stderr | Diagnostic remains separate from valid protocol output |
| Learner authorization is bypassed | Independent server log exposes the forbidden invocation and the test fails |

Completion requires the dedicated chapter, both notebook/Markdown pairs, worked answers, educator guide and learner-owned checkpoint. Existing protocol teaching is then relocated from Chapter 14, whose opening and prerequisites must be rewritten to assume this explicit construction.

Continue to [Chapter 14: isolation](../ch14/profrod-sovereign-agent-ch14-tool-isolation-chapter.md). [Exercise Book](../../exercises/ch13/profrod-sovereign-agent-ch13-mcp-tools-exercise-guide.md) · [Solutions Book](../../solutions/ch13/profrod-sovereign-agent-ch13-mcp-tools-solutions-guide.md) · [Textbook contents](../profrod-sovereign-agent-textbook-start-here.md).

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
