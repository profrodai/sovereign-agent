# Historical documentation

Sovereign Agent 1.0 deliberately replaced the 0.7 fleet framework with a much
smaller educational organization. The `v0.7.0` tag remains immutable and the
old package remains installable with:

```bash
uvx "sovereign-agent<1"
```

The following repository areas are retained as historical evidence and may name
modules, commands, dependencies, examples, or architecture that do not exist on
`main`:

- `docs/v0.*`
- `docs/migration-v0.*` except the 0.7-to-1.x guide
- `docs/release-notes/`
- `docs/tutorials/`, `docs/how-to/`, `docs/concepts/`, `docs/chapters/`, and
  `docs/reference/`
- `docs/teaching-surface.md`, `docs/deployment.md`, and the branch-consolidation
  record
- `docs/public-api-v0.*.txt`

They are kept because release history and migration decisions should remain
inspectable. They are not silently rewritten to resemble 1.x. For current
material, return to the [documentation index](index.md), the
[book](../book/README.md), or the source under `src/`.
