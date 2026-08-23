# Migration from v0.6 to v0.7

v0.6 remains the capability-native single-node default. v0.7 adds a bounded
execution fleet. The 161 v0.6 symbols remain. New exports: `FleetCoordinator`,
`PodmanWorker`, `SshWorker`, `SecretBroker`.

`DockerWorker` now implements digest-pinned, fail-closed container execution.
Without an engine or digest it still refuses at prepare — it does not silently
become `SubprocessWorker`.

`NetworkPolicy.DISABLED` is additive. Receipts may carry optional `fleet`
evidence; schema 1.0 receipts still load. Config `worker_backend` accepts
`podman` and `ssh` in addition to `bare`, `subprocess`, and `docker`.
