# Compatibility

## Current 1.x line

| Component | Supported contract |
| --- | --- |
| Python | 3.14 or newer |
| Direct runtime dependency | `pydantic>=2,<3` |
| Operating systems | Platform-independent core; provider CLIs and shell examples depend on their host |
| Default tests | Offline, deterministic, no credentials |
| Package typing | Inline annotations with a shipped `py.typed` marker |

The lockfile records the tested development environment. The package metadata,
not the lockfile, defines the runtime dependency range users install.

Claude, Codex, and Cursor adapters invoke external executables and probe their
availability and supported flags at runtime. The OpenAI-compatible adapter runs
inside Sovereign Agent and reports configured availability without contacting
its endpoint; actual invocation still fails honestly if that endpoint is
unreachable. Optional providers never prevent the scripted offline curriculum
from running.

## Versioning

The supported top-level import contract is documented in [API.md](API.md).
Patch releases remain compatible within the current 1.x minor line. Persistence
migrations run forward and preserve existing canonical rows or fail closed.

## Historical 0.x line

The 0.7 framework used Python 3.13 and ZeoCore and exposed a much larger API. It
is not source-compatible with 1.x. Install it with an explicit `<1` constraint
and read the [migration guide](migration-v0.7-to-v1.md) and
[historical documentation map](history.md). The `v0.7.0` tag is immutable.
