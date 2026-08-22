# Migration from v0.3 to v0.4

v0.4 never rewrites a live v0.3 runtime root. Copy the tree, then open the
copy:

```python
from pathlib import Path
from sovereign_agent.operations import migrate_v03_copy_on_write

upgraded = migrate_v03_copy_on_write(Path("runtime-v03"), Path("runtime-v04"))
```

Rollback is restoring the original tree. `layout_version` 1 roots remain
readable by v0.4 until you choose to migrate.

The 152-symbol `sovereign_agent.__all__` surface is unchanged. v0.4
packages (`api`, `admission`, `connectors`, `approvals`, `plugins`,
`service`, `operations`) are importable internals until a later minor
promotes selected names.
