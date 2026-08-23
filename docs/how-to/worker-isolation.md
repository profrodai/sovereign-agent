# Choose a worker backend

Set `SOVEREIGN_AGENT_WORKER_BACKEND` to `bare`, `subprocess`, `docker`,
`podman`, or `ssh`.

- **bare** — in-process and intentionally unisolated.
- **subprocess** — OS isolation with Landlock on supported Linux or
  `sandbox-exec` on supported macOS hosts.
- **docker / podman** — engine-backed, digest-pinned containers.
- **ssh** — remote execution with pinned host identity.

The runtime fails closed when requested controls cannot be enforced. A Docker
or Podman image must be pinned by `sha256:` digest; an SSH host must use a
pinned known-hosts file. Execution containers never receive the engine socket.

Start with the offline host probe:

```bash
python -m examples.isolated_worker.run
```

For production setup and reconciliation, follow the
[v0.7 operator guide](../v0.7-operator.md) and the backend-specific unit docs.
