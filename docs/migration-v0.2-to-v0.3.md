# Migrating from v0.2 to v0.3

v0.3.0 is additive at the top-level Python API: all 67 symbols published in
`sovereign_agent.__all__` at v0.2.0 remain exported with compatible signatures.
The machine-checked manifests are
[`public-api-v0.2.txt`](public-api-v0.2.txt) and
[`public-api-v0.3.txt`](public-api-v0.3.txt).

## Required action

Change the dependency constraint only after running your tests:

```text
sovereign-agent>=0.3,<0.4
```

Existing imports do not need to change. In particular:

- `run_task(...)` remains the synchronous convenience wrapper. It now reaches
  the same `NativeProvider` protocol used by governed execution; it is not a
  separate legacy execution engine.
- `ToolRegistry`, `register_tool`, `global_registry`, and
  `make_builtin_registry` retain their stable imports. Existing registries can
  still be passed as `extra_tools`.
- v0.2 session schema version 1 remains readable. Missing additive fields use
  their v0.2 defaults. Loading does not rewrite a session; a resumed execution
  creates a new child directory and records `resumed_from`, so migration is
  copy-on-write and the parent remains byte-for-byte unchanged.

## New opt-in surfaces

v0.3 adds native Codex/Claude CLI providers, governed repository execution,
durable seat registry/relay, execution receipts, and worker lifecycle APIs.
They do not activate merely because the package is imported. Live provider
probes are opt-in and require the operator to name the credential/provider.
The deterministic test and release gates use recorded provider fixtures.

## Deprecations

v0.3.0 introduces no public deprecations. No v0.2 public symbol emits a
deprecation warning. Future deprecations will remain functional for at least
one complete minor release after the warning first ships, identify a
replacement, and be listed in the changelog and migration guide before removal.

## Compatibility boundaries

- Python 3.12+ remains required.
- The core install works without optional voice, telemetry, Evidently, Rasa, or
  Docker packages.
- `DockerWorker` remains an unavailable compatibility placeholder. Selecting it
  fails explicitly; installing the `docker` extra does not implement a backend.
- Filesystem isolation constrains filesystem access only. It is not a claim of
  network isolation.
