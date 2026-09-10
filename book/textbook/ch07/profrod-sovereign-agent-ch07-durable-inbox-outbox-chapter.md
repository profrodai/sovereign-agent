# Chapter 7 — Build a durable work inbox and report outbox

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Status: PLANNED.** This construction brief defines the new lesson and acceptance cases. Its full manuscript, learner implementation, two runnable notebooks and checkpoint remain to be authored. Existing Telegram and scheduling demonstrations continue to use supplied runtime infrastructure until their handoff is rebuilt against this chapter.

## Why Lucy needs this chapter

A request stored in a Python list vanishes with the process. A completed stock brief can also vanish from the customer's perspective if the process dies between recording completion and sending the reply. These are different failures: the agent needs durable work to do and durable reports to deliver.

This chapter follows [tested skills](../ch06/profrod-sovereign-agent-ch06-versioned-skills-chapter.md) and precedes [Telegram](../ch08/profrod-sovereign-agent-ch08-telegram-messaging-chapter.md). We first build the shared work mechanism without a messaging account. Telegram and the scheduler then become producers for that mechanism rather than separate agents.

## Goals and prerequisites

Bring the Chapter 4 state store, Chapter 5 session/context records and Chapter 6 active procedure. No queue, outbox, delivery-guarantee or state-machine knowledge is assumed. Introduce those ideas with paper records and a single worker before using their technical names.

By the end you will be able to:

1. Persist a request under a stable source identity and explain exact duplicate versus conflicting duplicate.
2. Admit or reject work before invoking a model, with explicit capacity and session rules.
3. Claim one pending assignment and connect it to the existing learner-owned loop.
4. Complete work and create its report in one transaction, so a committed completion cannot lose its report locally.
5. Separate completed business work from confirmed, pending or uncertain outbound delivery.
6. Explain which crash cases the single-worker introduction handles and which require Chapter 12's ownership recovery.

## Concepts introduced from first use

An **inbox** is persisted input awaiting handling. A **queue** orders or selects work; it does not require a separate server. A **state machine** names allowed transitions so “pending,” “running” and “finished” cannot be arbitrary labels. A **source identity** names the external occurrence; a **session identity** groups conversations. Two messages with equal text can be separate occurrences, while one occurrence delivered twice must not become two jobs.

An **outbox** is a local record of an intended external report. It closes the gap between committing a result and remembering to send it. It does not make a database transaction extend across a network. If the recipient may have accepted a send before its reply disappeared, the outcome is **UNKNOWN**. A local retry cannot promise exactly-once external delivery unless the external service supplies and honors the required identity/reconciliation contract.

Derive these names from two failure experiments: restart an in-memory queue, then stop after completing work but before creating its report. Explain atomic state/report creation using the transaction built in Chapter 4. A SQL trigger may later express the same invariant; teach its implicit execution explicitly before replacing visible Python statements with it.

## Build, fail and repair

| Step | Build | Failure made visible |
| --- | --- | --- |
| 1 | Admit a request into a Python list | Process restart loses it |
| 2 | Persist identity, session, payload and pending state | Repeated intake must not create a second work item |
| 3 | Compare a duplicate's immutable fields | Reused identity with different content is a conflict |
| 4 | Add bounded admission and one atomic claim | Refused work must not call the model or occupy ordinary capacity |
| 5 | Route the claimed request through the existing loop | A hardcoded report would conceal that learner code was never invoked |
| 6 | Complete work, then separately insert a report | An injected crash leaves a completed assignment with no report |
| 7 | Put terminal state and report insertion in one transaction | The same crash leaves neither half committed |
| 8 | Claim report delivery and retain confirmed or unknown disposition | A lost remote reply cannot silently become permission to resend |

The first worker is deliberately single-process. Do not borrow the finished runtime's lease/generation implementation without teaching it. A crash while executing leaves a visible unresolved assignment; Chapter 12 adds fenced ownership, takeover and recovery. The initial lesson may refuse automatic replay rather than inventing a successful recovery.

