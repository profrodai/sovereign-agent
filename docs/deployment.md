# Deployment

sovereign-agent can run as a single-host service on a Linux box, Mac Mini, or
laptop. v0.7 also supports bounded Docker, Podman, and identity-pinned SSH
workers coordinated by an operator-owned control host.

This page covers the beginner single-host case. For fleet placement,
reconciliation, quotas, secrets, and remote workers, use the
[v0.7 operator guide](v0.7-operator.md).

!!! warning "Alpha"
    The package version is `0.7.0` and the project is alpha. There is no
    official container image, Helm chart, Kubernetes control plane, or hosted
    service. Deploy it only where you are willing to read the code when it
    misbehaves.

## Single-host layout

```
/var/lib/sovereign-agent/           # or wherever you point sessions_dir
└── sessions/
    ├── sess_<id1>/
    ├── sess_<id2>/
    └── archive/
        └── sess_<old>/             # moved here by the default cleanup task
```

Back up the whole `sessions/` tree. It contains every piece of state: `session.json` files, memory, ticket manifests, trace logs, workspace artifacts. Restore is `cp -r` — no database migration, no schema version to negotiate.

## Running the orchestrator

As a one-shot against a single task:

```bash
sovereign-agent run "Write a report on Q3 revenue and save it to workspace/report.md"
```

As a long-running process that picks up work as it arrives:

```bash
sovereign-agent serve
```

Under a process supervisor (systemd, supervisord, launchd, pm2 — pick your flavor):

```ini
# /etc/systemd/system/sovereign-agent.service
[Unit]
Description=sovereign-agent orchestrator
After=network.target

[Service]
Type=simple
User=sovereign
WorkingDirectory=/var/lib/sovereign-agent
EnvironmentFile=/etc/sovereign-agent/env
ExecStart=/usr/local/bin/sovereign-agent serve
Restart=always
RestartSec=5
KillSignal=SIGTERM
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
```

SIGTERM triggers graceful shutdown — the orchestrator stops accepting new work but detaches active workers rather than killing them. On the next startup, any session whose state isn't terminal is resumed from disk.

## Environment

At minimum:

```bash
SOVEREIGN_AGENT_SESSIONS_DIR=/var/lib/sovereign-agent/sessions
NEBIUS_KEY=<your key>                  # or whichever provider you configured
```

For any non-default:

```bash
SOVEREIGN_AGENT_LLM_BASE_URL=https://api.tokenfactory.nebius.com/v1/
SOVEREIGN_AGENT_LLM_API_KEY_ENV=NEBIUS_KEY
SOVEREIGN_AGENT_LLM_PLANNER_MODEL=Qwen/Qwen3-Next-80B-A3B-Thinking
SOVEREIGN_AGENT_LLM_EXECUTOR_MODEL=Qwen/Qwen3-32B
SOVEREIGN_AGENT_MAX_CONCURRENT=5
SOVEREIGN_AGENT_POLL_INTERVAL_S=1.0
```

## Mount allowlist

`~/.config/sovereign-agent/mount-allowlist.json` controls which host directories workers are allowed to read. Empty allowlist (the default) means no additional mounts — the safest possible start. Add roots only when a specific scenario needs them, and keep `allow_read_write: false` unless the scenario actually writes.

The file lives outside any path the agent can reach, by design. If you edit it, you don't need to restart the orchestrator — the default `allowlist_refresh` scheduled task re-reads it every 5 minutes.

## Observability

The always-on default is `logs/trace.jsonl` per session: one JSON object per line, zero dependencies. Read it with `jq`:

```bash
jq . sessions/sess_*/logs/trace.jsonl | less
```

Generate a markdown report for a session:

```bash
sovereign-agent report <session_id> > report.md
```

For dashboards, install the optional extras:

```bash
pip install sovereign-agent[evidently]      # LLMEval dashboards
pip install sovereign-agent[otel]           # OpenTelemetry export
```

Both backends read from `trace.jsonl` rather than replacing it, so the local file is always the source of truth. Both are also **import-gated stubs** in this release: installing the extra gets you the dependency, not a working dashboard export. `trace.jsonl` is the only observability path that actually works today.

## Worker isolation

`Config.worker_backend` selects how a session step is executed:

- `"bare"` (default) — in-process. No isolation. Fine for single-tenant hosts.
- `"subprocess"` — a separate Python process, confined by Landlock on Linux ≥ 5.13 or `sandbox-exec` on macOS. This is the supported isolated backend. `make_worker_backend()` raises rather than silently degrading if the host offers neither primitive.
- `"docker"` — digest-pinned container worker. Refuses without an engine or image digest. Execution containers never receive the engine socket. The `docker` extra stays optional and is excluded from `[all]`.
- `"podman"` — rootless Podman sharing the Docker contract.
- `"ssh"` — identity-pinned remote worker; disconnect is unknown until reconcile.

If you were planning to isolate workers with containers, use `"subprocess"`.

## Backup / restore

Sessions are directories. Backup is `tar` or `rsync`:

```bash
tar -czf sovereign-agent-$(date +%F).tar.gz /var/lib/sovereign-agent/sessions/
```

Restore is untar into place. No migration. No versioning ceremony.

## Resource sizing

- **CPU:** minimal. The agent spends most of its time waiting on LLM calls.
- **Memory:** `max_concurrent × ~100MB` is a generous upper bound for the Python process footprint. Container-based workers do not exist (see below), so there is no per-container overhead to budget for.
- **Disk:** dominated by trace logs and memory files. For a busy system, budget a few GB per week per session and archive completed sessions weekly (the default scheduled task does this).
- **Network:** whatever your LLM provider's pricing scheme charges for.

## What not to do

- Do not point `sessions_dir` at a shared filesystem. Atomic rename guarantees are weaker across NFS/SMB and the framework doesn't try to work around it.
- Do not run two orchestrators against the same `sessions_dir`. There is no lease/coordination layer between instances — they will both try to work on the same sessions and results are undefined. If you need that, you need a multi-machine deployment, which is out of scope for v1.0.
- Do not try to edit `session.json` by hand. Use `sovereign-agent sessions show` to inspect, and let the framework write.
