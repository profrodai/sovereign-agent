# Security policy

## Supported versions

The latest v0.7 patch release receives security fixes. Earlier alpha minors may
receive a migration note but are not supported security branches.

## Report a vulnerability privately

Use GitHub's private vulnerability reporting for
[`zeroemployeeorg/sovereign-agent`](https://github.com/zeroemployeeorg/sovereign-agent/security/advisories/new).
Do not include secrets, personal data, or unredacted production session
directories.

Include:

- affected version and commit;
- operating system, Python version, and worker backend;
- minimal reproduction and expected security boundary;
- impact and whether exploitation was attempted;
- sanitized logs or artifacts needed to reproduce.

Please allow maintainers time to confirm and coordinate a fix before public
disclosure. If private reporting is unavailable, open a public issue containing
only a request for a private security contact, without vulnerability details.

## Important boundaries

Sovereign Agent is alpha and not a general security sandbox.

- `bare` workers are intentionally unisolated.
- OS isolation depends on host support and fails when requested controls cannot
  be enforced.
- Docker and Podman require digest-pinned images and never receive the engine
  socket inside execution containers.
- SSH requires pinned host identity; trust-on-first-use is refused.
- Secret values should be resolved at spawn and must not be persisted in
  requests, tickets, traces, receipts, or artifacts.
- SHA-256 manifests detect changes; they do not establish authorship or protect
  against a host administrator.
- Models and capability outputs are untrusted input. Authorization and business
  policy belong in deterministic code.

Review the full [threat model](docs/threat-model.md) and
[v0.7 operator guide](docs/v0.7-operator.md) before deployment.
