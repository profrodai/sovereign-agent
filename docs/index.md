# Sovereign Agent documentation

Sovereign Agent 1.x is an executable textbook for learning how an outcome
becomes governed work performed by accountable actors. It is a compact Python
reference implementation, not the production Zero Employee control plane.

## Start here

1. [Install and run the quickstart](quickstart.md).
2. Work through the [executable book](../book/README.md).
3. Read the [architecture](architecture.md) when you want to connect a chapter
   concept to the production modules.
4. Use the [API reference](api_reference.md) and
   [compatibility policy](compatibility.md) when integrating the package.

The default curriculum is offline and deterministic. Live provider CLIs are
optional and credentialed execution is never required by the default test suite.

## Current 1.x reference

- [Architecture](architecture.md)
- [Public API and stability contract](API.md)
- [Task-oriented API reference](api_reference.md)
- [Persistence boundary](persistence-boundary.md)
- [Durable non-goals](non-goals.md)
- [Security policy](../SECURITY.md) and [threat model](threat-model.md)
- [Migration from 0.7 to 1.x](migration-v0.7-to-v1.md)
- [Rulings index](rulings/index.md)

## Historical 0.x documentation

Files named `v0.*`, `migration-v0.*`, the legacy tutorials, generated-reference
stubs, and release notes describe the retired pre-1.0 framework. They remain in
the repository so old releases and migration decisions stay auditable; they are
not a guide to the code on `main`. See [Historical documentation](history.md)
before following one of those pages.

## Repository map

| Path | Purpose |
| --- | --- |
| `src/sovereign_agent/` | The small governed-organization implementation and CLI. |
| `src/reference_organizations/store/` | Lucy's store domain used by the book. |
| `book/` | Reader-facing chapters, solutions, instructor notes, and labs. |
| `tests/` | Behavioral and adversarial proof matrix. |
| `scripts/` | Release, curriculum, proof-pack, and repository verifiers. |
| `docs/` | Current reference plus explicitly retained historical records. |
| `.github/` | Provider-neutral GitHub automation and contributor templates. |

Local editor, model-provider, credential, build, and session state does not
belong in the public source tree.
