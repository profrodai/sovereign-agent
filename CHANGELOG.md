# Changelog

Notable changes to Sovereign Agent, newest first. Entries describe the version
where a change became available; they are not claims about every older release.
This log follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Status — November 20, 2026

Sovereign Agent is a Python library and command-line application for learning
and running an always-on agent: a model/tool loop, durable state, bounded
permissions, recovery, and a simulated shop that can be inspected end to end.

- **Activity:** active. The latest merged repository change was November 12,
  2026; the latest merged runtime feature work was October 26, 2026.
- **Current release:** 1.4.0, published September 5, 2026. Changes under
  Unreleased are on the development line and are not included in that release.
- **Works today:** deterministic offline shop demonstrations, a SQLite-backed
  ledger, explicit approval and verification, recovery, and persistent research
  investigations on the development line. Development supports Python 3.12+;
  the published 1.4.0 package requires Python 3.14.
- **Boundaries:** live providers need their own installation and configuration;
  offline tests do not certify every live provider or a production deployment.
  The 1.x API is incompatible with the old 0.x framework, and there is no
  automatic conversion of old session directories.
- **Check it yourself:** run `make install`, then `make verify` from a development
  checkout. The gate checks formatting, lint, types, tests, dependencies, source
  budgets, offline commands, and clean-environment onboarding.

The book and companion exercises once stored here now have separate public
homes. Historical entries below describe what shipped at the time. A source tag
is not, by itself, proof that its artifacts were published to a package registry.

## [Unreleased]

### Added

- Persistent research investigations with revision history, queued experiments,
  decisions, reminders, and bounded campaigns, so work can continue across
  sessions and be redirected without discarding its evidence.
- A complete teaching agent with a bounded model/tool loop, structured tool
  results, durable work queues, and ledger-backed operating reports.
- A Telegram interface with durable intake and delivery receipts, stock watches,
  and scheduled work that remains traceable after restart.
- Versioned local skills, controlled activation, evidence-backed evaluation,
  improvement, and rollback, so proposed changes can be checked before use.
- Bounded MCP discovery and tool use, an optional isolated tool, and an explicit
  one-host service and maintenance path for the teaching agent.
- Delegation with shared spending allowances and reconciliation of uncertain
  supplier outcomes, including account-recovery checks.
- Expanded classroom notebooks, worked exercises, instructor material, and
  measured lessons on model behavior, retrieval, evaluation, cost, and recovery.

### Changed

- **Breaking:** reference-shop money fields now use USD integer cents rather than
  the earlier currency-specific names. For example, `total_pence` became
  `total_cents`. These are newly defined example prices, not an exchange-rate
  conversion. Existing databases receive a forward migration.
- **Breaking:** cancellation names use `CANCELED` and `canceled`. The migration
  updates persisted state, and legacy outcome records remain readable.
- Lowered the development Python requirement from 3.14 to 3.12, allowing the
  current code to run in more notebook and classroom environments.
- Moved the book, exercises, solutions, and chapter checkpoints out of the runtime
  repository, so the package and its teaching material have clear separate homes.
- Standardized the current examples and documentation on American English and
  clarified what each evaluation result actually demonstrates.
- Kept pull-request automation lightweight while retaining the full development
  verification gate for qualification.

### Fixed

- Retained successive report revisions and independent delivery receipts, so a
  delayed acknowledgement cannot hide a newer result.
- Preserved the original failure when database lock acquisition fails and rolled
  back interrupted transactions reliably.
- Deferred saturated scheduled work instead of repeatedly creating rejected
  reports.
- Revalidated approvals against current policy and superseded obsolete unsent
  proposals without confusing them with already transmitted effects.
- Made uncertain-order renewal and conclusive receipt resolution explicit, so
  missing supplier evidence is not mistaken for a completed purchase.
- Tightened evaluation acceptance, named-check review, and failure reporting, so
  incomplete or failed cases are not reported as successful assessments.
