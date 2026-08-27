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

A workspace root that is itself a symlink is refused, not reclaimed: reclaim
never recurses through it, because the organization allocates a real
directory at that path and a symlink there would delete whatever the link
points at instead — territory this function has no authority over. A symlink
*entry inside* an otherwise real workspace is unlinked directly
(`Path.unlink()`, which removes the link and never follows it into its
target) rather than passed to `shutil.rmtree`, which refuses to recurse into
a symlinked directory and raises `OSError` instead — unguarded, that
exception used to have no protection at its only call site and could
propagate after the assignment's terminal state was already durably written,
which is the review round below reports fixing.

**Corrected by review round two** (P1 finding 1): the two `snapshot_boundary`
calls that bracket the provider invocation (Property 3) used to sit partly
outside the receipt-producing exception handling. A fault taking the
*before* snapshot used to propagate straight out of `run_assignment`,
skipping the persistence block entirely and leaving the assignment stuck at
`RUNNING` (already committed a few lines earlier) with no receipt at all. A
fault taking the *after* snapshot used to be completely unguarded and could
replace an already-caught interruption's own exception at the method's final
`raise failure` — the caller would see an unrelated `OSError` from
bookkeeping instead of the `KeyboardInterrupt` that actually happened, even
though the interruption's own receipt had already been correctly written.
Fixed: the before-snapshot is now taken inside the same try block as the
provider invocation, covered by the same three exception handlers every
other fault in this method already used; the after-snapshot is wrapped in
its own guard that never overwrites an already-determined `failure` — the
more important, already-happened fact always wins, and a snapshot fault that
occurs with no prior failure becomes the reported failure itself rather than
being silently absorbed.

