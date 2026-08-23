# Quickstart

## Install

```bash
pip install sovereign-agent            # core
```

Requires Python 3.13+. `zeocore>=0.5,<0.6` is required.

Dev tooling is a PEP 735 dependency *group*, not an extra, so there is no
`[dev]` to install. From a checkout:

```bash
uv sync --group dev                    # or: pip install -e . --group dev
```

Optional extras that do something: `[evidently]`, `[otel]`, `[voice]`, `[rasa]` —
and note that the Evidently and OTel backends are stubs today. The `[docker]`
extra installs the Docker SDK but there is no working Docker code path; see
[non-goals](non-goals.md).

## Preflight

```bash
export NEBIUS_KEY="your-nebius-api-key"
sovereign-agent doctor
```

Doctor checks your Python version, API key, disk space, mount allowlist, and (unless you pass `--skip-llm`) makes one real LLM call. If everything reads ✓, you're ready.

## Minimal agent

New work should author reusable actions with ZeoCore `@capability` and merge
them with Sovereign runtime commands via `make_session_callable_surface`.
`@register_tool` still runs through `run_task` and is deprecated.

```python
from pydantic import BaseModel
from zeo_core.contracts import CapabilityResult, EffectKind
from zeo_core.tools import ToolContext, capability
from sovereign_agent import run_task, Config

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
        msg="ok",
    )

config = Config.from_env()
result = run_task("What's the weather in Edinburgh?", config=config)
print(result.summary)
```

Under the hood this creates a session directory at `sessions/sess_<id>/`, runs a
planner, runs an executor against the callable surface, and returns a summary.
Each invocation is an audit-traceable ticket.

## Inspect what happened

```bash
sovereign-agent sessions list
sovereign-agent sessions show <session_id>
sovereign-agent report <session_id>
```

The report command renders the complete session trace as markdown — timeline, tickets, handoffs, final result.

## Next steps

- Walk through the [chapters](chapters/index.md) to see how the framework is built from scratch.
- Read the [architecture doc](architecture.md) for the full rationale.
- Look at `examples/research_assistant/`, `examples/code_reviewer/`, `examples/pub_booking/` in the repo for end-to-end scenarios you can clone and modify.

## Swapping providers

Any OpenAI-compatible endpoint works:

```python
from sovereign_agent import Config

config = Config(
    llm_base_url="https://api.openai.com/v1/",
    llm_api_key_env="OPENAI_API_KEY",
    llm_planner_model="gpt-4",
    llm_executor_model="gpt-4o-mini",
)
```

## Offline testing

```python
from sovereign_agent._internal.llm_client import FakeLLMClient, ScriptedResponse
from sovereign_agent.planner import DefaultPlanner

client = FakeLLMClient([
    ScriptedResponse(content='[{"id": "sg_1", ...}]'),
    # ...
])
planner = DefaultPlanner(model="fake", client=client)
```

This is how every sovereign-agent test runs — deterministic, offline, fast.