- Corrected process cleanup on macOS after a child exits, while continuing to
  report genuine cleanup failures.
- Repaired the development test worker's inherited environment so asynchronous
  research checks do not accidentally depend on unrelated caller settings.
- Updated retained documentation links after removing outdated development-only
  records from the source tree.

### Security

- Hardened provider and experiment subprocess boundaries and limited inherited
  environment data, reducing unintended access to application state.
- Strengthened isolated-tool deadlines, privilege separation, and response
  validation across tool and MCP boundaries.
- Restricted local skill file reads and rejected stale or unsupported activation
  and schema inputs before they could affect later work.

### Removed

- Removed the in-repository book and archived teaching distribution after moving
  their maintained replacements to the separate book and course.
- Removed obsolete development records from the runtime source tree without
  rewriting its Git history or changing the installed package.

## [1.4.0] — 2026-09-05

### Fixed

- Made durable file replacement safe with concurrent writers and cleaned up
  temporary files on success and failure.
- Made sales respect reserved stock and reject non-positive quantities before
  changing the ledger; low-stock checks now use the remaining available stock.
- Aligned the book's file-safety and inventory examples with the runtime's actual
  guarantees, so readers can reproduce the claims rather than infer them.

## [1.3.0] — 2026-09-05

### Added

- Six inspectable mechanisms: isolation policy, persistent condition scheduling,
  recoverable transcript compaction, session incarnations, bounded tool discovery,
  and access-controlled hybrid memory retrieval.
- An offline `mechanisms` demonstration and adversarial regression tests that
  exercise those mechanisms against the package and its real ledger.
- Executable diagrams, worked extensions, and break-and-repair exercises across
  the book, with source and test references tying the lessons to implementation.
- A hostile-PATH onboarding check that runs documented commands from a fresh
  archive, detecting accidental use of unrelated global executables.

### Fixed

- Reported clean-environment creation failures as explicit release-verification
  failures instead of leaving an unexplained partial run.

## [1.2.0] — 2026-09-02

### Added

- Append-only heartbeat records and a command for checking their freshness,
  separate from the mechanism that creates work.
- Clearer conceptual diagrams and per-chapter verification requirements, helping
  learners distinguish a running process from a completed business outcome.
- Public package metadata, contributor and security guidance, typed-package
  signaling, and current architecture and API documentation.

### Changed

- Modernized the automated checkout and verification workflow dependencies.

## [1.1.1] — 2026-09-01

### Added

- Thirteen executable chapters and companion labs with incomplete starters,
  reference solutions, adversarial exercises, and expected observations.
- Separate checks for executable snippets, teaching depth, and lab behavior,
  with shared source references so those checks agree about what is covered.

### Changed

- Made uv the documented installation and execution path for current examples.
  Runtime behavior is otherwise unchanged from 1.1.0.

### Fixed

- Prevented incomplete snippet runs and mismatched teaching coverage from looking
  like a passing book verification.
- Synchronized the locked package metadata with the release version.

## [1.1.0] — 2026-09-01

### Added

- An OpenAI-compatible HTTP provider, exposed as `ollama`, for local or compatible
  model servers while preserving the same validated actor-report contract.

### Fixed

- Connected documented model configuration to the provider implementation.
- Recorded unreachable or malformed model responses as failed reports rather
  than manufacturing a successful result.

## [1.0.0] — 2026-08-31

### Added

- A small educational control plane with outcomes, actors, assignments, approvals,
  evidence, independent verification, and explicit acceptance in a SQLite ledger.
- A simulated store with multi-product stock, cash accounting, repeat-safe
  replenishment, and a verifiable business result.
- Governed Claude, Codex, and Cursor adapters with capability probes, structured
  reports, durable failures, and explicit credential-environment allowlists.
- Workspace policies, boundary snapshots, reclamation, actor leases, execution
  fencing, and a foreground supervisor that records hard-killed worker failures.
