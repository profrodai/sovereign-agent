# Architecture

Sovereign Agent 1.x is a local, SQLite-backed teaching implementation of a
governed organization. It separates probabilistic proposals from deterministic
authority, state transitions, and acceptance.

## System shape

```text
world change
  -> durable signal
  -> deterministic wake decision (optional Pulse path)
  -> outcome -> SOW -> assignment
  -> provider proposes an ActorReport
  -> host validates and commits a domain effect
  -> receipt + verification + evidence
  -> independent review
  -> acceptance re-checks the outcome
```

The language model or provider never becomes the authority merely because it is
capable. An `Actor` has a role and a provider binding. Role policy determines
which operation the actor may attempt; the provider produces data; host Python
validates that data and performs the canonical write.

## Canonical state and projections

SQLite at `.sovereign/organization.db` is canonical for operational and
governance state in 1.x. Transactions keep related rows and append-only events
all-or-nothing. Database triggers protect proof-bearing append-only tables.

JSON and Markdown under `governance/` are derived projections for people and
version-control review. They can be regenerated from SQLite. A verifier compares
freshly rendered bytes without repairing drift unless reconciliation is
explicitly requested.

See [Persistence boundary](persistence-boundary.md).

## Work and proof graph

An `Outcome` describes a desired condition in the world. A `StatementOfWork`
describes bounded work toward that outcome. An `Assignment` binds one actor and
workspace to one SOW.

Execution produces a `Receipt`; verification re-runs deterministic checks and
records `Evidence`; review is performed by a distinct actor. Acceptance follows
those ledger edges, checks required effects and deliverables, re-runs the
outcome condition, checks evidence freshness, and refuses self-approval. A
status string alone cannot make an outcome true.

## Runtime mechanisms that must remain distinct

| Mechanism | Responsibility | Explicit non-claim |
| --- | --- | --- |
| Provider invocation | Produce a typed proposal for an assignment. | Does not grant authority or commit canonical state. |
| Pulse | Turn eligible business signals into governed work. | Is not a scheduler or liveness protocol. |
| Supervisor | Reconcile expired claims and abandoned attempts. | Never creates new business work or guesses success. |
| Heartbeat | Append a timestamped liveness observation. | Does not prove progress, health, or death from silence. |
| Automation | Evaluate a durable time or condition trigger. | A non-firing evaluation is not work; this is neither Pulse nor heartbeat. |
| Context compaction | Render a smaller derived view over an immutable transcript. | A generated summary is not canonical source. |
| Session claim | Fence one host incarnation's callbacks. | Actor identity alone does not prove a process is current. |

## Concurrency and recovery

SQLite `BEGIN IMMEDIATE`, uniqueness constraints, and compare-and-set updates
move race arbitration to the database boundary. Actor leases and execution
attempts carry monotonic fencing tokens. A process that resumes after takeover
cannot commit terminal state with an old token.

The supervisor may recover an expired attempt as `worker_lost`. It writes the
failed receipt and terminal ledger state before applying workspace reclamation.
It never infers success from a partial provider artifact.

## Workspace and provider boundary

`safe_join` refuses absolute, empty, traversing, and symlink-resolved escape
paths. Boundary snapshots detect tracked changes within
`organization_root_excluding_workspace_and_ledger`. This is a detective control,
not universal OS containment: the organization database and paths outside the
organization root are outside snapshot scope. Provider-specific sandbox claims
are made only when the adapter proves and requests them.

## Module map

| Module | Responsibility |
| --- | --- |
| `organization.py` | Governed lifecycle, execution, verification, review, acceptance. |
| `models.py` | Strict boundary records and state enums. |
| `database.py` | Schema, migrations, transactions, append-only enforcement. |
| `policy.py` | Role authority and legal state transitions. |
| `execution.py`, `providers/` | Provider protocol and adapters. |
| `fencing.py`, `supervisor.py` | Leases, execution fences, reconciliation. |
| `pulse.py` | Signal-to-work decisions and attribution. |
| `heartbeat.py` | Durable liveness observations. |
| `workspace.py` | Safe paths, boundary snapshots, reclaim policy. |
| `isolation.py` | Independent filesystem, network, credential, tool, and process-probe claims. |
| `automation.py` | Persistent interval and condition state with visible run history. |
| `context.py` | Append-only transcripts and recoverable derived summaries. |
| `coordination.py` | Host leases, session incarnations, and delivery attempts. |
| `tools.py` | Bounded discovery followed by separate authorization. |
| `memory.py` | Access-filtered lexical/semantic ranking with score provenance. |
| `governance.py`, `evidence.py`, `checks.py` | Projections and proof obligations. |

## Deliberate limits

The core has no HTTP service, web dashboard, daemon scheduler, plugin
marketplace, general secrets manager, embedding provider, or model SDK
dependency. The automation module performs one caller-driven due evaluation;
the isolation module provides application policy and reports OS process
isolation as unavailable unless a behavioral probe proves it. The package does
not claim equivalent sandboxing across providers or independent authenticity
from a self-authored proof pack. See [Durable non-goals](non-goals.md) and
[Security](../SECURITY.md).
