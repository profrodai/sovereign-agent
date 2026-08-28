# Unit 7: workspace lifecycle

- **status:** ACCEPTED, 2026-08-28 (ratified as a contract 2026-08-28)
- **authority:** principal
- **base:** `main = 5120ebf3` (Units 0-6 accepted at `33e51d19`; this ruling
  merged as `5120ebf3`)
- **audit target:** `26235956a0887753d8b10c04b0d4201a53b8cd04` — PR #29's
  merge commit into `main`, the commit Sparring's acceptance-record audit
  examined
- **accepted target:** `26235956a0887753d8b10c04b0d4201a53b8cd04` — the same
  commit. Unlike `docs/units-0-6-contract.md`, where the audit ran at a
  commit (`9c242828`) with findings outstanding and acceptance landed later
  at a different, remediated commit (`33e51d19`), Unit 7's six review rounds
  and their fixes all happened *before* merge, on the PR branch; the audit
  ran once, after merge, against `main` at its head, and passed there with no
  further remediation needed. One commit is both the audit target and the
  accepted target because there is no gap between them to name two commits
  for.
- **governing ruling:**
  [`docs/rulings/2026-08-27-unit7-is-workspaces-not-pulse.md`](rulings/2026-08-27-unit7-is-workspaces-not-pulse.md)
  (scope: workspace lifecycle, not Pulse; unchanged by this acceptance)
- **applies_to:** Sovereign Agent 1.x, Unit 7
- **requested_by:** `.unit7/SCOPE-PROPOSAL.md`, the read-only investigation
  the governing ruling cites as the source of Unit 7's five properties

This document follows `docs/units-0-6-contract.md`'s own shape: a contract
stated as testable properties, then how to check each one against the
repository. It is **additive** — nothing in the Units 0-6 acceptance table is
touched or revised here.

## Acceptance audit at `26235956`

