# Sovereign Agent

**An always-on AI agent you can read end to end, in Python.**

[![CI](https://github.com/profrodai/sovereign-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/profrodai/sovereign-agent/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/sovereign-agent.svg)](https://pypi.org/project/sovereign-agent/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Sovereign Agent runs Lucy's ice cream shop unattended. It answers her messages, keeps stock,
orders from suppliers within the spending she approved, survives a worker crash without ordering
twice, and reports its day from receipts rather than from what the model said. Everything an
agent harness needs is here, small enough to read: the model and tool loop, typed tools, durable
SQLite state, memory with retrieval, versioned skills, a durable work queue, messaging and
schedules, approvals bound to the exact spend, idempotent external actions, leases and fencing for
recovery, execution isolation, evaluation, controlled improvement and bounded delegation. Python
3.14, SQLite and one runtime dependency, Pydantic.

**If it helps you understand how agents really work, [star the repository](https://github.com/profrodai/sovereign-agent)**:
it is how other engineers find it.

## Build it yourself, one chapter at a time

This repository is the finished agent. The way to understand it is to build it:

- **Read the book:** [*Build Your Always-On AI Agent From Scratch*](https://profrod.ai/book) on
  profrod.ai. Twenty chapters, each measuring its mechanism on real local models before building
  it.
- **Do the exercises:** [the book's course](https://github.com/profrodai/profrodai-resources/tree/main/courses/sovereign-agent-book)
  in profrodai-resources. 38 ninety-minute notebook units that open in Colab, worked solutions,
  educator guides, and each chapter's checkpoint code, which runs against this package.
- **Join the learner community:** [profrod.ai/community](https://profrod.ai/community). Bring a
  result, a question or a failure you learned from.

Its final checkpoint runs a whole shop day: a separate simulated supplier loses replies, a worker is
killed, and the agent verifies two purchases totaling USD 26.00 without a duplicate order.

```bash
git clone https://github.com/profrodai/profrodai-resources.git
cd profrodai-resources/courses/sovereign-agent-book
make setup run
```

For an initialized shop directory, `sovereign-agent agent report --root PATH` prints the current
ledger-derived report. Amounts come from structured records, with uncertain outcomes and
accounting disagreements made explicit.

Always-on means unattended work and explicit restart and recovery while the host and its
dependencies are available. The book's [deployment chapter](https://profrod.ai/book/ch19-operation)
gives the one-host recipe. Maintained production organizations can graduate to
[Zeocore](https://github.com/profrodai/zeocore).

## Install and run with uv

[`uv`](https://docs.astral.sh/uv/) is the supported way to install and run
sovereign-agent. Try it without installing anything permanent:

```bash
uvx sovereign-agent@latest doctor
uvx sovereign-agent@latest demo store --mode simulated --root /tmp/first-shift
```

(`@latest` makes uv refresh its cached tool environment, so you always get
the current release.)

Or install the CLI onto your PATH:

```bash
uv tool install sovereign-agent
sovereign-agent doctor
```

(Plain `pip install sovereign-agent` still works in any Python 3.14
environment if you prefer it.)

The 1.x API intentionally replaces the v0.7 fleet framework. To keep using that
framework: `uvx "sovereign-agent<1"`.

## Educational development install

Python 3.14 is required; `uv` provides it automatically.

```bash
uv sync
uv run sovereign-agent doctor
```

Expected result:

```text
Sovereign Agent doctor
  Python:   3.14.x OK
  Pydantic: 2.x OK
  Network:  not required
  Tokens:   not required
  Providers:
    scripted available (streaming)
    claude   missing executable
    ...
Ready for the offline curriculum. Live providers are optional.
```

The runtime also provides a **manually dispatched** store-shift demo (no Pulse):

```bash
uv run sovereign-agent demo store --mode simulated
```

For additional runtime demonstrations, run the six advanced mechanisms with no provider,
credential, or network:

```bash
uv run sovereign-agent mechanisms --root /tmp/sovereign-agent-mechanisms
```

This demonstrates four-plane isolation policy, durable condition scheduling,
recoverable context compaction, session-incarnation fencing, bounded tool
discovery, and provenance-bearing hybrid memory. The book at
[profrod.ai/book](https://profrod.ai/book) builds each of them from first principles.

## Product vocabulary

| Thing | Canonical word |
| --- | --- |
| Package and CLI | `sovereign-agent` |
| Control loop | `supervisor` |
| Installed OS hosting | `service` |
| Proactive wake | `pulse` |
| Liveness proof | `heartbeat` (records the runtime was alive; never creates work) |
| Intelligence CLI | `provider` |
| Governed identity | `actor` |

An actor is not a model. Every provider receives the same governed assignment
envelope and must emit a valid terminal event and write the exact
`ActorReport`. A zero exit without both is a failed receipt. Cursor's
`--workspace` is directory selection, not sandboxing; isolation belongs to
Sovereign Agent's disposable workspace.

Provider subprocesses receive only base process variables plus documented
credential allowlists: Claude (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
`CLAUDE_CODE_OAUTH_TOKEN`), Codex (`CODEX_API_KEY`), and Cursor
(`CURSOR_API_KEY`). Other parent secrets are not forwarded.

## Unit 1 gates

```bash
uv run python -m pytest -q
uv run python scripts/verify_runtime_dependencies.py
uv run python scripts/verify_source_budget_v2.py
uv run sovereign-agent --help
uv run sovereign-agent doctor
```

See the [educational reset ruling](docs/rulings/2026-08-25-educational-reset.md)
and [v0.7 migration guide](docs/migration-v0.7-to-v1.md).

## Project resources

- [The book](https://profrod.ai/book) and [its exercises](https://github.com/profrodai/profrodai-resources/tree/main/courses/sovereign-agent-book)
- [Architecture](docs/architecture.md) and [API reference](docs/api_reference.md)
- [Contributing guide](CONTRIBUTING.md)
- [Support](SUPPORT.md) and [security policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
