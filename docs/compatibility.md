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
| 0.5.1+ (current public 0.5 line) | `>=0.5,<0.6` | 3.13+ |

v0.4 was a git-line capability, not a public PyPI replacement for 0.2.0.
The matrix records the last *published* pair, not every git tag.