- Proactive work creation from durable signals, with atomic wake decisions and
  traceable origins, separate from supervision and heartbeat reporting.
- Executable introductory chapters, instructor notes, learner evaluation, redacted
  proof manifests, and isolated installed-wheel verification.
- An atomic, repeat-safe marker for a local pilot demonstration, without claiming
  that a real deployment had started or completed.

### Changed

- **Breaking:** replaced the 0.x fleet framework with a deliberately smaller 1.x
  educational API. Existing 0.x users must stay on the older version line or
  migrate explicitly; its broad exported API and session layout are not retained.
- **Breaking:** required Python 3.14 for this release and reduced direct runtime
  dependencies to Pydantic. The older framework's integrations are not implicit
  dependencies of the new teaching package.

### Fixed

- Made acceptance recheck the actual declared outcome and its related evidence,
  rather than treating a status transition as proof that the outcome is true.
- Made replenishment, signal handling, wake creation, and related cash/event
  writes atomic and repeat-safe under failures and concurrent connections.
- Bound worker completion and mailbox acknowledgement to current execution
  authority, preventing stale results from becoming canonical.
- Tightened workspace cleanup and failure reporting and retained failed receipts
  across provider errors and timeouts.
- Kept learner-evaluation and provider results explicitly untested when no valid
  execution evidence exists.

### Security

- Hardened workspace and output-path validation and isolated provider
  environments, so unsupported or escaping execution requests fail closed.
- Protected append-only event history and validated evidence relationships at the
  database boundary, including writes from independent connections.

### Removed

- Removed the previous fleet, generic plugin, and orchestration implementation
  from the 1.x package; the old version tags retain that historical source.

## [book-v1-ch03] — 2026-08-27

### Added

- Tagged the reviewed source checkpoint for chapter 3. This is a teaching
  checkpoint, not a package release or a separate compatibility promise.

## [book-v1-ch02] — 2026-08-27

### Added

- Tagged the introductory governance and acceptance checkpoint, so the lesson can
  be inspected at a fixed source revision. This is not a package release.

## [book-v1-ch01] — 2026-08-27

### Added

- Tagged the introductory durable-state checkpoint alongside the store's verified
  replenishment example. This is not a package release.

## [book-v1-ch00] — 2026-08-27

### Added

- Tagged the introductory store preview at a fixed source revision, so readers
  can return to the same example. This is not a package release.

## [0.7.0] — 2026-08-23

### Added

- Bounded fleet execution with container and authenticated remote workers,
  placement checks, capacity reservations, scoped credentials, and retained
  network-policy evidence.
- Content-addressed artifacts and reconciliation that preserve conflicting
  outcomes instead of choosing whichever result arrived last.

### Changed

- Made the container-worker path executable rather than a placeholder while
  keeping scheduling separate from reusable capability definitions.

## [0.6.0] — 2026-08-23

### Added

- A capability-native single-node runtime with a frozen per-execution action
  catalog and retained approval, invocation, and concurrency-lease evidence.

### Changed

- Made reusable capabilities the default execution surface instead of requiring
  every caller to assemble a custom tool registry.

### Deprecated

- Kept the earlier tool-registration decorator as a compatibility surface rather
  than the preferred way to define reusable actions.

## [0.5.1] — 2026-08-23

### Fixed

- Aligned package metadata, the documented Python requirement, bundled contract
  fixtures, and dependency compatibility checks with the capability migration.
- Declared the existing Apache-2.0 license consistently in package metadata.

## [0.5.0] — 2026-08-23

### Added

- Reusable capability definitions and runtime capability evidence with distinct
  identities, so callers can separate available actions from execution receipts.

### Changed

- **Breaking:** required Python 3.13 and adopted ZeoCore as the reusable capability
  layer. Runtime capability-evidence names now distinguish execution evidence
  from reusable action definitions.

### Fixed

