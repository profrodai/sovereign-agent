# Unit 7: workspace lifecycle

- **status:** proposed for acceptance (this document is new; it has not yet
  been through the same audit pass that closed `docs/units-0-6-contract.md`)
- **base:** `main = 5120ebf3` (Units 0-6 accepted at `33e51d19`; this ruling
  merged as `5120ebf3`)
- **authority:** ruled by
  [`docs/rulings/2026-08-27-unit7-is-workspaces-not-pulse.md`](rulings/2026-08-27-unit7-is-workspaces-not-pulse.md)
- **applies_to:** Sovereign Agent 1.x, Unit 7
- **requested_by:** `.unit7/SCOPE-PROPOSAL.md`, the read-only investigation
  the governing ruling cites as the source of Unit 7's five properties

This document follows `docs/units-0-6-contract.md`'s own shape: a contract
stated as testable properties, then how to check each one against the
repository. It is **additive** — nothing in the Units 0-6 acceptance table is
touched or revised here.

## Why workspaces, not Pulse

The governing ruling above resolved a transcription error, not a genuine
disagreement: the only in-tree 1.x sentence naming what Unit 7 *is*
(`book/ch03_actor_is_not_a_model/README.md:89`, "Stronger workspace lifecycle
policies arrive in Unit 7") already agreed with the ratified sequencing
amendment (`docs/sows/sovereign-agent-v1-educational-control-plane.md:59`,
"Unit 9 is the first fully proactive milestone"). A corpus-side handover note
transcribed the pipeline under the wrong unit number; both are corrected. Unit
9 owns Pulse. Unit 7 is workspace lifecycle.

## The contract

### Property 1 — reclaim tied to assignment terminal state

`Organization.run_assignment` allocates `.sovereign/runs/<workspace_id>/` and,
before this unit, never reclaimed it on any path. Reclaim now runs
unconditionally at the end of `run_assignment`, after the assignment's
terminal state (`COMPLETED`, `BLOCKED`, or `FAILED`) is durably written —
never before, and never skipped, including the `except BaseException`
(`KeyboardInterrupt`/`SystemExit`) path that already had to record an honest
`interrupted` receipt before re-raising. That interrupted path *is* terminal —
the ledger says the work is over — so its workspace is reclaimed exactly like
every other terminal outcome. A hard kill (`SIGKILL`) that never returns
control to `run_assignment` at all reclaims nothing, on purpose: a process
cannot record its own death, and that is Unit 8 recovery territory, not
silently deleted evidence.

"Reclaim" removes the actor's disposable scratch space — everything the
provider's own subprocess wrote directly into the workspace root
(`provider-raw/`, and anything else a provider leaves beside its mandatory
output) — and never touches `receipt.json`, `receipt.json.sha256`, or the
`.sovereign-out/` output directory. Both are read long after `run_assignment`
returns: by `_require_deliverables` and `accept()` at review time, and by
Chapter 3's own exercise, which reads `receipt.json` straight from the
workspace root. A reclaim policy that deleted them would silently break
re-verification — the exact risk the investigation that grounded this unit
named as an open question rather than guessing past it.

### Property 2 — `Actor.workspace_policy` is enforced

`models.py:120` declared the field (`workspace_policy: str =
"temporary_directory"`) since before this unit; nothing read it. Two changes
close that gap:

1. `actors.py::load_actors` now reads `workspace_policy` from committed TOML
   when present, instead of silently dropping it along with every other field
   the loader did not already know about.
2. `run_assignment` reads `worker.workspace_policy` and passes it to
   `reclaim_workspace`, which branches on exactly two recognized values:
   `"temporary_directory"` (property 1's behaviour) and `"persistent"`
   (reclaim is skipped entirely — the whole run stays inspectable). A value
   outside that set is refused, fail-closed, rather than silently treated as
   either "reclaim" or "keep" — both are real, consequential choices, and an
   unrecognized string must not pick one by accident.

### Property 3 — the workspace boundary is detectable

Only `codex`'s adapter passes real OS-level containment (`--sandbox
workspace-write`); `cursor`'s `--workspace` is documented in this same
repository as "not a sandbox"; `claude` and `scripted` have none. This
property does not invent containment Unit 6's provider boundary doesn't
already give — it makes the absence checkable after the fact instead of
merely asserted in the assignment envelope's own prose ("Do not read or write
outside this disposable workspace").

`workspace.snapshot_boundary` digests every tracked file under the
organization root, excluding the assignment's own workspace (which the actor
is authorized to write) and the live SQLite ledger files (legitimately
written by this same process, not the subprocess under test).
`run_assignment` takes one snapshot immediately before invoking the provider
and one immediately after, on every path — success, refusal, or interruption
— and `workspace.diff_boundary` compares them. The result is recorded as a
durable, queryable event, `assignment.workspace_boundary_checked`, carrying
`violated`, and the changed/added/removed paths. The verdict is **detected,
not prevented**: a clean report is evidence the boundary held for this one
invocation, not a claim that anything was stopped, and a dirty report does
not block the assignment from completing — it puts the fact on the ledger
either way, exactly as the governing ruling specifies ("you can determine
after the fact whether execution stayed inside it").

### Property 4 — `_require_deliverables` gets a traversal check

`organization.py`'s `_require_deliverables` joined an unvalidated
`deliverable` string from `StatementOfWork.deliverables` onto the output path
with `output / deliverable` and no check — an absolute string replaces the
join outright under normal `pathlib` semantics, and a `..`-laden relative
string can walk outside it. `workspace.safe_join` resolves both the root and
the joined candidate and requires the candidate to sit at or under the
resolved root, which defeats a mixed-separator or symlink string a
prefix-string check would miss. `_require_deliverables` now calls it for
every declared deliverable before checking existence.

### Property 5 — parity across all four providers, no live credential

`run_assignment` calls the reclaim and boundary-check logic from one call
site shared by every provider — there is no per-provider branch for either
mechanism, so the same guarantee holds for `scripted`, `claude`, `codex`, and
`cursor` alike. Verified with the same deterministic fake-executable pattern
`test_provider_integration.py` already established for Unit 6: no new
dependency on a live credential, no relaxation of "default CI needs no
credential." Credentialed Claude/Codex/Cursor smokes remain deferred to Unit
12 and were never run in the course of this work.

## Explicit non-scope

- **Pulse, proactive waking, any simulated Pulse event, any wake gate** — Unit
  9. Nothing in this unit creates work, reads a signal, or fires a gate.
- **Multi-process fencing, a supervisor, hard-kill recovery** — Unit 8.
  Property 1's reclaim runs in the same single process already writing
  receipts synchronously in `run_assignment`; nothing here introduces a
  fencing token or an independent sweep process.
- **Credentialed Claude/Codex/Cursor smokes** — Unit 12. Never run, not
  claimed here.

## How to check this document against the repository

```bash
# Baseline, still green after Unit 7 lands
python -m pytest -q
python scripts/verify_source_budget.py
python scripts/verify_curriculum.py

# Property 1 — reclaim tied to terminal state, including the interrupted path
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "reclaimed_after_terminal_state or survives_non_terminal_state or interrupted_assignment or hard_kill"

# Property 2 — workspace_policy drives real branching, loads from TOML,
# fails closed on an unrecognized value
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "persistent_policy or temporary_directory_policy or unknown_workspace_policy or policy_loads_from_toml"

# Property 3 — boundary violation detected end to end, mutation-checked both
# directions (a real escape is caught; legitimate in-workspace writes are not)
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "detects_write_outside or do_not_trip_the_boundary or new_file_outside or clean_boundary_event or caught_by_run_assignment"

# Property 4 — traversal refused fail-closed; a legitimate nested path still
# succeeds
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "traversal or absolute_deliverable or legitimate_nested or empty_deliverable"

# Property 5 — parity across all four providers, no live credential
env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API" || true   # must be empty
python -m pytest -q tests/test_workspace_lifecycle.py -k "identically_across_providers"
```

## Budget impact

Reproduced by `scripts/verify_source_budget.py`, before and after this unit's
change, both figures read from the script's own printed output rather than
estimated:

| | modules | nonblank lines | root exports |
| --- | --- | --- | --- |
| Before (Units 0-6 accepted, `33e51d19`) | 23/40 | 3696/6000 | 7/30 |
| After (this unit) | 24/40 | 3916/6000 | 7/30 |

One new module (`src/sovereign_agent/workspace.py`), no new root export —
`Organization.run_assignment` and `_require_deliverables` call the new module
internally; nothing in `workspace.py` is re-exported from the package root.
Headroom remaining: 16 modules, 2084 nonblank lines, 23 root exports.

## What this unit did not do

Found but out of scope, named rather than fixed inline because fixing it was
not required to make any of the five properties above true:

- `Actor.workspace_policy` is a bare `str` rather than a `StrEnum`, matching
  every other state field in `models.py` (`OutcomeState`, `SowState`,
  `AssignmentState`, `Role`). `workspace.py`'s own `WORKSPACE_POLICIES`
  frozenset and fail-closed refusal give the same behavioural guarantee
  without touching `models.py`'s existing import surface, but a future pass
  could tighten the type at the model layer instead of enforcing it only at
  the point of use.
- `cli.py`'s `_actor_list` prints `id`, `role`, and `provider` for each actor
  but not `workspace_policy`. Not required by any of the five properties, and
  the CLI surface was explicitly not named in the governing ruling's scope.
