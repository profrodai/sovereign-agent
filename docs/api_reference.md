# API reference

The supported 1.x import surface contains seven names. Full signatures and
field definitions live in the inline type annotations and docstrings shipped
with the package.

## `Organization`

```python
from pathlib import Path
from sovereign_agent import Organization

org = Organization.init(Path("/tmp/my-organization"))
```

`Organization` owns the local ledger and the governed lifecycle. Its teaching
methods create and activate outcomes, create and ready SOWs, assign and run
actors, verify and review work, accept outcomes, record rulings, inspect inboxes,
and query SOWs. The CLI is preferred for the first learning pass; library use is
appropriate when constructing a reference organization or a deterministic test.

Close `org.db` when a long-lived process no longer needs the organization.

## Boundary models

```python
from sovereign_agent import Actor, Outcome, StatementOfWork
```

- `Actor` is a governed identity with a role, authority, provider binding, and
  workspace policy.
- `Outcome` is a desired world condition and its declared acceptance checks.
- `StatementOfWork` is bounded work under one outcome, including scope,
  required role, effects, checks, deliverables, and state.

These are strict Pydantic models: unknown fields are refused rather than
silently ignored.

## `Refusal`

```python
from sovereign_agent import Refusal
```

`Refusal` is the expected fail-closed exception for an invalid or unauthorized
operation. It carries a user-facing problem, the governing reason, a check, a
repair action, and a machine-readable category. It is not a generic wrapper for
programming errors.

## `new_id`

```python
from sovereign_agent import new_id

outcome_id = new_id("out")
```

Creates a timestamped, prefixed identifier suitable for durable records. The
prefix names the record family; callers must not parse an ID to recover business
state.

## `__version__`

The source version is exposed as `sovereign_agent.__version__`. Installed tools
should prefer `importlib.metadata.version("sovereign-agent")` when they need the
distribution version.

## Advanced implementation modules

The book intentionally reads modules such as `fencing`, `pulse`, `heartbeat`,
`supervisor`, and `workspace`. They are executable teaching material, but they
are not added to the supported top-level surface merely by being documented.
Open a feature proposal before building a third-party integration on a private
or submodule-only name.
