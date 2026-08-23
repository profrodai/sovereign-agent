# ZeoCore compatibility

Sovereign Agent declares one tested ZeoCore minor range in
`pyproject.toml`: `zeocore>=0.5,<0.6`.

## CI matrix

GitHub Actions job `zeocore-compat` installs:

- the **minimum** allowed version (`zeocore==0.5.0`);
- the **newest** version that satisfies `zeocore>=0.5,<0.6`.

and runs the capability, contract, architecture-boundary, and release-source
suites.

## Compatibility review triggers

A ZeoCore upgrade that changes any of the following requires an explicit
review before the lockfile or lower bound moves:

- cancellation (`CancelledError` must not be swallowed; see
  [v0.5-unit1-foundation.md](v0.5-unit1-foundation.md) and
  [v0.5-unit2-adapter.md](v0.5-unit2-adapter.md));
- serialization of capability requests or results;
- provider projection names;
- request or invocation digests;
- effects;
- requirements;
- invocation-record shape or persistence.

Sovereign Agent wire schemas stay owned here even when a receipt carries
ZeoCore-derived evidence. Provider names are projections; canonical capability
IDs are the durable identity.

## Package pairs

Shipped as `sovereign_agent/contracts/fixtures/compatibility-matrix.json`:

| sovereign-agent | ZeoCore | Python |
|---|---|---|
| 0.2.0 (previous public PyPI line) | none | 3.12+ as published |
| 0.5.1 (truthful public 0.5 line) | `>=0.5,<0.6` | 3.13+ |
| 0.6.0 (capability-native default) | `>=0.5,<0.6` | 3.13+ |
| 0.7.0 (bounded execution fleet) | `>=0.5,<0.6` | 3.13+ |

## Sovereign-owned extensions

These are not ZeoCore types and are never monkey-patched into ZeoCore:

- runtime commands (`complete_task`, `handoff_to_structured`, `abort_execution`, `session_status`)
- admission and `ExecutionScope`
- durable capability approvals
- durable concurrency leases (ZeoCore declares mode; Sovereign acquires)
- frozen per-execution catalog persistence
- append-only invocation evidence linked from receipts
- `invoke_cancellable` / `invoke_capability` until upstream stops swallowing `CancelledError`

v0.4 was a git-line capability, not a public PyPI replacement for 0.2.0.
The matrix records published pairs plus the current line.
