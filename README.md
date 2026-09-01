# Sovereign Agent

**The executable textbook for Zero-Employee Organizations.**

Sovereign Agent 1.x is a small Python reference implementation for learning how
an outcome becomes governed work performed by accountable actors. Production
organizations graduate to [Zero Employee](https://github.com/zeroemployeeorg).

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

Chapter 0 is runnable as a **manually dispatched** store shift (no Pulse):

```bash
uv run sovereign-agent demo store --mode simulated
```

See [`book/ch00_first_shift`](book/ch00_first_shift/README.md) and
[`book/ch03_actor_is_not_a_model`](book/ch03_actor_is_not_a_model/README.md).

## Product vocabulary

| Thing | Canonical word |
| --- | --- |
| Package and CLI | `sovereign-agent` |
| Control loop | `supervisor` |
| Installed OS hosting | `service` |
| Proactive wake | `pulse` |
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
python -m pytest -q
python scripts/verify_runtime_dependencies.py
python scripts/verify_source_budget.py
sovereign-agent --help
sovereign-agent doctor
```

See the [educational reset ruling](docs/rulings/2026-08-25-educational-reset.md)
and [v0.7 migration guide](docs/migration-v0.7-to-v1.md).