**Corrected by review round three** (finding A): review round two's own
after-snapshot guard (`if failure is None: failure = snapshot_error`) was
written to stop a snapshot fault from *overwriting* an already-caught, more
important failure. It said nothing about what to persist when there was no
prior failure to protect in the first place — the provider ran and
succeeded normally, and only the *after*-snapshot faulted afterward. In
that shape, the persistence block a few lines down still read `report` (the
provider's own genuine `completed` result) and committed `COMPLETED` to the
ledger, while `failure` being newly non-`None` meant `run_assignment` still
raised the `OSError` to the caller at the method's final `raise failure` —
the caller saw a raised exception while the ledger recorded success, two
facts that must never disagree. Fixed: when the after-snapshot faults and
there was no earlier failure, the snapshot fault itself becomes the
terminal failure — `FAILED` is persisted, not `COMPLETED`, with a fresh
failed receipt (`internal_error`) overwriting the stale successful one
already written to `receipt.json`, so the receipt on disk agrees with the
ledger's own verdict. The provider's own successful result is not silently
discarded either: the failure message names that the provider itself
succeeded (or whatever its report said) before the boundary check could not
be confirmed.

A workspace root being a symlink is now also refused *before* the workspace
is ever created or the provider invoked, not only inside `reclaim_workspace`
at the very end. **Corrected by review round three** (finding B): the
review-round-two symlink guard inside `reclaim_workspace` only fires during
reclaim, by which point a pre-planted symlink at the workspace path had
already let the provider read and write through it for real — into
whatever external directory the link pointed at — with `COMPLETED` already
committed to the ledger before reclaim's own refusal ever fired. Fixed by
checking the workspace path for a symlink at the very first opportunity,
immediately alongside the `workspace_policy` validation and before the SOW
or assignment state is touched, before the directory is created, and before
the provider is ever invoked — proven with the same
invocation-counter-stays-zero pattern the policy check already established,
plus a byte-for-byte hash of the external target's whole tree, before and
after, not merely a check for new top-level names. On this path,
`reclaim_workspace`'s own symlink guard never gets exercised at all — the
early refusal is the only one the caller sees — but that guard stays in
place unchanged as defense in depth for whatever other path might reach
`reclaim_workspace` directly.

The check also walks every ancestor directory from the workspace path up to
(but not including) `self.root`, not only the workspace leaf itself: a
leaf-only check is blind to `.sovereign/runs/` (or `.sovereign/`) itself
being a symlink, since the leaf workspace directory underneath a symlinked
ancestor is, on its own, a perfectly ordinary, non-symlink directory —
`workspace.is_symlink()` alone would traverse straight through such an
ancestor transparently. `self.root` itself is excluded from the walk
because it is the organization's own allocated real directory, not
something this method traverses into on the provider's behalf.

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

**Corrected by review round two** (P1 finding 2): that validation used to
happen only inside `reclaim_workspace`, called at the very end of
`run_assignment` — by which point the provider had already run for real and
`COMPLETED` was already committed to the ledger, so an invalid policy meant
"the run happened, then the bookkeeping afterward refused," not "the run
never happened." `run_assignment` now validates `worker.workspace_policy`
against the same `WORKSPACE_POLICIES` set as its very first act, before the
SOW or assignment state is touched, before the workspace directory is
created, and before the provider is invoked — an invalid policy means the
provider never runs at all. Proven with a spy/counter on `invoke_actor` that
must stay at zero, not merely by asserting the final ledger state.

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

**Corrected by review round two** (P1 finding 4): `violated: False` on its
own reads as "execution stayed inside the workspace," but the check is
structurally blind to two things by design — the workspace itself (the actor
is authorized to write there) and `.sovereign/organization.db*` (written by
this same process's own transaction, not by the subprocess under test). A
real schema change or row write to the ledger between two snapshots is
genuinely invisible to `diff_boundary`, and the review correctly named this
a coverage-*honesty* problem, not a "must detect DB writes" problem — the
check was never meant to watch the ledger, per the paragraph above. Fixed by
making the report say what it covers rather than widening what it watches:
`BoundaryReport` (and the `assignment.workspace_boundary_checked` event) now
carries `scope: "organization_root_excluding_workspace_and_ledger"`
(`workspace.BOUNDARY_SCOPE`), naming the same exclusion this section already
documented, as a value a reader can check rather than only a docstring they
must already be looking at. The event also carries `computed: bool`,
distinguishing "the check ran and found nothing" from "the check itself
could not run" (see Property 1's fault-injection correction above) — the two
must never share one boolean.

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

**Corrected by review round two** (P2): `safe_join` used to accept an
absolute input whenever it happened to *resolve* inside root, checking only
the resolved candidate and never whether the input itself was absolute —
looser than the function's own docstring (workspace-relative paths) and than
the "absolute path refused" test category already asserted for the
non-resolving case. `_require_deliverables`'s only real caller passes
workspace-relative deliverable names, so an absolute input is never a
legitimate case here regardless of where it resolves. Fixed to reject any
absolute `relative` argument outright, matching the apparent contract rather
than loosening the docstring to fit the looser behaviour.

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

# Property 1 — reclaim tied to terminal state, including the interrupted path;
# a snapshot fault at either bracket still reaches a terminal state and never
# masks a real interruption (review round two, P1 finding 1); a snapshot
# fault with NO prior failure becomes the terminal failure itself instead of
# a false COMPLETED (review round three, finding A); reclaim refuses a
# symlinked workspace root and unlinks (never rmtrees) a symlinked child
# entry without touching its external target (review round two, P1 finding 3)
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "reclaimed_after_terminal_state or survives_non_terminal_state or interrupted_assignment or hard_kill or fault_in_before_snapshot or fault_in_after_snapshot or reclaim_refuses_a_symlinked or reclaim_unlinks_a_symlinked"

# Property 2 — workspace_policy drives real branching, loads from TOML, fails
# closed on an unrecognized value, and validates before the provider ever
# runs, proven by a spy/counter at zero (review round two, P1 finding 2); a
# symlinked workspace root -- leaf or ancestor -- is refused before the
# provider ever runs too, same spy/counter plus a byte-for-byte external-tree
# hash (review round three, finding B)
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "persistent_policy or temporary_directory_policy or unknown_workspace_policy or policy_loads_from_toml or symlinked_workspace_root_refused_before or symlinked_runs_directory_ancestor"

# Property 3 — boundary violation detected end to end, mutation-checked both
# directions (a real escape is caught; legitimate in-workspace writes are
# not); the report carries an honest scope and a real DB write stays outside
# it on purpose, not silently overclaimed as violated=False (review round
# two, P1 finding 4)
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "detects_write_outside or do_not_trip_the_boundary or new_file_outside or clean_boundary_event or caught_by_run_assignment or does_not_see_a_real_database_write"

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
| After (this unit, original) | 24/40 | 3916/6000 | 7/30 |
| After (review round two's four P1 fixes + P2) | 24/40 | 4056/6000 | 7/30 |
| After (review round three's two findings) | 24/40 | 4134/6000 | 7/30 |

One new module (`src/sovereign_agent/workspace.py`), no new root export —
`Organization.run_assignment` and `_require_deliverables` call the new module
internally; nothing in `workspace.py` is re-exported from the package root.
Review round two's fixes stayed inside the same two modules (`workspace.py`,
`organization.py`) plus their tests — no new module, no new root export.
Review round three's fixes stayed inside `organization.py` and its test file
only — `workspace.py`'s own `reclaim_workspace` symlink guard is untouched,
kept in place as defense in depth — no new module, no new root export.
Headroom remaining: 16 modules, 1866 nonblank lines, 23 root exports.

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
