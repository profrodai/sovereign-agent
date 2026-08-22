# Architecture

This page is the architecture summary for `sovereign-agent`. It is not a pointer
to a longer document elsewhere in this tree, because there is no longer document.

Earlier revisions of this page described a root `SOW.md` as "the authoritative
architecture document." No such file has ever existed in this repository, and it
is not going to be added. The reason is a repository boundary, not an oversight:

- **`work_repo`** — this repository. It holds code that genuinely collides, so
  work lands on branches and is merged through pull requests. What it owes you is
  readable code, this architecture summary, the API contract in
  [API stability](API.md), and the [CHANGELOG](https://github.com/zeroemployeeorg/sovereign-agent/blob/main/CHANGELOG.md).
- **`sow_repo`** — a separate corpus repository. Scoping and reporting live
  there, not here.

These are deliberately two different fields. A Statement of Work committed onto a
branch in a work repo is invisible to everyone who is not already on that branch,
which is exactly the failure mode the split exists to prevent. So: no `SOW.md` in
this tree, and no path in this tree that claims to be one.

For the current release-readiness picture, read
[CHANGELOG.md](https://github.com/zeroemployeeorg/sovereign-agent/blob/main/CHANGELOG.md)
and [v0.3 non-goals](v0.3-non-goals.md). Those are maintained; a checklist buried
in a spec document would not be.

## One sentence

sovereign-agent is a Python framework for building agents that run continuously, have persistent memory, and run on infrastructure you own — built around the observation that **the session directory is the unit of everything**.

## The nine architectural decisions

1. **Per-session filesystem isolation.** Every task gets its own directory under `sessions/sess_<id>/`. All state for that task lives there, nowhere else.
2. **SessionQueue with three guarantees.** Per-session serialization, global concurrency cap, retry with exponential backoff.
3. **Filesystem IPC with atomic rename.** Workers talk via JSON files written with `temp-file + rename`.
4. **Idle preemption via sentinel, not signal.** A `_close` file tells a worker to exit cleanly. No `SIGKILL`.
5. **Credential gateway.** API keys live in the orchestrator process environment; workers are injected at spawn time with per-tool scoping.
6. **Drift-corrected scheduler.** Recurring tasks anchor to their scheduled time, not `now()`. Missed intervals are skipped, not run back-to-back.
7. **Mount allowlist outside project root.** `~/.config/sovereign-agent/mount-allowlist.json` — a path the agent cannot reach.
8. **Graceful shutdown detaches, does not kill.** Running workers are logged as "detached" on SIGTERM and left alone. The next startup resumes them.
9. **Long operations are tickets with explicit state.** `pending → running → (success | skipped | error)`. SUCCESS requires a verified sha256 manifest. No manifest, no success.

## The four patterns from QuackVerse

- **Pattern A — Discovery.** Every extension implements `discover()` returning a JSON schema. Agents learn about extensions at runtime.
- **Pattern B — Summary artifact.** Every long operation emits a short LLM-readable summary alongside its raw output. The agent reads the summary; the audit log keeps the raw output.
- **Pattern C — Structured error taxonomy.** Errors carry machine-readable category codes (`SA_SYS_*`, `SA_VAL_*`, `SA_IO_*`, `SA_EXT_*`, `SA_TOOL_*`). Agents branch on category, not on exception class.
- **Pattern D — Manifest discipline.** A long operation has not succeeded until it has written a manifest with verified checksums. This catches LLM hallucinated success at the framework level.

## Why filesystem, not database

A database approach has five failure modes that the directory approach does not:

1. Databases are opaque to humans. Directories you `ls`.
2. Databases are hard to make atomic across multiple writes. Rename is atomic, per-file.
3. Databases couple the agent's lifetime to the database's. A directory is portable (`tar` it).
4. Databases hide the schema inside the database. The directory layout is the schema, and it's documented.
5. Databases don't scale to multiple agent halves sharing state without an API contract. Directories do — the directory is the API.

The cost is about 1s of polling latency for IPC, which is invisible for an agent system and unacceptable for high-frequency trading. Pick the cost that fits the problem.

## Why two halves (loop + structured)

Open-ended research and high-stakes rule-following are different kinds of work. The loop half uses an LLM with tools. The structured half uses explicit rules that are testable and auditable.

The planner decides which half gets which subgoal. The halves communicate only through the session directory — one writes a handoff file, the other picks it up.

This is the split Claude Code makes (ReAct loop for coding, structured dialogs for destructive operations). sovereign-agent makes it explicit and pluggable.

## Why two-stage planner + executor

Reasoning models plan well but are slow at tool use. Fast tool-calling models execute well but are less good at multi-step planning.

Split the roles: the planner produces subgoals; the executor runs each one through a ReAct loop. Empirically, this lifts task success by 15–30% on multi-step tasks while reducing total latency, because the executor moves much faster than a thinking model would.

## Where the rest of it lives

There is no single specification document to send you to. The material an SOW
would have carried is distributed across artifacts that are actually maintained:

| What you want | Where it is |
|---|---|
| Prior art and credits | [`CREDITS.md`](https://github.com/zeroemployeeorg/sovereign-agent/blob/main/CREDITS.md) |
| File-level specifications | The module docstrings. Every public module explains why it exists before it explains what it does. |
| Test obligations | `tests/`, and the CI workflow that gates them |
| What shipped, when | [`CHANGELOG.md`](https://github.com/zeroemployeeorg/sovereign-agent/blob/main/CHANGELOG.md) |
| What is deliberately deferred | [v0.3 non-goals](v0.3-non-goals.md) |
| What the public API promises | [API stability](API.md) |

Scoping and reporting for work on this repository live in the corpus repository
(`sow_repo`), not here. See the boundary note at the top of this page.