- Corrected Windows file-lock serialization and sandbox-path handling.
- Verified built distribution contents instead of assuming a hardcoded artifact
  filename matched the version being released.

## 2026-08-22 — 0.4.0 (untagged development version)

This version label appeared in the historical changelog, but no corresponding
release tag is present. It is retained as development history, not a claimed
package release.

### Added

- A local execution service with authenticated connections, supervised workers,
  durable approvals, channel integration, and backup/restore support.

## 2026-08-22 — 0.3.0 (untagged development version)

This version label appeared in the historical changelog, but no corresponding
release tag is present. It is retained as development history, not a claimed
package release. The work began in May and was integrated in August.

### Added

- Channel adapters, a generic plugin registry, worker backends, and liveness
  monitoring, developed after the initial release.
- Bounded worker lifecycle and native CLI adapters with evidence-bearing probes,
  normalized events, cancellation, timeouts, and redacted diagnostics.
- Isolated repository execution with retained Git evidence, durable ownership
  leases, and explicit delivery checks.
- A persistent registry, durable message relay, and an execution handshake that
  produces structured requests and receipts across the worker/runtime boundary.

### Changed

- Moved the package to a `src` layout and published API manifests and migration
  guidance, making the supported import surface explicit.

### Removed

- Stopped installing an unused container SDK through the all-features extra while
  retaining its explicit optional dependency declaration.

## [0.2.0] — 2026-04-24

The first tagged package version includes the initial scaffold and the alpha
work recorded on the same day. The old 0.1 and alpha labels are not separate
release tags in the current repository.

### Added

- Sessions with atomic metadata, trace events, a durable queue, concurrency
  limits, retries, and graceful shutdown.
- Typed tools, planning and execution loops, handoffs, tickets, error categories,
  discovery, scheduling, and a command-line interface.
- Parallel-safe tool execution that batches eligible calls while preserving
  result order and serializing operations that must not overlap.
- Subprocess workers and native filesystem-isolation policies, allowing supported
  hosts to run bounded workers without requiring a container daemon.
- Linked session resume, pluggable rule verifiers, and human approval bound to a
  specific proposed tool invocation.
- Offline examples, environment and TOML configuration, user-data directories for
  retained runs, and package publishing support.

### Security

- Refused requested native isolation when the host cannot enforce it, rather than
  silently treating weaker execution as an equivalent sandbox.

## 2026-04-24 — 0.2.0-alpha (untagged development version)

### Added

- Developed the parallel tool calls, isolated workers, session resume, verifier
  protocol, and invocation-specific human approval included in the 0.2.0 tag.
  This label is a historical alpha record, not a separate tagged release.

## 2026-04-24 — 0.1.0 (untagged initial scaffold)

### Added

- Established the initial session, queue, ticket, tool, planning, handoff, and
  command-line scaffold. This was development source, not a tagged release.

[Unreleased]: https://github.com/profrodai/sovereign-agent/compare/v1.4.0...main
[1.4.0]: https://github.com/profrodai/sovereign-agent/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/profrodai/sovereign-agent/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/profrodai/sovereign-agent/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/profrodai/sovereign-agent/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/profrodai/sovereign-agent/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/profrodai/sovereign-agent/compare/v0.7.0...v1.0.0
[book-v1-ch03]: https://github.com/profrodai/sovereign-agent/tree/book-v1-ch03
[book-v1-ch02]: https://github.com/profrodai/sovereign-agent/tree/book-v1-ch02
[book-v1-ch01]: https://github.com/profrodai/sovereign-agent/tree/book-v1-ch01
[book-v1-ch00]: https://github.com/profrodai/sovereign-agent/tree/book-v1-ch00
[0.7.0]: https://github.com/profrodai/sovereign-agent/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/profrodai/sovereign-agent/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/profrodai/sovereign-agent/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/profrodai/sovereign-agent/compare/v0.2.0...v0.5.0
[0.2.0]: https://github.com/profrodai/sovereign-agent/tree/v0.2.0
