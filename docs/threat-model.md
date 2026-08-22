# v0.3 threat model

## Security objective

sovereign-agent is a bounded, single-host execution framework. Its security
boundary is deterministic admission plus serialized repository/session
mutation, with durable evidence sufficient for an external governor to decide
whether an obligation was satisfied. The framework does not grant itself ZEO
governance-mutation authority.

## Assets and trust boundaries

- Repository contents, credentials, session artifacts, provider-session
  identity, seat identity, relay messages, and execution receipts are assets.
- Governed request admission, repository leases, worker launch, provider
  invocation, receipt finalization, and relay acknowledgement are boundaries.
- Provider output, repository state, relay input, old session files, CLI output,
  and environment variables are untrusted input.
- A receipt is evidence, not proof that provider output is true or that an
  external policy was satisfied.

## Enforced controls

- Requests and capability manifests are versioned and validated before
  invocation. Missing evidence fails closed.
- Repository mutation occurs in isolated worktrees under fenced locks. The
  implementation does not use hard reset and does not automatically merge a
  protected trunk.
- Governance-affecting operations serialize at an explicit boundary. There is
  no multi-repository atomicity claim.
- Sovereign session IDs, provider session IDs, and seat-instance IDs remain
  distinct and are persisted explicitly.
- Receipts are immutable after finalization; supersession is represented by a
  new receipt rather than mutation.
- Logs, provider diagnostics, Git evidence, and receipts redact known secret
  fields. Tests and default gates use recorded fixtures, not live credentials.
- Worker isolation probes detect host capability. Supported Unix hosts exercise
  real local sockets and the available filesystem primitive; unsupported hosts
  report the missing capability rather than claiming enforcement.

## Attacker capabilities considered

The model considers malformed or adversarial provider events, stale/corrupted
session and relay files, duplicate/redelivered messages, lock contention,
repository state changing during delivery, symlink/path traversal attempts,
credential strings in diagnostics, and a tool attempting filesystem access
outside its declared worktree.

## Non-goals and residual risk

- Filesystem isolation is not network isolation. A confined process may retain
  network access unless the operator supplies a separate network control.
- This is not a Kubernetes or general scheduler, CI replacement, workflow
  engine, database-backed canonical state, or all-vendor abstraction.
- v0.3 does not provide multi-repository atomic execution, automatic
  protected-trunk merge, or a complete transcript-corpus copy.
- A compromised same-user host, kernel, provider executable, or Python process
  can defeat application-level controls. Redaction is defense in depth, not a
  guarantee against arbitrary secret formats.
- Relay durability is local-host durability, not Byzantine consensus.

The normative scope exclusions are in [v0.3 non-goals](v0.3-non-goals.md).
