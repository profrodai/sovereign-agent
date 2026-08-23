# Author typed capabilities

A capability is an action the model may request. Its Python definition is the
real boundary; prompt text is only guidance.

## The four parts

```python
@capability(
    id="acme.inventory.lookup@1.0.0",
    description="Look up current stock for one product SKU.",
    effects={EffectKind.READ},
)
def lookup_inventory(
    request: InventoryQuery, ctx: ToolContext
) -> CapabilityResult:
    ...
```

1. **ID** — use a stable, namespaced, versioned identifier.
2. **Description** — say when to call the capability and what it returns.
3. **Effects** — declare whether it reads, writes, or causes an external effect.
4. **Typed request/result** — validate model arguments and return structured
   evidence.

Bind definitions before passing them to `run_task`:

```python
extra_capabilities=[bound_capability_of(lookup_inventory)]
```

Runtime commands such as `complete_task` and `handoff_to_structured` are
provided by Sovereign Agent. Reusable domain actions belong in ZeoCore
capabilities. The older `@register_tool` API remains only for compatibility.

## Design rules

- Keep one capability focused on one action.
- Reject invalid or unauthorized requests in Python.
- Return source identifiers with data so grounding can be audited.
- Do not hide network writes behind a `READ` effect.
- Version behavior-changing contracts with a new capability ID.
- Never place credentials in results, traces, or descriptions.

## Run the canonical examples

```bash
python -m examples.research_assistant.run
python -m examples.capability_receipt.run
```

The first shows a capability used by a complete agent. The second shows
capability receipts and restart behavior. Both are deterministic and offline.

For the runtime composition API, see
[Capabilities in the API reference](../api_reference.md#capabilities-v05).
