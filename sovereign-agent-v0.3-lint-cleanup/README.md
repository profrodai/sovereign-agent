# v0.3 lint-cleanup

A small one-off that brings the M1 + M2 patches into compliance with the
project's ruff configuration. Apply once, after both M1 and M2 have landed.

## What it fixes

| File | Issue | Rule | Fix |
|---|---|---|---|
| `orchestrator/main.py` | `adapters: "list[ChannelAdapter] \| None"` | UP037 | unquote (future-import makes the quotes unnecessary) |
| `orchestrator/main.py` | `adapter: "ChannelAdapter"` | UP037 | unquote |
| `orchestrator/main.py` | `auto_approver` import after `credentials` | I001 | reorder alphabetically |
| `orchestrator/main.py` | TYPE_CHECKING block out of order | I001 | reorder alphabetically |
| `tests/test_channels_*.py` | `from datetime import timezone` + `tzinfo=timezone.utc` | UP017 | switch to `from datetime import UTC` + `tzinfo=UTC` |
| `sovereign_agent/__init__.py` | channels re-exports flagged unused | F401 | rewrite as `X as X` (ruff's official re-export pattern) |

After the patcher runs, `install.sh` invokes `ruff format` + `ruff check --fix`
to canonicalize anything else (blank lines, trailing commas) that the
structural string-replace can't account for.

## Install

```bash
tar -xzf sovereign-agent-v0.3-lint-cleanup.tar.gz
cd sovereign-agent-v0.3-lint-cleanup
./install.sh
```

The installer detects flat vs src layout automatically.

## Idempotent

Re-running on a clean tree: 0 applied, 7 skipped. The patcher is robust to
prior auto-fixes — if ruff already canonicalized something the patcher
expected to do, the patch reports "skipped" rather than failing.

## After install

```bash
git add -A
git commit -m "chore: fix ruff lint after v0.3 M1+M2 patches (I001, UP017, UP037, F401)"
make ci   # should now pass: format-check + lint + test + drift + examples
```
