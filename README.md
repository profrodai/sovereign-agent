# Sovereign Agent

**The executable textbook for Zero-Employee Organizations.**

Sovereign Agent 1.x is a small Python reference implementation for learning how
an outcome becomes governed work performed by accountable actors. Production
organizations graduate to [Zero Employee](https://github.com/zeroemployeeorg).

The 1.x API intentionally replaces the v0.7 fleet framework. To keep using that
framework:

```bash
pip install "sovereign-agent<1"
```

## Educational development install

Python 3.14 is required.

```bash
python -m pip install -e .
sovereign-agent doctor
```

Expected result:

```text
Sovereign Agent doctor
  Python:   3.14.x OK
  Pydantic: 2.x OK
  Network:  not required
  Tokens:   not required
  Providers:
    scripted available (streaming)
    claude   missing executable
    ...
Ready for the offline curriculum. Live providers are optional.
```

Chapter 0 is runnable as a **manually dispatched** store shift (no Pulse):

```bash
sovereign-agent demo store --mode simulated
```

See [`book/ch00_first_shift`](book/ch00_first_shift/README.md) and
[`book/ch03_actor_is_not_a_model`](book/ch03_actor_is_not_a_model/README.md).

## Product vocabulary

| Thing | Canonical word |
| --- | --- |
| Package and CLI | `sovereign-agent` |
| Control loop | `supervisor` |
| Installed OS hosting | `service` |
| Proactive wake | `pulse` |
| Intelligence CLI | `provider` |
| Governed identity | `actor` |

## Unit 1 gates

```bash
python -m pytest -q
python scripts/verify_runtime_dependencies.py
python scripts/verify_source_budget.py
sovereign-agent --help
sovereign-agent doctor
```

See the [educational reset ruling](docs/rulings/2026-08-25-educational-reset.md)
and [v0.7 migration guide](docs/migration-v0.7-to-v1.md).
