# Units 0–6: the contract, and how it was accepted

- **status:** ACCEPTED, 2026-08-27 (ratified as a contract 2026-08-26)
- **authority:** principal
- **applies to:** Sovereign Agent 1.x, Units 0 through 6
- **audit target:** `9c242828a99f469896de940878ae3bf735257800` — the commit the
  read-only audit examined, with findings outstanding
- **accepted target:** `33e51d1972d9d10150765a9504fe668519bf7b23`

Both are named because they are different commits. `9c242828` is where the
audit found three `CHANGES_REQUESTED`; naming it alone as "the acceptance
target" would make a failing commit read as accepted.

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
records for users pinning `<1`; **documentation that describes the software that
exists**; and a **validated textbook source** in `book/`.

Publication is explicitly NOT a Units 0-6 dependency. This repository builds no
site: the textbook is rendered and published by `zeroemployeeorg/zeo-site`, per
[the publication ruling](rulings/2026-08-27-book-publication-destination.md), and
`book/CONTENT-SOURCE.md` states the contract that consumer inherits. An
earlier version of this contract said "a published site is part of the reset",
which was written while this repository still carried a MkDocs pipeline aimed at
a second site nobody wanted. Amended rather than quietly dropped, because a
contract edited to match whatever was built is not a contract.

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
| 0 | `CHANGES_REQUESTED` → remediated | the MkDocs navigation was configured to publish a legacy curriculum whose directory and drift-tool do not exist (Pages was never enabled, so nothing was ever actually served -- the defect was the configured surface and the repository's own legacy documentation, not a live page); quickstart specified Python 3.13 and three nonexistent commands; `CONTRIBUTING` advertised six `make` targets and a `--skip-llm` flag that do not exist; 26 of 28 documented imports did not resolve. `book/` being unpublished was **not** a defect — publication belongs to the consuming site — and the MkDocs pipeline was removed rather than repaired |
| 1 | `ACCEPTED` | 12/12 subcommands respond; fresh 3.14 wheel installs and runs; runtime requires exactly `pydantic<3,>=2`; budgets 23/40 modules, 3631/6000 lines, 7/30 exports |
| 2 | `ACCEPTED` | migrations forward-only and byte-frozen; append-only enforced from an outside connection; transactional store state with rollback proven by fault injection |
| 3 | `ACCEPTED` | per-SOW proof chains; causal binding through the effect edge; separation derived from the ledger; falsification suite refuses every known lie |
| 4 | `ACCEPTED_WITH_EXPLICIT_DEFERRALS` | identity, authority, leases and concurrency verified; fencing deferred to Unit 8; `F-U4-1` recorded as a named limit |
| 5 | `CHANGES_REQUESTED` → remediated | catchable interruption left an assignment recorded `RUNNING` with no receipt; Scripted provider's own failure branches untested |
| 6 | `CHANGES_REQUESTED` (curriculum execution) | adapters, probing and fixtures verified; Chapter 3's exercise was required but never executed; credentialed smokes deferred to Unit 12 |

## Final acceptance at `33e51d19`

- **status:** ACCEPTED
- **recorded:** 2026-08-27
- **target:** `33e51d1972d9d10150765a9504fe668519bf7b23` (merged `main`, PR #26)

The three `CHANGES_REQUESTED` verdicts above were remediated and re-reviewed.
This section records what closed them; the table above is left unedited as the
audit's finding of record at `9c242828`.

| Unit | Was | Now | What closed it |
| --- | --- | --- | --- |
| 0 | `CHANGES_REQUESTED` | `ACCEPTED` | the **current** surface — README, quickstart, `CONTRIBUTING`, `book/` — corrected against the software that exists, and the MkDocs navigation removed, which took the legacy import-heavy tutorials off the rendered surface. **The 0.x documentation corpus was not rewritten:** three files under `docs/` still import symbols 1.x removed, and one of them carries no warning at all. They are off the navigation surface, not fixed. See the limit below |
| 5 | `CHANGES_REQUESTED` | `ACCEPTED` | catchable interruption now writes a durable `interrupted` receipt before re-raising; the Scripted provider's failure branches are driven by real subprocesses rather than pre-classified fixtures |
| 6 | `CHANGES_REQUESTED` | `ACCEPTED_WITH_EXPLICIT_DEFERRALS` | the curriculum gate now **executes** every required exercise -- the tags show it: 3 executed at `9c242828`, 4 at `f7d84f92`. Credentialed smokes remain deferred to Unit 12 |

Units 1, 2 and 3 are unchanged at `ACCEPTED`; Unit 4 unchanged at
`ACCEPTED_WITH_EXPLICIT_DEFERRALS`.

**Units 0-6 are ACCEPTED.** Unit 7 is authorized.

### What acceptance does not claim

Credentialed Claude Code, Codex and Cursor smokes have **never been run**. No
live-provider evidence exists anywhere in this repository, and default CI needs
no credential and no commercial CLI. Multi-process fencing is deferred to Unit
8. Both are recorded below as deferrals rather than absences.

The curriculum gate executes each chapter's `solution.py`. It does **not**
execute commands shown in prose -- stated exactly in `book/CONTENT-SOURCE.md`,
including the reproduction that proves it.

### The Unit 0 limit, stated exactly

Three files under `docs/` retain 0.x-era documentation importing symbols 1.x
removed:

| File | Removed symbols it imports | Warning |
| --- | --- | --- |
| `docs/api_reference.md` | the legacy v0.7 surface, including `Config`, `Half`, `Orchestrator`, `Registry` | identifies itself as the v0.7.0 contract in prose |
| `docs/tutorials/first-agent.md` | `Config`, `run_task` | explicit banner: *Legacy — describes software removed in 1.0* |
| `docs/tutorials/structured-and-approval.md` | `Rule`, `StructuredHalf` | **none** |

Unit 0's requirement was documentation describing the software that exists.
That is met for everything a reader reaches: README, quickstart, `book/` and the
contributor path all resolve. The legacy corpus was taken **off the navigation
surface** rather than rewritten, which is a narrower remediation than "documented
imports corrected" — the claim an earlier draft of this section made, and which
was false.

Reproduce:

```bash
rg -l '^from sovereign_agent import ' docs --glob '*.md'
```

An earlier version of this section ran a Python parser here and reported **four**
files. `docs/persistence-boundary.md` was a false positive: it contains a shell
one-liner, `python -c "from sovereign_agent.organization import Organization; \`,
and the parser captured `Organization; \` as an imported name, then checked that
against top-level `sovereign_agent` and concluded a valid submodule import had
been removed. `Organization` exists.

An earlier version of this table also said `api_reference.md` imports **25**
removed symbols. That number came from the same broken parser: it matched only
the first line of each import, so eleven multi-line parenthesised blocks were
read as one symbol apiece. Those blocks alone contain seventy.

The correction is deliberately **not** a better number. Two reviewers recounted
independently and got 83 and 90; one of them reached 19 and 95 on earlier
attempts before reading the raw blocks. When careful people disagree by seven on
a hand-parse, the integer is not the verifiable part — that every top-level
symbol the file imports was removed is, and the `rg` reproduction proves the
file set without claiming to enumerate symbols.

That is worth leaving on the record rather than quietly deleting. The section
documenting instrument failures contained one: a parser whose own output showed
a name with a trailing backslash — visible evidence it had mis-parsed — which
this seat read past because the count it produced looked plausible. The
replacement matches only top-level imports at line start, which is what the
claim is about.

### Checkpoint tags

Annotated, in `main`'s ancestry, each gating green at its own target:

| Tag | Commit | Why there |
| --- | --- | --- |
| `book-v1-ch00` | `9c242828` | Chapter 0's exercise executes |
| `book-v1-ch01` | `9c242828` | Chapter 1's exercise executes |
| `book-v1-ch02` | `9c242828` | Chapter 2's exercise executes |
| `book-v1-ch03` | `f7d84f92` | Chapter 3's exercise was *required but never executed* at `9c242828`; `f7d84f92` is where it first runs |

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
