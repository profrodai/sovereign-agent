# Units 0–6: the contract, and how it was accepted

- **status:** RATIFIED, 2026-08-26
- **authority:** principal
- **applies to:** Sovereign Agent 1.x, Units 0 through 6
- **acceptance target:** `9c242828a99f469896de940878ae3bf735257800`

## Why this document exists

The 1.x SOW is a design memo. It records the decision, three resolved open
questions, and seven sequencing amendments — and then says:

> The full design memo lives with the originating stream.

That memo is not in this repository. Every earlier line had per-unit requirement
documents in `docs/` (`v0.3-unit1…`, `v0.4-unit1…`, `v0.5-unit1…`,
`v0.7-unit1…`); the 1.x line had none. So an acceptance audit of Units 0–6 had
nothing in-tree to audit against, and any verdict would have graded the code
against its own CHANGELOG — which establishes internal consistency and never
that a unit met a contract someone else set.

**An acceptance record that points at a document not in the tree is the same
defect this project exists to remove, one level up.** This document retires that
external dependency. It is the contract from here on.

## The contract

### Unit 0 — reset and coherent published documentation

Educational reset ruling; `v0.7.0` frozen at its tag; migration and removal
records for users pinning `<1`; and **documentation that describes the software
that exists**. A published site is part of the reset, not separate from it.

### Unit 1 — the skeleton that runs

Python `>=3.14`. Exactly one runtime dependency: Pydantic. An `argparse` CLI
whose every advertised subcommand responds. A wheel that installs clean into a
bare interpreter. `doctor`. Module, line and export budgets enforced by script.

### Unit 2 — memory that does not lie

Strict Pydantic records with `extra="forbid"`. Sortable ids and UTC time.
Forward-only numbered SQLite migrations whose applied bytes are frozen.
Append-only events, enforced by the database rather than by convention.
Transactional store state: inventory, cash, signals.

### Unit 3 — governance that refuses

Outcomes, statements of work, rulings, evidence, verification, review,
acceptance. Separation of duties and no self-approval, derived from the ledger
rather than supplied by the caller. A canonical persistence boundary with
generated projections and drift detection. `ACCEPTED` means the declared outcome
is true now.

### Unit 4 — actors and their mailbox

Actor configuration in committed TOML. Identity separate from role and provider;
rebinding a provider changes neither identity nor authority. Durable addressed
mailbox with claim leases, expiry and reclaim, retry and dead-letter.
**Multi-process fencing is deferred to Unit 8** — see the deferral record.

### Unit 5 — execution that fails closed

`argv`-only subprocess invocation; never a shell string. The Scripted provider
protocol: assignment envelope in, `report.json` out. Timeouts, malformed streams,
malformed and invalid reports, provider failure and **catchable interruption**
must each produce a durable failed receipt and a non-running terminal state.
Nothing is ever a guessed success. A hard kill cannot be caught and belongs to
Unit 8 recovery: a process cannot record its own death.

### Unit 6 — providers behind one boundary

Claude Code, Codex and Cursor as adapters implementing `probe` /
`build_invocation` / `parse_event`. Capability claims come from probing the
installed CLI and fail closed when unprovable. Deterministic offline fixtures and
fake-executable integration tests. Default CI needs no credential and no
commercial CLI. **Credentialed smokes are deferred to Unit 12** — see the
deferral record.

## Cross-cutting

**Curriculum.** Chapters and exercises for implemented behaviour land with their
unit. Every required chapter exercise must *execute*, not merely import. Unit 10
expands, reorganises and polishes Chapters 0–7; it is not where the book first
becomes runnable.

**Checkpoints.** Checkpoint tags name commits and are preserved in `main`'s
ancestry. A tag whose triggering behaviour already works is owed now.

## Acceptance at `9c242828`

Audited read-only. Every finding below was reproduced by descent before it was
recorded; findings that came from an agent or a reviewer were re-run rather than
accepted.

| Unit | Verdict | Grounds |
| --- | --- | --- |
| 0 | `CHANGES_REQUESTED` | site published a legacy curriculum whose directory and drift-tool do not exist, while `book/` was unpublished; quickstart specified Python 3.13 and three nonexistent commands; 26 of 28 documented imports did not resolve |
| 1 | `ACCEPTED` | 12/12 subcommands respond; fresh 3.14 wheel installs and runs; runtime requires exactly `pydantic<3,>=2`; budgets 23/40 modules, 3631/6000 lines, 7/30 exports |
| 2 | `ACCEPTED` | migrations forward-only and byte-frozen; append-only enforced from an outside connection; transactional store state with rollback proven by fault injection |
| 3 | `ACCEPTED` | per-SOW proof chains; causal binding through the effect edge; separation derived from the ledger; falsification suite refuses every known lie |
| 4 | `ACCEPTED_WITH_EXPLICIT_DEFERRALS` | identity, authority, leases and concurrency verified; fencing deferred to Unit 8; `F-U4-1` recorded as a named limit |
| 5 | `CHANGES_REQUESTED` → remediated | catchable interruption left an assignment recorded `RUNNING` with no receipt; Scripted provider's own failure branches untested |
| 6 | `CHANGES_REQUESTED` (curriculum execution) | adapters, probing and fixtures verified; Chapter 3's exercise was required but never executed; credentialed smokes deferred to Unit 12 |

## Deferrals, on the record rather than as absences

- [Unit 4 multi-process fencing → Unit 8](rulings/2026-08-26-deferral-unit4-fencing.md)
- [Unit 6 credentialed provider smokes → Unit 12](rulings/2026-08-26-deferral-unit6-smokes.md)

## How to check this document against the repository

```bash
python -m pytest -q
python scripts/verify_curriculum.py
python scripts/verify_runtime_dependencies.py
python scripts/verify_source_budget.py
sovereign-agent demo store --mode simulated --root /tmp/contract-check
python scripts/verify_store_outcome.py /tmp/contract-check
```

A contract nobody can check against the code is the thing this document replaces.
