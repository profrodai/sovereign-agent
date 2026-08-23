# sovereign-agent

**Build auditable AI agents that run on infrastructure you control.**

[![CI](https://github.com/zeroemployeeorg/sovereign-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/zeroemployeeorg/sovereign-agent/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/sovereign-agent.svg)](https://pypi.org/project/sovereign-agent/)
[![Python](https://img.shields.io/pypi/pyversions/sovereign-agent.svg)](https://pypi.org/project/sovereign-agent/)
[![License](https://img.shields.io/pypi/l/sovereign-agent.svg)](LICENSE)

sovereign-agent is a Python framework for agents whose state, work, and audit
trail remain inspectable on disk. A session is a directory: you can debug it
with ordinary tools, move it between machines, and recover it after a crash.

Version 0.7 is alpha software. Read the [current limitations](#current-limitations)
before using it for important work.

Current release: **v0.7.0.**

## Install

Python 3.13 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install "sovereign-agent~=0.7.0"
sovereign-agent doctor --skip-llm # offline; no API key required
```

For a zero-cost working agent, clone this repository and run the deterministic
research example:

```bash
git clone https://github.com/zeroemployeeorg/sovereign-agent.git
cd sovereign-agent
python -m pip install -e .
python -m examples.research_assistant.run
```

Next, follow the [Quickstart](docs/quickstart.md) to add a typed capability,
connect an OpenAI-compatible model, run a task, and inspect its trace.

## Your first agent

Reusable actions are [ZeoCore](https://pypi.org/project/zeocore/) capabilities.
Sovereign Agent adds session management, planning, execution, runtime commands,
and evidence. The older `register_tool` decorator remains available only during
its documented compatibility window; new code should use `@capability`.

```python
from pydantic import BaseModel
from sovereign_agent import Config, run_task
from zeo_core.contracts import CapabilityResult, EffectKind
from zeo_core.tools import ToolContext, bound_capability_of, capability


class WeatherQuery(BaseModel):
    city: str


@capability(
    id="demo.weather.get@1.0.0",
    description="Get the current weather for a city.",
    effects={EffectKind.READ},
)
def get_weather(request: WeatherQuery, ctx: ToolContext) -> CapabilityResult:
    return CapabilityResult.ok(
        data={"city": request.city, "temperature": 18, "condition": "rainy"},
        msg="Weather fixture returned.",
    )


result = run_task(
    "What is the weather in Edinburgh?",
    config=Config.from_env(),
    extra_capabilities=[bound_capability_of(get_weather)],
)
print(result.summary)
print(result.session_dir)
```

Set a provider key before running this program. Nebius is the default; any
OpenAI-compatible endpoint can be configured:

```bash
export NEBIUS_KEY="..."
python weather_agent.py
```

The result is stored under `sessions/sess_<id>/`:

```text
session.json       lifecycle and ancestry
SESSION.md         task context
workspace/         files produced by the agent
tickets/           append-only operation records
logs/trace.jsonl   planner, executor, and capability events
ipc/               durable handoffs and completion signals
```

Inspect it with:

```bash
sovereign-agent sessions list
sovereign-agent sessions show <session-id>
sovereign-agent report <session-id>
```

## Choose a learning path

- **I want to build an agent:** start with the
  [Quickstart](docs/quickstart.md), then work through the
  [tutorials](docs/tutorials/index.md).
- **I learn by examples:** use the [example catalog](examples/README.md). All
  nine scenarios run offline; live modes are explicitly marked.
- **I want to understand the internals:** complete the five
  [build-from-scratch chapters](chapters/README.md).
- **I operate agents:** read the [deployment guide](docs/deployment.md), then
  the [v0.7 fleet operator guide](docs/v0.7-operator.md).
- **I need a class or function:** use the
  [API reference](docs/api_reference.md) and
  [API stability contract](docs/API.md).

## What the framework gives you

- **Filesystem sessions** — state and artifacts are visible, portable files.
- **Typed capabilities** — explicit inputs, effects, and structured results.
- **Planner/executor orchestration** — a reasoning half and a deterministic
  policy half connected by durable handoffs.
- **Tickets and manifests** — append-only evidence with SHA-256 verification.
- **Deterministic testing** — repository examples use scripted model responses,
  so learning and CI do not consume tokens.
- **Human approval and resume** — approval can arrive seconds or days later;
  no in-memory process must remain alive.
- **Bounded execution** — bare, OS-isolated, Docker, Podman, and SSH workers,
  with fail-closed placement and reconciliation.

The architectural rationale is in [Architecture](docs/architecture.md).

## Current limitations

- The package is **alpha**. Read code you make load-bearing and pin to
  `~=0.7.0`.
- Python 3.13+ and `zeocore>=0.5,<0.6` are required.
- Memory retrieval/consolidation, voice, and the Evidently/OTel backends are
  scaffolding, not production implementations.
- Docker and Podman workers require an available engine and a digest-pinned
  image. SSH requires pinned host identity. Requested isolation fails closed.
- Real model runs cost money and may vary. Every tutorial starts offline where
  possible and labels networked steps.

See [Non-goals](docs/non-goals.md), the
[threat model](docs/threat-model.md), and the
[v0.7 release notes](docs/release-notes/0.7.0.md).

## Develop and contribute

```bash
git clone https://github.com/zeroemployeeorg/sovereign-agent.git
cd sovereign-agent
make first-run
make test
make docs-strict
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete workflow and
[SECURITY.md](SECURITY.md) for private vulnerability reporting.

## License

[Apache 2.0](LICENSE).
