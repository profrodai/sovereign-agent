# Public API stability

This contract applies to Sovereign Agent 1.x. The 0.x public surface ended at
the 0.7 line and is preserved by the immutable `v0.7.0` tag and the historical
`public-api-v0.*.txt` manifests.

## Supported import surface

The top-level names in `sovereign_agent.__all__` are the supported library API:

```python
from sovereign_agent import (
    Actor,
    Organization,
    Outcome,
    Refusal,
    StatementOfWork,
    __version__,
    new_id,
)
```

The source-budget gate verifies this list mechanically. Direct imports from
other modules are implementation-level integration points unless a current 1.x
document explicitly says otherwise.

## Compatibility promise

Within a 1.x minor line, patch releases do not intentionally:

- remove a supported top-level name;
- add a required parameter to its documented call surface;
- narrow accepted input types or return types incompatibly;
- change a documented exception to an unrelated type;
- weaken an authority, persistence, evidence, or fail-closed guarantee.

Patch releases may add optional parameters, new names, diagnostics, checks, and
bug fixes that restore documented behavior. A change to the supported surface
requires tests, documentation, and a changelog entry.

## Internal modules

Names absent from `__all__` may evolve as the executable textbook improves.
Some are intentionally readable and tested because the chapters teach them;
readability does not silently promote them to the compatibility surface.

Use the [task-oriented reference](api_reference.md) for the supported objects
and the [0.7-to-1.x migration guide](migration-v0.7-to-v1.md) for the retired
framework.
