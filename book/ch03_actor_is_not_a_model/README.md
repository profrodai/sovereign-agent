# Chapter 3 — The actor is not a model

## Status: runnable (offline)

An actor is a governed identity with a role and authority. A provider is an
external intelligence CLI: `scripted`, `claude`, `codex`, or `cursor`. Binding
`operator-course` to `claude` does not make Claude the operator. The same
actor can be rebound to `scripted` without changing the outcome, the SOW, or
the evidence rules.

Cursor is a first-class adapter, equal to Claude and Codex. It is not a
documentation bridge.

Default tests never call those CLIs. They parse committed fixtures. Live
probes are opt-in and must not be in default CI:

```bash
python -m pytest -q -m live
```

Those probes run `--help` / `--version` only. They do not submit prompts.

`solution.py` imports the production registry rather than copying it.
