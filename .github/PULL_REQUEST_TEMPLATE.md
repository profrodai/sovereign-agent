## Problem

What user-visible problem does this change solve?

## Approach

Why is this the smallest correct change? Name any public API, persistence,
provider, curriculum, or security-boundary effect.

## Evidence

- [ ] `make verify`
- [ ] `uv lock --check` when dependency metadata changed
- [ ] Tests fail without the change and pass with it, or the PR explains why a
      mechanical test is not possible
- [ ] Reader-facing commands and expected output were executed when changed

Paste concise results or link to the relevant CI run. Do not include secrets,
credentials, private prompts, or production organization databases.

## Documentation and compatibility

- [ ] Documentation and changelog updated when user-visible behavior changed
- [ ] Migration or compatibility impact stated, including "none"
- [ ] The change stays within the repository's documented security boundaries
