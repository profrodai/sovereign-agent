# Migration from v0.4 to v0.5

Two changes require action before upgrading.

**Python 3.13 is the floor.** v0.4 supported 3.12. Install a 3.13 interpreter
first (`uv python install 3.13`), then reinstall.

**`zeocore` is a required dependency.** It arrives automatically with
`pip install sovereign-agent` and brings `pydantic` transitively. The import
name is `zeo_core`.

## Renamed runtime evidence types

Runtime/provider/worker *evidence* is no longer called `Capability`:

| v0.4 | v0.5 |
|---|---|
| `Capability` | `RuntimeCapabilityAssertion` |
| `CapabilityManifest` | `RuntimeCapabilityManifest` |

The old names still import from `sovereign_agent.contracts` and emit a
`DeprecationWarning` through 0.5. They are the same objects, so `isinstance`
checks keep working. The JSON wire key is unchanged: a governed execution
request still serializes `capability_manifest`.

## Authoring reusable actions

New reusable actions should be ZeoCore capabilities rather than tools:

```python
from zeo_core.contracts import CapabilityResult, EffectKind
from zeo_core.tools import ToolContext, capability

@capability(id="acme.invoice.send@1.0.0", effects={EffectKind.WRITE})
def send_invoice(request: SendInvoice, ctx: ToolContext) -> CapabilityResult:
    ...
```

Session control (`complete_task`, `handoff_to_structured`) stays a Sovereign
runtime command. `make_session_callable_surface` merges capabilities and
commands into the single tools list the model sees.

`@register_tool`, `ToolRegistry`, `ToolResult`, and `make_builtin_registry`
remain public and deprecated; removal needs a separately approved breaking
release.

## Behaviour changes

`parallelism_policy="always"` is no longer a product option and raises at
construction. Use the default `"respect_tool_flags"` or `"never"`.

Executor traces no longer default to recording raw tool arguments; they
record a request digest instead.

The 152-symbol v0.4 `sovereign_agent.__all__` surface is a subset of v0.5's
161 symbols. Nothing was removed.