Audited read-only by Sparring against merged `main`
([GitHub comment id 5447432090 on PR #29](https://github.com/zeroemployeeorg/sovereign-agent/pull/29#issuecomment-5447432090)),
verdict PASS. Every command in "How to check this document against the
repository" was executed directly, exit codes read from the run rather than
assumed, no pipes:

- Full gate: 230 passed / 9 deselected, exit 0. `verify_source_budget.py`
  exit 0. `verify_curriculum.py` exit 0 (4 chapters, 4 exercises executed,
  all links resolve).
- Property-block selections, all exit 0, all counts non-trivial: Property 1
  — 9 passed; Property 2 — 13 passed; Property 3 — 6 passed; Property 4 — 6
  passed; Property 5 — 4 passed.
- Budget table verified in both directions against the script's own output,
  not the prose: the final row (`24/40`, `4307/6000`, `7/30`) matches a live
  run on `main` byte-for-byte; the historical baseline row (`23/40`,
  `3696/6000`, `7/30`) was independently re-verified by running the script in
  a worktree at `33e51d19` itself.
- Credential absence confirmed: the required env grep is empty; the 9
  deselected tests are exactly the Unit 12 credentialed provider smokes
  deferred below — no live-provider evidence is claimed anywhere in this
  record.
- Pulse-clean: every "pulse" occurrence in this unit's code, tests, and this
  record is either a reference to the governing ruling or the explicit
  non-scope declaration below. Nothing creates work, reads a signal, or
  fires a gate.
- Deferrals confirmed named and nowhere claimed as done: Unit 8
  (fencing/supervisor/hard-kill, `F-U4-1` stands), Unit 9 (Pulse), Unit 12
  (credentialed smokes).
- This document's own six-round review narrative (below) was checked
  against the filed review chain on PR #29 and matches: each finding, each
  fix, each round's verdict as filed.

Per standing doctrine, this audit is Sparring's alone; the status flip
above — this record moving from "proposed for acceptance" to `ACCEPTED` — is
authored work, done by Master/stream and co-signed on the PR that carries
it, not by Sparring. The Principal's acceptance of Unit 7 arrived as an
explicit message, not inferred from this audit or any green gate.

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

**Corrected by review round three, second finding** (B3): the ancestor walk
above guards the workspace root and everything above it, but a workspace
root can pass every one of those checks as an ordinary real directory while
`.sovereign-out` — the organization-allocated *output child* living one
level *below* the workspace root — was pre-planted as a symlink. The
reviewer's own framing: probe the dual of every fix, same mechanism,
opposite position; round three's first finding (B) guarded the path above
the workspace, this one is the path below it. Before this fix, the provider
wrote its report and every declared artifact through that symlink for real,
into whatever external directory it pointed at, and `_require_deliverables`
— which reconstructs the same `.sovereign-out` path independently and joins
onto it with `safe_join` — resolved through the same symlink and accepted
evidence sitting entirely outside the workspace boundary as proof the SOW
was satisfied. Fixed by checking `.sovereign-out` for a symlink immediately
after the ancestor walk, in the same place, before the SOW or assignment
state is touched, before the workspace directory is created, and before the
provider is ever invoked — refusing with a distinct category
(`symlinked_output_directory`, not `symlinked_workspace_root`) because it is
a different path component (a child, not a root or an ancestor) that the
ancestor walk cannot see. Proven with the same invocation-counter-stays-zero
and byte-for-byte external-tree-hash pattern the two round-three-B tests
already established.

**Corrected by review round four** (findings C1 and C2, the dual of B3):
the B3 check above refuses `.sovereign-out` *being* a symlink, but says
nothing about `.sovereign-out` pre-planted as an ordinary *real* directory
with a hostile interior — the provider's own `mkdir(parents=True,
exist_ok=True)` (`providers/scripted.py`) never disturbs pre-existing
content, so a real directory sitting there before `run_assignment` runs
survives untouched. Two shapes, both reproduced against the unfixed code
before any edit: **C1**, a symlinked *child* (`.sovereign-out/report.json`
pointing at an external file) — the provider's real report bytes wrote
through the link, overwriting the external file, with `COMPLETED`
committed; and **C2**, a real file already sitting at the exact name a
SOW declares as its deliverable, never written by the provider at all —
`_require_deliverables` accepted it as proof the run produced evidence it
never produced. The same defect class was independently present on the
organization's *other* write path: `execution.py::invoke_actor` allocates
`workspace / "provider-raw"` the same unchecked way, and a pre-planted
symlink there let the post-subprocess bookkeeping (`stdout.txt`,
`stderr.txt`, `events.jsonl`) write straight through it.

Fixed at the root, not by adding a third `is_symlink()` refusal: the
allocation-time comment above claimed "the provider must never run
against an output path this method did not allocate as a real
directory," but the method never allocated it at all — it only ever
checked what was already there. `run_assignment` now actually allocates
`.sovereign-out` fresh: immediately after the existing symlink check (and
after `workspace.mkdir()`, since the output child lives inside the
workspace root), any pre-existing content at that path — real directory,
hostile interior, whatever shape — is removed with `shutil.rmtree` and
replaced with a clean, empty, real `mkdir`. `shutil.rmtree` unlinks a
symlinked child *entry* without following it into its target, so a
hostage file the symlink pointed at is never touched by the removal
itself, only by whatever the (now-absent) link would have let the
provider write afterward. `execution.py::invoke_actor` gets the identical
treatment for `provider-raw`, immediately before its own three writes.
Because the symlink check upstream already refused a top-level symlink at
`.sovereign-out`, the recreate step there only ever needs to handle "real
directory or nothing"; `provider-raw` has no upstream check of its own
(a third, independent path `run_assignment`'s checks never look at), so
its own recreate step handles the symlink case directly too. This closes
C1 and C2 (and their `provider-raw` sibling) regardless of which hostile
shape was planted, rather than adding a growing list of shape-specific
refusals — the next dual of this fix, if one exists, would have to be a
substitution happening *after* the recreate and *before* the provider
runs (a live TOCTOU race), which is out of this unit's scope by the same
reasoning every prior round used: Unit 8 fencing territory, not a
pre-planted-content question this allocation-time fix already answers
regardless of timing before the provider starts.

**Design note on resume, checked rather than assumed**: `run_assignment`
never currently passes `provider_session_id` to `invoke_actor` — the
parameter exists on `invoke_actor` and `InvocationRequest`, but nothing in
`run_assignment`'s own call site wires a resumed session through it (the
call is `invoke_actor(worker, sow, workspace, output,
assignment_id=assignment.id)`, no fifth argument). Recreating
`.sovereign-out` fresh on every call therefore does not break any *live*
resume path today, because there is not one. If a future unit wires
`provider_session_id` through `run_assignment` for a real resume case that
needs prior output content to survive between calls, that unit will need
to make the recreate conditional on whether the call is a fresh
allocation or a genuine resume — this fix does not attempt to anticipate
that shape, since guessing at an unbuilt resume contract risks getting it
wrong in a security-relevant way. Recorded here as a known scope boundary,
not a silent decision.

Proven the same way as every fix in this unit: reproduced against the
unfixed code first (three standalone scripts, not suite tests, matching
this project's own pattern), then covered by three new tests
(`test_symlinked_child_inside_a_real_output_directory_cannot_be_written_through`,
`test_fabricated_deliverable_preplanted_in_a_real_output_directory_is_not_accepted`,
`test_symlinked_provider_raw_cannot_be_written_through`), then falsified
by disabling the recreate in both files, confirming all three tests fail
with the exact same symptom the unfixed reproduction showed (real bytes
landing in the external target; the fabricated file surviving), then
restored and confirmed byte-identical via `diff` before re-confirming
green.

**Corrected by review round five** (finding E1, a comment-correctness
defect, not a behavioural one): round four's own closing comment on the
recreate above claimed a completeness property — "by construction only a
real directory — or nothing at all — can remain here; `output.exists()`
alone is therefore a complete test, not an approximation." That claim was
false at round four's head. The symlink check just above only refuses
`.sovereign-out` *being* a symlink; it says nothing about the path
existing as some *other* non-directory shape — most simply, an ordinary
plain file, left over from an earlier crash or planted by something that
stopped short of a symlink. Reproduced against round four's own head
before any edit: a pre-planted plain file at `.sovereign-out` is not a
symlink (passes the check above) and is not a directory (`exists()` is
`True`), so `shutil.rmtree` reached a `scandir` call on a file and raised
a raw `NotADirectoryError` — a third shape the comment's enumeration
missed. The same shape at `provider-raw` (`execution.py::invoke_actor`)
reproduced too, with a different outcome: because that recreate happens
*inside* `run_assignment`'s own `try`/`except` block (the `.sovereign-out`
recreate happens *before* it), the `NotADirectoryError` there was already
caught by `except Exception`, already produced an honest `FAILED` receipt
with category `internal_error`. Both paths were already fail-closed with
a truthful ledger — nobody was harmed by the bug — but a proven-false
completeness claim, in a codebase whose whole subject is that a claim
must not outrun the check behind it, is exactly the pattern review rounds
two and four already put on record as the shape that precedes a paid
failure, even when (as here) the underlying behaviour is safe.

Fixed by refusing the shape explicitly rather than only correcting the
comment (the reviewer's own preferred resolution, called the better
teaching artifact: a named `Refusal` with a clear message teaches more
than a rewritten sentence does). `run_assignment` now refuses
`.sovereign-out` existing as anything other than a directory — a second,
independent `elif` right after the existing symlink check, with its own
category (`non_directory_output_path`, not folded into
`symlinked_output_directory`: a different shape, most likely a different
cause — leftover state, not necessarily an adversarial link — and a
different fix, "remove the file," so the category should say which one
applies). `execution.py::invoke_actor` gets the identical treatment for
`provider-raw`, for consistency, even though its own un-fixed failure was
already honest: the `Refusal` there is still caught by the same
`except Exception` handler in `run_assignment`, so the assignment still
fails exactly as before — only the receipt's category improves, from the
generic `internal_error` to this shape's own name. The closing comment
above the recreate is corrected to describe what actually makes
`output.exists()` a complete test now: both the symlink check and the new
non-directory check have already turned away every shape but "real
directory" or "absent" by the time that line runs, so the claim is true
for the first time, not merely re-asserted.

Proven the same way as every fix in this unit: reproduced against
round four's head first (two standalone scripts, not suite tests), then
covered by two new tests
(`test_non_directory_output_path_is_refused_before_the_provider_ever_runs`,
`test_non_directory_provider_raw_is_refused_with_a_named_category`), then
falsified by disabling the new `elif` in both files, confirming both
tests fail with the exact `NotADirectoryError` symptom the unfixed
reproduction showed, then restored and confirmed byte-identical before
re-confirming green.

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
# hash (review round three, finding B); a symlinked *output child*
# (.sovereign-out) one level below the workspace root is refused the same
# way (review round three, finding B3); a REAL .sovereign-out with a hostile
# interior -- a symlinked child, or a fabricated deliverable -- cannot be
# written through or accepted, because it is removed and recreated fresh at
# allocation time, and the organization's other write path (provider-raw)
# gets the same treatment (review round four, findings C1 and C2); a
# non-directory shape (a plain file) at either .sovereign-out or
# provider-raw is refused explicitly, by name, instead of surfacing as a
# raw NotADirectoryError from shutil.rmtree (review round five, finding E1)
python -m pytest -q tests/test_workspace_lifecycle.py \
  -k "persistent_policy or temporary_directory_policy or unknown_workspace_policy or policy_loads_from_toml or symlinked_workspace_root_refused_before or symlinked_runs_directory_ancestor or symlinked_output_directory_refused_before or symlinked_child_inside_a_real_output_directory or fabricated_deliverable_preplanted or symlinked_provider_raw or non_directory_output_path or non_directory_provider_raw"

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
| After (review round three's third finding, B3) | 24/40 | 4168/6000 | 7/30 |
| After (review round four's findings, C1/C2) | 24/40 | 4236/6000 | 7/30 |
| After (review round five's finding, E1) | 24/40 | 4307/6000 | 7/30 |

One new module (`src/sovereign_agent/workspace.py`), no new root export —
`Organization.run_assignment` and `_require_deliverables` call the new module
internally; nothing in `workspace.py` is re-exported from the package root.
Review round two's fixes stayed inside the same two modules (`workspace.py`,
`organization.py`) plus their tests — no new module, no new root export.
Review round three's fixes (both finding B and finding B3) stayed inside
`organization.py` and its test file only — `workspace.py`'s own
`reclaim_workspace` symlink guard and `safe_join` are both untouched, kept in
place as defense in depth — no new module, no new root export.
Review round four's fixes touched `organization.py`, `execution.py`
(the `provider-raw` recreate), and their shared test file — no new module,
no new root export; `execution.py` already existed and already owned
`provider-raw`'s allocation, so extending its own `mkdir` call site is not
a new dependency surface.
Headroom remaining: 16 modules, 1764 nonblank lines, 23 root exports.

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
