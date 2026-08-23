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
| Know what is deliberately out of scope | [Non-Goals](non-goals.md) |
| See the post-v0.5 sequence | [Roadmap](roadmap.md) |

## Key properties

- **Offline-testable.** The framework ships with `FakeLLMClient` so you can write deterministic tests for your agent's trajectory without burning API credits.
- **Auditable by default.** Every action the agent takes produces a ticket with a verified manifest. `cat`ing the session directory tells you exactly what happened.
- **Provider-agnostic.** Any OpenAI-compatible endpoint works. Nebius Token Factory is the default.
- **Explicit surface area.** 161 public names in `sovereign_agent.__all__`, checked
  against a versioned manifest.

## Status

Alpha. The declared package and documentation version is **0.6.0**. Python
3.13 is the floor and `zeocore>=0.5,<0.6` is required. Reusable actions are
ZeoCore capabilities; runtime commands stay in Sovereign Agent. A git tag is
not a public release — see [the roadmap](roadmap.md).

The spine is covered by deterministic contract, unit, and integration tests.
Memory, voice, and the observability backends (Evidently, OTel) are
skeletons with clear TODOs, not implementations. The Rasa-based structured half is
an optional extra with no implementation in this tree. The Docker worker backend
is a stub that raises `NotImplementedError`.

See the [CHANGELOG](https://github.com/zeroemployeeorg/sovereign-agent/blob/main/CHANGELOG.md)
for what shipped, [API Stability](API.md) for what is promised, and
[Non-Goals](non-goals.md) for what will not be attempted through v0.7.

## License

Apache 2.0.
