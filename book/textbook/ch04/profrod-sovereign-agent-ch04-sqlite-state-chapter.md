# Chapter 4 — Build durable state with SQLite

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Status: PLANNED.** This is the construction brief for a new lesson. The complete teaching manuscript, learner implementation, two runnable notebooks and executable checkpoint remain to be authored. The examples below specify acceptance; they are not a completed lesson disguised as working code.

## Why Lucy needs this chapter

Yesterday's Python dictionary disappears when the process exits. Lucy's corrected delivery preference must still exist tomorrow. Before choosing which facts to remember, we need a place where a successfully committed change survives a restart and an interrupted multi-write change leaves no half-finished state.

This chapter sits between the [model/tool loop](../ch03/profrod-sovereign-agent-ch03-agent-loop-chapter.md) and [memory](../ch05/profrod-sovereign-agent-ch05-durable-memory-chapter.md). It constructs the state boundary that the rest of the book will consume. A small SQLite database is the first useful mechanism; copying the finished project's complete historical schema would hide the design we need to understand.

## Goals and prerequisites

You bring Python functions, dictionaries, classes, exceptions and the bounded loop from Chapters 1–3. No SQL, database-driver or context-manager experience is assumed. The lesson must introduce each before relying on it.

By the end you will be able to:

1. Create a file-backed database, insert a stock record, close it and recover that record in a new connection.
2. Explain a row, column, primary key, constraint and parameterized statement through a concrete shop example.
3. Construct an explicit transaction boundary in which a state change and its event either both commit or both disappear.
4. Refuse a duplicate identity with conflicting content, immutable event replacement and an unsupported schema version.
5. Explain why the same connection returning a row does not prove that another process can recover it.

## Introduce the concepts slowly

Begin with a two-column Python table on paper: `sku` identifies a product and `stock_tubs` holds its current quantity. Translate that one table into SQL, explaining each keyword before introducing a wrapper. A **primary key** identifies a row; a **constraint** refuses an invalid state at the storage boundary. A **parameter** passes a value separately from the SQL instruction so product text is never interpreted as query structure.

A **connection** is a handle to the database, not the database file itself. A **transaction** groups changes so their committed visibility is all-or-nothing. A **commit** publishes those changes; a **rollback** discards the uncommitted group. Closing and reopening with a second connection makes persistence observable. Explain Python's `with` statement and exception propagation before constructing a context manager.

Select and document transaction control explicitly for the pinned Python version. Do not inherit a driver default and call it a design. Show one read, one committed insert and one rejected insert before introducing retries, indices or migrations. The [Python SQLite reference](https://docs.python.org/3.14/library/sqlite3.html) supports the driver-specific details; the chapter must still teach the concepts without requiring an external reading detour.

## The construction sequence

| Step | Build | Predict, break and repair |
| --- | --- | --- |
| 1 | Open a fresh file and define a stock table | An empty query returns zero rows; missing data is not invented |
| 2 | Insert vanilla with two tubs using parameters | Close and reopen; expect exactly the same row |
| 3 | Add identity and nonnegative-quantity constraints | A second vanilla identity and a negative quantity must fail without altering the original |
| 4 | Write stock and an event separately | Inject an exception between writes and observe the inconsistent result |
| 5 | Construct one explicit transaction around both writes | Inject the same exception; neither write may survive |
| 6 | Add append-only events with immutable identity/content | Replaying identical content is distinct from replacing an event |
| 7 | Introduce a schema-version row and one migration | Migrate a supported old version; reject a future version before changing any rows |
| 8 | Reopen with a separate observer connection | Compare authored expected rows and event counts to persisted reality |

The wrapper comes last. Each of its responsibilities must already have appeared as a small, visible operation. Explain lock contention with two connections and a bounded failure policy; never silently retry an entire external business operation because a database write was busy.

## Ownership and handoff contract

The learner owns `StateStore`, the connection lifetime, an `immediate()` transaction context manager, schema initialization/migration and immutable `append_event` behavior. These names are the planned teaching interface, not aliases for the supplied `sovereign_agent.database.Database` class.

The initial schema contains only chapter-owned state and event records. Memory adds its own tables in Chapter 5; durable work adds its tables in Chapter 7. Record each migration's owner and supported predecessor version. Avoid importing the finished runtime's governance tables to make a notebook pass.

Required behavior: entering a transaction gives one current connection; successful exit commits; an exception rolls back and propagates; a failed commit cannot be reported as success; ownership of connection closure is explicit. Nested transactions are refused in the initial interface until their semantics are deliberately taught. Chapter 5 receives the store and parameterized execution interface, not an unbounded collection of hidden convenience functions.

A temporary directory and independent observer connection are supplied test infrastructure. The observer reads persisted rows directly; it must not call the learner's own summary method to generate its expected result.

## Unit A — Construct and connect, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Retrieve the difference between a Python value and durable state; predict an empty query | Written prediction |
| 10–25 | Translate a stock dictionary into the first schema and parameterized insert | One committed row |
| 25–40 | Close/reopen, then exercise identity and quantity constraints | Independent read and two refusals |
| 40–55 | Introduce exceptions and a transaction with two writes | Before/after state table |
| 55–75 | Implement the minimal StateStore and append-event path | Learner code and passing authored examples |
| 75–85 | Connect a Chapter 2 stock observation to persisted state | Trace from handler input to stored row |
| 85–90 | Explain what survived and submit the artifact | Recall answers and source file |

## Unit B — Diagnose and transfer, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict failure between the two writes | Expected row/event counts |
| 10–25 | Reproduce a partial-commit implementation | Failing independent observation |
| 25–45 | Repair transaction and exception propagation | Passing rollback/reopen cases |
| 45–60 | Introduce one schema migration and refuse a future version | Version/state evidence |
| 60–75 | Transfer to a second product, duplicate event and competing connection | Distinct failure dispositions |
| 75–85 | Remove the learner transaction boundary and prove the checker fails | Negative-control result |
| 85–90 | Explain the handoff to memory without reading the solution | Written reasoning |

## Independent acceptance examples

| Given and action | Expected observation |
| --- | --- |
| Fresh database, query stock | Zero rows and the supported schema version |
| Commit vanilla=2 and event e1, then reopen | One vanilla row and exactly one e1 |
| Attempt vanilla=9 and e2, raising between writes | Reopen still shows vanilla=2 and only e1 |
| Append e1 again with the same payload | One retained e1; documented duplicate outcome |
| Append e1 with different payload | Explicit conflict; original e1 unchanged |
| Set the schema marker to an unsupported future version | Initialization refuses before any migration or business write |
| Transaction implementation suppresses the injected exception | Independent checker fails even if a convenience method reports success |

Acceptance also starts from an empty learner workspace with declared dependencies. The essential state path may not import the finished reference database. Completion requires the full explanatory chapter, both ninety-minute notebook/Markdown pairs, worked solutions, educator guide and an executable checkpoint using the learner's implementation.

Continue to [Chapter 5: memory](../ch05/profrod-sovereign-agent-ch05-durable-memory-chapter.md). [Exercise Book](../../exercises/ch04/profrod-sovereign-agent-ch04-sqlite-state-exercise-guide.md) · [Solutions Book](../../solutions/ch04/profrod-sovereign-agent-ch04-sqlite-state-solutions-guide.md) · [Textbook contents](../profrod-sovereign-agent-textbook-start-here.md).

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