## Ownership and dependency interfaces

The learner owns `admit(source_id, session_id, text)`, `claim(worker_id)`, `finish(work_id, result)` and the outbox repository. These names describe proposed chapter interfaces, not existing finished helper imports. Inject the state store and the Chapter 3 loop so the data path can be observed directly.

Admission outcomes distinguish accepted, identical duplicate, conflicting duplicate and capacity refusal. A claim on an empty queue returns no assignment and performs no model call. Completion binds the result to the specific claimed work identity. Report identity is immutable and distinct from work identity: later recovery may produce a different terminal generation without rewriting an already issued report.

The sender boundary receives one retained report and returns a known receipt or an explicit uncertain outcome. The core lesson uses a controlled fake transport with an independent accepted-send log. Telegram's adapter in Chapter 8 supplies authenticated intake and its polling cursor, but may only acknowledge intake after the shared admission transaction commits. Chapter 9's clock/stock producers use the same admission contract.

Do not conflate authentication and deduplication. Knowing that an occurrence is new does not establish who authorized it. The adapter is responsible for authenticated identity; the queue retains it without allowing generated text to replace it.

## Unit A — Construct and connect, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict which requests survive a list-backed restart | State sketch |
| 10–25 | Build the work schema with source/session identities | Persisted sample request |
| 25–40 | Implement admission and distinguish duplicate/conflict | Authored dispositions |
| 40–55 | Add bounded admission and single-worker claim | Empty/capacity/claim observations |
| 55–75 | Connect the learner loop and atomically retain result/report | Input-to-result data trace |
| 75–85 | Reopen the store and inspect the independent report row | Durable observation |
| 85–90 | Explain the unresolved worker-crash case | Recall and handoff notes |

## Unit B — Diagnose and transfer, 90 minutes

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict crashes before and after commit | Expected work/report states |
| 10–25 | Reproduce the completed-without-report defect | Independent failure evidence |
| 25–45 | Repair completion atomicity and propagate errors | Both rollback and commit cases |
| 45–60 | Simulate remote acceptance followed by a lost reply | UNKNOWN plus independent accepted-send log |
| 60–75 | Transfer to a second session, repeated input and rejected intake | No duplicate work or unauthorized call |
| 75–85 | Break the learner finish implementation deliberately | Checker fails through the integrated path |
| 85–90 | Explain why outbox persistence is not exactly-once networking | Written answer |

## Independent acceptance examples

| Given and action | Expected observation |
| --- | --- |
| Empty queue, one worker poll | No work and zero model invocations |
| Admit source s1 twice with identical session and text | One work record and a duplicate disposition |
| Reuse s1 with different text | Conflict; original text and state unchanged |
| Admit s2 with the same text as s1 | Two work records because occurrence identities differ |
| Fail between terminal state and report insertion | Reopen shows neither terminal change nor new report |
| Commit finish, then stop before sender runs | One completed work item and one pending report survive |
| Fake service accepts r1 but loses its response | One externally accepted send, local UNKNOWN and no automatic second send |
| Second terminal generation legitimately creates r2 | Both immutable reports remain attributable to their own generation |
| Learner finish is replaced with a no-op | The integrated observer fails; supplied runtime cannot rescue the test |

Completion requires the chapter's code to be consumed by Telegram and scheduling, not merely demonstrated beside them. Both notebook/Markdown pairs, worked answers, educator cases and the checkpoint must execute with learner-owned admission and completion.

Continue to [Chapter 8: Telegram](../ch08/profrod-sovereign-agent-ch08-telegram-messaging-chapter.md). [Exercise Book](../../exercises/ch07/profrod-sovereign-agent-ch07-durable-inbox-outbox-exercise-guide.md) · [Solutions Book](../../solutions/ch07/profrod-sovereign-agent-ch07-durable-inbox-outbox-solutions-guide.md) · [Textbook contents](../profrod-sovereign-agent-textbook-start-here.md).

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
