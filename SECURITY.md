# Security policy

## Supported versions

Security fixes are made on the current 1.x release line and `main`. Older 0.x
releases are historical and do not receive security fixes. Because Sovereign
Agent is an educational reference implementation, upgrade to the latest patch
before reporting a defect that may already be fixed.

## Report a vulnerability privately

Use
[GitHub private vulnerability reporting](https://github.com/profrodai/sovereign-agent/security/advisories/new).
Do not disclose vulnerabilities in public issues, discussions, pull requests,
or provider transcripts.

Include:

- the affected release and exact commit SHA;
- operating system, Python version, provider, and invocation mode;
- a minimal reproduction and the expected security boundary;
- impact, preconditions, and whether exploitation was attempted;
- sanitized logs or artifacts needed to reproduce.

Never send credentials, personal data, private prompts, or a production
`.sovereign/organization.db`. Please allow maintainers time to confirm the issue
and coordinate a release before public disclosure.

## Current security boundaries

Sovereign Agent is an educational, single-host reference implementation—not a
general-purpose security sandbox.

- Provider output is untrusted data. Providers propose typed reports;
  deterministic host code enforces role authority, validates domain operations,
  and commits canonical state.
- Provider subprocesses receive a documented allowlist of credential variables,
  not the caller's complete environment. This reduces accidental secret
  exposure; it does not protect against a compromised host or provider binary.
- A workspace path is an assignment boundary. Path validation and before/after
  snapshots detect stated classes of escape, but most provider adapters do not
  supply operating-system confinement. Snapshot scope excludes the organization
  database and anything outside the organization root.
- SQLite transactions, append-only triggers, idempotency keys, leases, and
  fencing tokens protect ledger consistency. A process with the same user's
  direct database access can still tamper with local state.
- A heartbeat proves only that a runtime recorded a beat at a timestamp. Silence
  is not proof of death, and a fresh beat is not proof that work progressed.
- Receipts, evidence digests, and proof packs establish the claims their schemas
  name. Internal consistency is not independent authenticity; a party that can
  forge both an artifact and its digest can forge a self-consistent pack.
- Default tests and the executable textbook run without network access or
  credentials. Live-provider execution is opt-in.

Read the implementation-grounded boundaries in
[workspace lifecycle](docs/v1-unit7-workspace-lifecycle.md),
[fencing and recovery](docs/v1-unit8-supervisor-fencing-recovery.md),
[Pulse](docs/v1-unit9-pulse-proactive-work.md), and
[release evaluation](docs/v1-unit12-release-evaluation.md). Historical 0.x
threat-model documents describe the retired framework and are not claims about
the 1.x implementation.
