# Quickstart

This guide verifies the installation offline, runs a deterministic agent, then
connects a model and gives it one typed capability. You need basic Python, a
terminal, and Python 3.13 or newer.

## 1. Install

=== "macOS and Linux"

    ```bash
    python3.13 -m venv .venv
    source .venv/bin/activate
    python -m pip install "sovereign-agent~=0.7.0"
    ```

=== "Windows PowerShell"

    ```powershell
    py -3.13 -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install "sovereign-agent~=0.7.0"
    ```

Confirm the package and local environment without credentials or network calls:

```bash
sovereign-agent version
sovereign-agent doctor --skip-llm
```

`doctor --skip-llm` checks Python, configuration, disk space, and writable
runtime paths. It intentionally does not require an API key.

## 2. See an agent work offline

The repository includes scripted model responses so you can observe the full
planner/executor flow without spending money:

```bash
git clone https://github.com/zeroemployeeorg/sovereign-agent.git
cd sovereign-agent
python -m pip install -e .
python -m examples.research_assistant.run
```

The example plans a research task, calls a deterministic lookup capability,
writes a report, and audits that every cited paper came from the lookup result.
The final output tells you where artifacts were written.

!!! note
    Offline examples run from a source checkout because their scripted fixtures
    are teaching material, not part of the installed wheel.

## 3. Configure a model

Nebius is the default OpenAI-compatible provider:

```bash
export NEBIUS_KEY="your-key"
sovereign-agent doctor
```

For another OpenAI-compatible provider, set the endpoint, key variable name,
and models:

```bash
export OPENAI_API_KEY="..."
export SOVEREIGN_AGENT_LLM_BASE_URL="https://api.openai.com/v1/"
export SOVEREIGN_AGENT_LLM_API_KEY_ENV="OPENAI_API_KEY"
export SOVEREIGN_AGENT_LLM_PLANNER_MODEL="gpt-4o"
export SOVEREIGN_AGENT_LLM_EXECUTOR_MODEL="gpt-4o-mini"
```

See [Configuration and providers](how-to/configuration.md), including local
Ollama setup. A normal `doctor` call makes one small model request.

## 4. Give the agent a capability

Create `weather_agent.py`:

```python
from pydantic import BaseModel
from sovereign_agent import Config, run_task
from zeo_core.contracts import CapabilityResult, EffectKind
from zeo_core.tools import ToolContext, bound_capability_of, capability


class WeatherQuery(BaseModel):
    city: str


@capability(
    id="tutorial.weather.get@1.0.0",
    description="Get the current weather for a city.",
    effects={EffectKind.READ},
)
def get_weather(request: WeatherQuery, ctx: ToolContext) -> CapabilityResult:
    # Replace this fixture with an API call after the flow works.
    return CapabilityResult.ok(
        data={"city": request.city, "temperature_c": 18, "condition": "rainy"},
        msg="Weather fixture returned.",
    )


result = run_task(
    "What is the weather in Edinburgh?",
    config=Config.from_env(),
    extra_capabilities=[bound_capability_of(get_weather)],
)

print(result.summary)
print(f"Session: {result.session_id}")
print(f"Files: {result.session_dir}")
```

Run it:

```bash
python weather_agent.py
```

The model can call only capabilities and runtime commands exposed to it. The
description helps it choose an action; the typed request validates arguments;
the effect classification becomes policy and evidence.

## 5. Inspect the run

```bash
sovereign-agent sessions list
sovereign-agent sessions show <session-id>
sovereign-agent report <session-id> --output report.md
```

Or inspect the files directly:

```bash
ls sessions/<session-id>
cat sessions/<session-id>/logs/trace.jsonl
```

Every run has lifecycle state, task context, workspace artifacts, tickets,
manifests, and a JSONL trace. See
[Sessions and traces](tutorials/sessions-and-traces.md).

## What next?

- [Build a complete first agent](tutorials/first-agent.md).
- [Learn to author capabilities](tutorials/capabilities.md).
- [Test an agent deterministically](tutorials/testing.md).
- Browse all [nine examples](https://github.com/zeroemployeeorg/sovereign-agent/tree/main/examples).
- Learn the architecture through the [five chapters](chapters/index.md).
