# Build your first agent

In this tutorial you will build a small agent that turns a topic into a study
plan. The agent receives one read-only capability and writes its final answer
into an auditable session.

## Create the project

```bash
mkdir study-agent
cd study-agent
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install "sovereign-agent~=0.7.0"
sovereign-agent doctor --skip-llm
```

Configure a model as described in the [Quickstart](../quickstart.md#3-configure-a-model).

## Write the agent

Create `agent.py`:

```python
from pydantic import BaseModel, Field
from sovereign_agent import Config, run_task
from zeo_core.contracts import CapabilityResult, EffectKind
from zeo_core.tools import ToolContext, bound_capability_of, capability


class SyllabusQuery(BaseModel):
    topic: str
    level: str = Field(description="beginner, intermediate, or advanced")


@capability(
    id="tutorial.syllabus.lookup@1.0.0",
    description="Return trusted learning objectives for a topic and level.",
    effects={EffectKind.READ},
)
def lookup_syllabus(
    request: SyllabusQuery, ctx: ToolContext
) -> CapabilityResult:
    objectives = {
        "python": [
            "values, variables, and control flow",
            "functions and modules",
            "files, errors, and tests",
        ]
    }
    return CapabilityResult.ok(
        data={"topic": request.topic, "objectives": objectives.get(request.topic.lower(), [])},
        msg="Syllabus fixture returned.",
    )


result = run_task(
    "Create a three-session beginner study plan for Python. "
    "Use only objectives returned by the syllabus capability.",
    config=Config.from_env(),
    extra_capabilities=[bound_capability_of(lookup_syllabus)],
)

if not result.success:
    raise SystemExit(result.summary)

print(result.summary)
print(f"Audit files: {result.session_dir}")
```

Run `python agent.py`. Sovereign Agent creates a session, asks the planner for
subgoals, lets the executor call the capability, and records the result.

## Verify grounding

Read the trace and compare the final answer with the capability output:

```bash
sovereign-agent report <session-id>
```

For production scenarios, automate this comparison. The
[research assistant example](https://github.com/zeroemployeeorg/sovereign-agent/tree/main/examples/research_assistant)
demonstrates a dataflow integrity audit that rejects citations not returned by
its lookup.

## Extend it

Replace the in-memory fixture with a trusted data source, keep the same typed
request and result, and add a test before changing the model prompt. Continue
with [Author typed capabilities](capabilities.md).
