# Threat model

The current operational security policy is [SECURITY.md](../SECURITY.md). This
page expands the model behind those boundaries for readers of the source.

## Assets

- the canonical SQLite ledger and derived governance projections;
- provider credentials and the sanitized subprocess environment;
- actor authority, leases, fencing tokens, receipts, evidence, and reviews;
- assignment workspaces and declared deliverables;
- proof-pack artifacts and release metadata.

## Untrusted inputs

Provider output, prompts, deliverable paths, workspace contents, environment
variables, stale processes, CLI arguments, proof-pack manifests, and direct
filesystem changes are untrusted. A model's confidence or a subprocess exit code
is never authorization or proof of success.

## Enforced controls

- Strict models reject unknown boundary fields.
- Role policy and state transitions are enforced by deterministic host code.
- SQLite transactions, foreign keys, uniqueness constraints, and append-only
  triggers guard canonical state.
- Actor leases and execution-attempt tokens fence stale processes at terminal
  writes.
- Provider credential forwarding uses explicit per-provider allowlists.
- Safe path resolution and boundary snapshots refuse or detect stated workspace
  escape classes.
- Verification re-runs checks, binds evidence to executions and observations,
  requires independent review, and checks freshness before acceptance.
- Proof-pack validation checks schema, status vocabularies, cross-field honesty,
  paths, commit identifiers, and artifact digests.

## Residual risk

- A compromised same-user process, provider executable, Python runtime, kernel,
  or host administrator can bypass application-level controls.
- Filesystem snapshots are scoped detective controls, not full host sandboxing.
- A timeout or stale heartbeat is suspicion, not proof that a process is dead.
- Local SQLite is not Byzantine consensus or multi-host high availability.
- A self-authored artifact plus matching digest is internally consistent but not
  independently authenticated.
- Provider-specific sandboxes and network controls are not equivalent across
  adapters.

## Explicit non-goals

The package is not a secrets manager, distributed scheduler, web control plane,
general workflow engine, container orchestrator, or guarantee of autonomous
operation without human governance. See [non-goals.md](non-goals.md).
