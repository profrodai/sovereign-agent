# sovereign-agent

**A framework for building always-on AI agents that you actually own.**

## What is it

Two things in one codebase, plus one that is scaffolding only:

1. An **alpha Python framework** for always-on agents. `pip install sovereign-agent` and go — with the alpha caveats in [Status](#status) read first.
2. A **build-from-scratch tutorial** that reconstructs the framework in five runnable chapters, drift-checked against the library in CI.
3. A **research-vehicle scaffold** under `lessons/`. This is currently a template (`lessons/_template/`) and a rationale README. No lesson has been written yet, so treat it as intent rather than content.

The core idea: the agent's **session directory is the unit of everything**. Memory, work queue, logs, tickets — all live as files under `sessions/sess_<id>/`. Nothing important lives in a database. This makes agents debuggable, recoverable from crashes, and portable between machines.

## Where to start

| If you want to... | Start here |
|---|---|
| Install and run a task in 5 minutes | [Quickstart](quickstart.md) |
| Understand the architecture | [Architecture](architecture.md) |
| Learn by building it from scratch | [Chapters](chapters/index.md) |
| Look up a class or function | [API Reference](api_reference.md) |
| Know what is actually stable | [API Stability](API.md) |
| Deploy it on a real machine | [Deployment](deployment.md) |
| Know what is deliberately out of scope | [v0.3 Non-Goals](v0.3-non-goals.md) |

## Key properties

- **Offline-testable.** The framework ships with `FakeLLMClient` so you can write deterministic tests for your agent's trajectory without burning API credits.
- **Auditable by default.** Every action the agent takes produces a ticket with a verified manifest. `cat`ing the session directory tells you exactly what happened.
- **Provider-agnostic.** Any OpenAI-compatible endpoint works. Nebius Token Factory is the default.
- **Small surface area.** 76 public names in `sovereign_agent.__all__`. Readable in an afternoon.

## Status

Alpha. The declared version is **0.2.0**, and PyPI has exactly one release
(`0.2.0`). The tree additionally carries unreleased v0.3 work — channel adapters,
plugin registries, worker-backend dispatch, and a liveness monitor — that has not
been tagged or released.

The spine is implemented and covered by **370 collected tests** (369 pass, 1
skipped). Memory, voice, and the observability backends (Evidently, OTel) are
skeletons with clear TODOs, not implementations. The Rasa-based structured half is
an optional extra with no implementation in this tree. The Docker worker backend
is a stub that raises `NotImplementedError`.

See the [CHANGELOG](https://github.com/zeroemployeeorg/sovereign-agent/blob/main/CHANGELOG.md)
for what shipped, [API Stability](API.md) for what is promised, and
[v0.3 Non-Goals](v0.3-non-goals.md) for what will not be attempted.

## License

Apache 2.0.
