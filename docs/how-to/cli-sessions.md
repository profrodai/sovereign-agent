# Use the CLI and manage sessions

## Run one task

```bash
sovereign-agent run "Summarize the supplied evidence"
```

This uses `Config.from_env()`, writes under `./sessions/`, prints the session
ID and directory, and exits nonzero on failure.

## Run a service or chat

```bash
sovereign-agent serve
sovereign-agent chat
```

`serve` runs a long-lived orchestrator with the CLI channel. `chat` connects to
an existing socket or starts an embedded orchestrator.

## Inspect and archive

```bash
sovereign-agent sessions list
sovereign-agent sessions list --state completed
sovereign-agent sessions show <session-id>
sovereign-agent report <session-id> -o report.md
sovereign-agent sessions archive <session-id>
```

## Resume

```bash
sovereign-agent sessions resume <parent-id> \
  --task "Continue using the previous result"
```

The new child gets fresh state and summarized parent context. The parent is not
modified.

## Discover command groups

```bash
sovereign-agent --help
sovereign-agent approvals --help
sovereign-agent governed --help
sovereign-agent fleet --help
```

Fleet and governed execution commands are advanced operator surfaces; start
with the [deployment guide](../deployment.md).
