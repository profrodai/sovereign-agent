# sovereign-agent documentation

Build auditable AI agents whose state, work, and evidence stay on infrastructure
you control.

Sovereign Agent stores each run as a directory of plain files. It combines
typed ZeoCore capabilities with planning, execution, policy rules, approvals,
and bounded workers. The result is an agent you can inspect, test offline,
resume after a crash, and operate without a hosted control plane.

!!! warning "v0.7 is alpha"
    Pin `sovereign-agent~=0.7.0`, read the
    [non-goals and limitations](non-goals.md), and review code before
    making it load-bearing. Sovereign Agent 1.x is an authorized educational
    reset on branch `v1-educational`; it is not a compatible continuation of
    this API. See [migrate v0.7 to v1](migration-v0.7-to-v1.md) and pin
    `sovereign-agent<1` to stay on 0.x.

## Start here

1. [Install and run the Quickstart](quickstart.md).
2. [Build your first agent](tutorials/first-agent.md).
3. [Inspect and debug its session](tutorials/sessions-and-traces.md).
4. Choose the next path below.

The install check and repository examples work without an API key. Networked
steps are labeled before they can spend tokens.

## Choose your path

### Build agents

- [Quickstart](quickstart.md) — installation to a real typed capability.
- [Tutorials](tutorials/index.md) — a progressive course for Python users.
- [Configuration and providers](how-to/configuration.md).
- [CLI and session management](how-to/cli-sessions.md).
- [Common problems](how-to/troubleshooting.md).

### Learn the internals

- [Core concepts](concepts/index.md) — sessions, tickets, halves, capabilities,
  and dataflow integrity.
- [Architecture](architecture.md) — design rationale and implementation map.
- [Build-from-scratch chapters](chapters/index.md) — five tested exercises
  covering the original substrate.

### Operate and integrate

- [Deployment](deployment.md) — single-host service operation.
- [v0.7 fleet operator guide](v0.7-operator.md) — Docker, Podman, SSH,
  placement, quotas, secrets, and reconciliation.
- [Threat model](threat-model.md) and [compatibility](compatibility.md).

### Look something up

- [API reference](api_reference.md) — task-oriented public API map.
- [Generated reference](reference/index.md) — signatures and docstrings.
- [API stability](API.md) — the semver contract.
- [Example catalog](https://github.com/zeroemployeeorg/sovereign-agent/tree/main/examples).

## The mental model

```text
task
  -> planner
  -> executor
  -> typed capabilities and runtime commands
  -> tickets + trace + artifacts
  -> sessions/sess_<id>/
```

The model proposes actions. Python code defines what exists and what is
allowed. Durable files record what happened.
