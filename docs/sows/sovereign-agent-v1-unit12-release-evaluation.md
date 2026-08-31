# SOW: Sovereign Agent 1.x — Unit 12 release evaluation, proof pack, Andrea protocol, 1.0.0 release

```yaml
sow: sovereign-agent-v1-unit12-release-evaluation
project: sovereign-agent
unit: 12
status: PROPOSED
authority: principal
base_commit: 266d5c421940d2e0fceedd275c11a0168049dd0d
governing_documents:
  - docs/sows/sovereign-agent-v1-educational-control-plane.md (sequencing amendment 6)
  - docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md
    (withdraws the real-deployment pilot-start premise this unit's own scope was
    originally written against)
  - docs/rulings/2026-08-31-unit12-scope.md (Unit 12 scope ruling, all seven
    holdings binding)
work_branch: unit-12/release-evaluation
runtime: Python 3.14
runtime_dependencies:
  - pydantic
```

## Authorization

This SOW is the Principal's implementation direction for Unit 12, incorporating
the Principal's Unit 12 scope ruling
(`docs/rulings/2026-08-31-unit12-scope.md`) in full.

**Filing and reviewing this SOW does not, by itself, authorize implementation**
— the same boundary every prior unit's own SOW has had to state explicitly.
Merging this SOW establishes the reviewed implementation contract; it does not
start implementation.

The sequence is:

1. File this SOW in the repository, route it through Sparring review, and merge
   the reviewed text into `main`. Merging establishes the contract; it does not
   start implementation.
2. Gate merged `main` from a clean clone, confirming the merge introduced no
   drift from the reviewed head.
3. Master requests explicit Principal authorization, bound to the exact merged
   SOW commit, before opening any implementation branch or spawning any stream
   work.
4. Only on that separate authorization does implementation begin, from the
   resulting exact merged commit — not from the drafting branch and not from
   `266d5c42` if `main` has advanced past this SOW's own merge.

**Three further, independent authorization gates govern this unit's own
terminal acts, each distinct from and later than implementation authorization:**

- **The Andrea live evaluation** (Holding 3 of the governing ruling) requires a
  real human participant. Scheduling and running that session is a separate
  Principal (or Operator, for participant selection) act, not implied by
  implementation acceptance.
- **The `1.0.0rc1` TestPyPI publication and the redacted proof pack's filing**
  (Holding 2 and Holding 5, steps 2-4) follow implementation acceptance but
  require their own review before the release-candidate artifact is treated as
  evidence of anything.
- **The final `v1.0.0` PyPI release** (Holding 5, steps 5-7) requires separate,
  explicit Principal authorization distinct from release-candidate publication.
  **Merging this unit's implementation does not authorize either release tag.**

**Correction (2026-08-31):** the original version of this paragraph described
Unit 12's own closure as following implementation merge with the final
release treated as a possibly-later, independently-orderable act. That
inverted the governing ruling's own Holding 5 sequence, where step 10
("close Unit 12") comes strictly after steps 5-9 (final release
authorization, tagging, PyPI publication, external verification, and
installation-documentation correction) — one ordered sequence, not two
separately-sequenceable branches. "Separately authorized" means the final
release needs its own distinct Principal act (step 5); it does not mean that
act, once granted and executed, may happen after Unit 12's own closure.
Corrected: Unit 12's own closure (Holding 5, step 10) follows the completed,
externally-verified final release and its documentation correction (Holding
5, steps 5-9) — a separate, reviewed `PROPOSED -> ACCEPTED` change and a
clean-`main` gate come only after that, matching every prior unit's own
closing convention. See "Review and merge ritual" and "Final Unit 12 closure
conditions" below for the corrected exact ordering.

A changed SOW head invalidates an earlier co-sign. Branch reconciliation must
use an allowed, auditable PR-based mechanism; do not substitute a local history
rewrite for the denied `git rebase`, `git merge`, or force-push mechanisms.

## Mission

Close the seven components the governing ruling authorized:

1. Build the redacted proof-pack manifest and its verifier (Holding 2).
2. Extend the Andrea evaluation to the full Chapters 0-12 curriculum with three
   new scored tasks and a defined protocol (Holding 3).
3. Extend mechanical curriculum verification to cover the installed-wheel path
   and the new gate surfaces, as a distinct release gate (Holding 4).
4. Wire the conditional, truthful provider-status reporting the proof pack
   requires (Holding 6).
5. Correct the stale unqualified "soak" phrasing Holding 7 names, additively.
6. Correct the top-level design memo's own `done_when` requirement,
   additively, with Holding 1's replacement text (Holding 1).
7. Leave the project ready for the Principal to separately authorize the
   `1.0.0rc1` release-candidate sequence (Holding 5) — this unit builds the
   mechanism and produces the evidence; it does not itself publish anything.

Unit 12 does not finish or simulate a real 30-day pilot, does not perform the
real pilot-start act, does not run the Andrea live evaluation itself (that is a
separate, later, separately-authorized human session using the protocol this
unit defines), does not publish any release tag, and does not claim PyPI
publication occurred. All of that remains outside this unit's own
implementation-acceptance scope, per the governing ruling's own holdings.

**Terminology**, per the governing ruling's Holding 7, binding on this SOW and
its own deliverables: **"Andrea live evaluation"** for the timed human session
this unit's protocol defines (never unqualified "soak"), **"local,
learner-controlled Sovereign Store release evaluation"** for what the proof
pack's own pilot-mechanism evidence documents (never "the 30-day pilot" or any
phrasing implying a real deployment), and **"v0.6 infrastructure soak"** if the
unrelated historical concept needs mentioning at all.

## Required implementation

### 1. The redacted proof-pack manifest and its verifier (governing ruling Holding 2)

Build `docs/evidence/unit12/proof-pack.json` (the manifest itself — filed only
once real evidence exists to populate it; this unit builds the schema and the
verifier, and produces a manifest whose fields are filled from evidence this
unit's own gate actually generates, but Andrea-evaluation and provider-status
fields for statuses this unit cannot itself produce — see below — are recorded
using their honest `NOT_RUN_*` states, never fabricated) and a corresponding
schema/verifier module.

The manifest must record, exactly as the ruling requires:

- exact source and release-candidate commits;
- Python/package versions and artifact digests;
- deterministic gate and curriculum results;
- installed-wheel results outside the source tree;
- local disposable pilot-mechanism evidence;
- the Andrea live-evaluation result;
- one status row for each provider (Claude, Codex, Cursor);
- redactions performed;
- explicit non-claims;
- evidence-file paths and SHA-256 digests.

Provider status is exactly one of `LIVE_PASS`, `NOT_RUN_UNAVAILABLE`,
`NOT_RUN_UNAUTHENTICATED`, `FAIL` — no fifth value, no free-text status field
that could smuggle in an unreviewed claim.

Build a verifier (`scripts/verify_proof_pack.py`) that rejects, with a specific
named reason for each:

- missing required fields;
- an unknown provider status value;
- a digest that does not match the file it claims to describe;
- any evidence path that escapes the evidence directory (`..`, absolute paths
  outside `docs/evidence/unit12/`, symlink traversal — matching this project's
  own established `.sovereign-out`/`.sovereign` path-escape discipline);
- content that matches a secret-shaped pattern. **Correction (2026-08-31):**
  the original version of this bullet cited `verify_runtime_dependencies.py`
  as already containing credential-shaped environment heuristics; independently
  re-checked, that script contains no such thing — it only validates that
  `pydantic` is the project's sole direct runtime dependency by reading
  `pyproject.toml`. No existing script in this repository performs
  secret-shaped-content detection; this SOW specifies the contract directly
  instead of citing a nonexistent precedent. The verifier must reject content
  matching common credential shapes: strings beginning with known provider
  prefixes this project's own provider adapters already check for by name —
  confirmed by direct read of each adapter's own `authentication_environment`
  tuple: `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`
  (`src/sovereign_agent/providers/claude.py:24-27`), `CODEX_API_KEY`
  (`src/sovereign_agent/providers/codex.py:26`), `CURSOR_API_KEY`
  (`src/sovereign_agent/providers/cursor.py:24`) — long high-entropy tokens (a
  conservative heuristic: 20+ contiguous alphanumeric/`-`/`_` characters with
  no whitespace), and any literal environment-variable dump shape (`KEY=value`
  pairs pasted verbatim rather than summarized). This is new detection logic
  this unit builds, not a reuse of anything that already exists;
- any status field, anywhere in the manifest, whose value is `NOT_RUN_*` but
  whose accompanying prose or a sibling field claims success — the exact
  "NOT_RUN means PASS" lie Holding 2 names explicitly.

This unit builds the manifest schema, the verifier, and — where this unit's
own gate genuinely produces the evidence (deterministic gate results,
installed-wheel results, local pilot-mechanism evidence) — a real filled-in
manifest reflecting that evidence truthfully. Fields this unit's own
implementation cannot itself produce (the Andrea live-evaluation result,
because that evaluation is a separate later human session; `LIVE_PASS`
provider rows, because no credential is available in this unit's own
implementation environment) are filled with their honest `NOT_RUN` /
not-yet-available states, never left absent and never fabricated.

### 2. The Andrea live evaluation: protocol, new tasks, and machine-checkable pre-check (governing ruling Holding 3)

Create a new document, `docs/andrea-chapters-0-12-evaluation.md`, following
`docs/andrea-chapters-0-7-evaluation.md`'s own established shape (task
descriptions, expected observations with real captured command output,
scoring key, "what this document does not authorize" section). This document
does not rewrite `docs/andrea-alpha-evaluation.md` or
`docs/andrea-chapters-0-7-evaluation.md` — both remain historical records of
their own prior evaluations, untouched.

The new document must define, exactly per the ruling:

- **Participant**: at least one real Andrea-profile learner, not an author or
  reviewer of this implementation.
- **Environment**: fresh laptop or notebook-style environment, Python 3.14,
  cold checkout/install, no pre-run exercises, no credentialed provider
  required.
- **Duration**: 60-minute session ceiling; first truthful accepted outcome
  within 10 minutes (matching the top-level SOW's own existing `done_when`
  clause, unchanged by this unit).
- **Sampling**: one fresh participant, one complete cold-start session,
  sufficient for 1.0; a blocking-defect correction requires a fresh cold-start
  session against the corrected exact head, with prior evidence preserved, not
  overwritten.
- **Three new scored tasks**, extending Tasks 1-7 (retained verbatim from
  `docs/andrea-chapters-0-7-evaluation.md`, maximum 14 across those seven,
  confirmed at this SOW's base commit):
  - Task 8: multi-SKU isolation.
  - Task 9: pilot-start structured evidence, replay, and refusal.
  - Task 10: distinguish the local mechanism from a real 30-day deployment,
    and identify ZEO Go as the production graduation path.

  Each new task scores 0-2, matching Tasks 1-7's own scale; new maximum 20 (14
  existing + 3 new tasks × 2).
- **Pass criteria**: at least 17/20; no zero on truth-critical Tasks 2, 7, 8,
  9, or 10; first accepted outcome within 10 minutes; complete session within
  60 minutes.

Build the machine-checkable pre-check
(`scripts/evaluate_andrea_chapters_0_12.py`, following
`scripts/evaluate_andrea_chapters_0_7.py`'s own established shape — stdlib
plus the production package, executes the cold-start path exactly as the new
document writes it, scores reachability and durable evidence, explicitly
declines to score what requires a human reader rather than inventing a score)
covering Tasks 8-9's own machine-checkable reachability/evidence portions (not
Task 10, which is a comprehension question a human must score). This unit
builds and runs the pre-check; it does not run the human session itself.

### 3. Curriculum verification extended to the installed-wheel path — a distinct release gate (governing ruling Holding 4)

`scripts/verify_curriculum.py` remains the structural gate, unweakened,
covering all 13 chapters (Chapters 0-12; Unit 12 adds no Chapter 13).

Build a new, distinct script, `scripts/verify_release_candidate.py`, that:

- runs all 13 exercises twice from fresh roots (matching the discipline
  `docs/sows/sovereign-agent-v1-unit11-store-expansion-pilot-start.md`'s own
  "Gate" section already established for `verify_curriculum.py`, extended
  here to the release-candidate context specifically);
- builds the wheel, installs it in a clean Python 3.14 environment outside the
  source tree, and runs every chapter's exercise against that installed
  artifact (not the source-tree package);
- mechanically validates the new Chapters 0-12 Andrea rubric's
  machine-checkable portions (invoking `evaluate_andrea_chapters_0_12.py`'s own
  reachability/evidence checks);
- confirms `verify_proof_pack.py` itself passes against whatever manifest state
  exists at gate time (partial-but-honest `NOT_RUN` rows included);
- confirms provider-status truthfulness (no row claims `LIVE_PASS` without a
  correspondingly real, verifiable evidence file backing it);
- confirms the local-pilot non-claim boundary (no committed evidence anywhere
  in this unit's own output claims the real pilot-start act occurred, matching
  the same grep-based discipline Unit 11's own "what this unit did not do"
  sections used).

This is a **distinct** gate from `verify_curriculum.py`, per the ruling's own
instruction not to overload one script with unrelated release responsibilities
— `verify_curriculum.py`'s own scope (chapter structure, sequence, instructor
notes, frontmatter, rulings-index agreement) does not grow.

Renderer independence is preserved (per
`docs/rulings/2026-08-27-book-publication-destination.md`); this unit adds no
publication pipeline of its own.

### 4. Conditional, truthful provider-status reporting (governing ruling Holding 6)

For each of Claude, Codex, and Cursor, build the reporting path that produces
one of the four allowed proof-pack statuses truthfully:

- run the existing non-submitting capability probe when the provider's
  executable exists (the same probe `sovereign-agent doctor` already performs,
  reused here rather than reimplemented);
- run the existing read-only and workspace-write live assignment tests
  (`tests/test_providers_live.py`, the 9 tests already built under Unit 6, all
  still deselected by default) only with explicit opt-in
  (`SOVEREIGN_AGENT_LIVE_ASSIGNMENTS=1`, the flag that already exists);
- never record credentials or unredacted provider output anywhere in the
  manifest or its evidence files;
- report `LIVE_PASS` only when a live assignment genuinely completed
  successfully with real, verifiable evidence; `NOT_RUN_UNAVAILABLE` when the
  executable is absent; `NOT_RUN_UNAUTHENTICATED` when the executable exists
  but no credential is available; `FAIL` when a live assignment was attempted
  and failed because of Sovereign Agent's own behavior (which blocks release
  until fixed, per the governing ruling).

This unit's own implementation environment is expected to hold no live
provider credentials — matching every prior unit's own confirmed state
(`env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API"` empty).
The proof-pack fields this unit itself produces will therefore genuinely show
`NOT_RUN_UNAUTHENTICATED` or `NOT_RUN_UNAVAILABLE` for all three providers —
this is the correct, honest state for this unit's own acceptance, not a gap to
paper over. Obtaining `LIVE_PASS` evidence, if ever pursued, is a separate,
later, explicitly-authorized act using real credentials this unit does not
hold or request.

### 5. Soak terminology correction, additive (governing ruling Holding 7)

Correct the stale unqualified "Unit 12 Andrea soak" phrasing confirmed present
in `docs/andrea-chapters-0-7-evaluation.md` (the exact line the Unit 12 scope
descent identified) with an explicit terminology note identifying it as
superseded wording, additively — matching this project's own established
discipline throughout this session of naming a stale phrase rather than
silently rewriting it. Do not touch any historical accepted SOW, acceptance
record, or `docs/v0.6-soak.md`. The new `docs/andrea-chapters-0-12-evaluation.md`
document itself must use only "Andrea live evaluation" throughout, never
unqualified "soak."

### 6. Correct the top-level design memo's own `done_when` requirement, additively (governing ruling Holding 1)

**Added 2026-08-31**, closing a gap the Principal identified: the original
version of this SOW cited the governing ruling's Holding 1 replacement text
but never required implementing it against the top-level design memo it
actually governs. Implementation could satisfy every other requirement in
this SOW while leaving `docs/sows/sovereign-agent-v1-educational-control-plane.md`'s
own binding `done_when` clause still reading the superseded line — a real gap,
not a cosmetic one, since that document's `done_when` field is this project's
own binding completion criterion for the whole 1.x line, not merely
descriptive prose.

Add, additively, to `docs/sows/sovereign-agent-v1-educational-control-plane.md`:
a dated correction note (matching the pattern this session's own Unit 11
rulings and SOW corrections already established — name the superseded line,
do not delete it, state the replacement, cite the ruling) identifying that the
`done_when` clause's line
"30-day Sovereign Store pilot -> redacted proof pack accepted" and sequencing
amendment 6's clause "then starts the 30-day pilot. Unit 12 finishes the
pilot..." are both superseded by
`docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md`
(already true and already ruled, but never yet annotated directly on the
document those clauses live in) and by
`docs/rulings/2026-08-31-unit12-scope.md`'s own Holding 1, whose replacement
text is:

> local, learner-controlled Sovereign Store release evaluation -> redacted Unit 12 proof pack accepted

The original `done_when` line and amendment 6's own original wording remain
intact, unedited — this is an additive correction note, not a rewrite,
matching every other correction this project's history has made to a
superseded-but-preserved passage.

## Explicit statements this SOW must make, and does — restated here per this
## project's own standing instruction, not left implicit

- **Merging this SOW establishes the reviewed contract but does not authorize
  implementation.** Stated in "Authorization" above.
- **Implementation requires a separate Principal decision bound to the
  verified SOW merge commit.** Stated in "Authorization" above.
- **This unit's implementation being merged, gated, and verified on `main`
  does not mean the Andrea live evaluation has run, the release candidate has
  been published, the final release has occurred, or this document's status
  has flipped to `ACCEPTED`** — each of those requires its own separate,
  later authorization and review. Stated in "Authorization" above and in
  "Final Unit 12 closure conditions" below.
- **No real pilot-start act, real 30-day deployment, or governance receipt is
  performed or required by this unit.** Stated in "Mission" above, matching
  the governing ruling's own Holding 1.
- **Credentialed provider `LIVE_PASS` evidence is not produced by this unit's
  own implementation** — this environment holds no live credentials. Stated
  in "Required implementation" §4 above.

## Explicit non-scope

Do not:

- perform the real pilot-start act, or claim a real 30-day deployment pilot
  occurred;
- run the Andrea live evaluation itself (build the protocol and the
  machine-checkable pre-check only);
- obtain or claim `LIVE_PASS` provider evidence using real credentials this
  unit's own implementation environment does not hold;
- publish `1.0.0rc1` to TestPyPI, tag `v1.0.0`, or publish to PyPI — building
  the mechanism this unit's evidence will eventually support is in scope;
  invoking the actual publish sequence is not;
- flip this document's own status to `ACCEPTED`;
- add a Chapter 13 or any content beyond the existing 13-chapter curriculum;
- rewrite `docs/andrea-alpha-evaluation.md` or
  `docs/andrea-chapters-0-7-evaluation.md`;
- touch `docs/v0.6-soak.md` or any historical accepted SOW/acceptance record;
- weaken any existing fencing, mailbox, workspace, Pulse-attribution, or
  Store-isolation guarantee from Units 7-11;
- change the runtime dependency surface beyond Pydantic plus stdlib;
- silently exceed or silently compress against the current source budget (see
  "Budget" below);
- overload `scripts/verify_curriculum.py` with release-gate responsibilities
  that belong in the distinct `scripts/verify_release_candidate.py`.

## Budget

`scripts/verify_source_budget.py` scopes only to `src/sovereign_agent/`. At
this SOW's base commit: `27/40 modules, 6208/6250 nonblank lines, 7/30 root
exports` — **42 lines of headroom**, confirmed by direct run at this SOW's
exact base commit.

**This unit's own required implementation is expected to need zero
`src/sovereign_agent/` changes.** The proof-pack manifest/verifier, the new
release-candidate gate script, and the new Andrea evaluation document/script
are all release/curriculum/documentation surfaces living in `scripts/`,
`docs/`, and evidence directories — the same split Unit 9 established for
`pulse_gate.py` and Unit 11 continued for `pilot.py`. If implementation
genuinely discovers a need to touch `src/sovereign_agent/` core primitives
(for example, if the proof-pack verifier's secret-shaped-content detection
needs a shared helper that belongs in core rather than in `scripts/`), **stop
and request a precise budget ruling before writing that code** — 42 lines is
a hard, small ceiling; do not compress correctness to fit it, and do not treat
a granted amendment as license to pad.

## Gate

Run at the exact implementation head:

```bash
uv lock --check
make verify
python scripts/verify_curriculum.py
python scripts/verify_curriculum.py
python scripts/verify_source_budget.py
python scripts/verify_proof_pack.py
python scripts/verify_release_candidate.py
git diff --check
```

Run `verify_curriculum.py` twice consecutively (existing discipline).
`verify_release_candidate.py` itself runs the 13 exercises twice from fresh
roots and the full installed-wheel path, per "Required implementation" §3
above — this is a heavier gate than any prior unit's own, matching this unit's
own release-gate mission. Build the wheel, install into a clean Python 3.14
environment outside the source tree, run `sovereign-agent --help`,
`sovereign-agent doctor`, `sovereign-agent demo store --mode simulated --root
/tmp/<somewhere-outside-source>` from that installed wheel (existing
discipline, reconfirmed here as part of the release gate specifically, not
merely as a general sanity check). Live-provider tests remain deselected and
must be reported as unrun, with the exact `NOT_RUN_*` status this unit's own
proof-pack manifest records.

## Review and merge ritual

1. Stream implements on `unit-12/release-evaluation`; it does not open or
   merge its own PR.
2. Master independently reads the implementation, runs the proof-pack
   verifier and the release-candidate gate directly, and reproduces the
   mutation checks for every new mechanical guarantee.
3. Master independently mutation-checks at least:
   - a proof-pack manifest with a missing required field — the verifier must
     catch this;
   - a proof-pack manifest claiming `LIVE_PASS` for a provider with no
     corresponding real evidence file — the verifier must catch this;
   - a proof-pack manifest with an evidence path that escapes
     `docs/evidence/unit12/` — the verifier must catch this;
   - a proof-pack manifest whose digest does not match its evidence file —
     the verifier must catch this;
   - the installed-wheel exercise path silently falling back to the
     source-tree package instead of the installed one — the release-candidate
     gate must catch this (matching the same "prove the isolation, don't
     assume it" discipline Unit 11's own disposable-identity guard used).
4. Master opens the PR and names its exact head.
5. Sparring reviews that exact head against this SOW and the governing scope
   ruling.
6. No merge over `CHANGES_REQUESTED`.
7. Principal acceptance is requested explicitly after Sparring co-signs.
8. Merge only through the allowed GitHub PR mechanism.
9. Gate merged `main` from a clean clone.
10. Audit `docs/v1-unit12-release-evaluation.md` (the documentation
    deliverable this unit adds) against merged behavior.
11. **This unit's implementation acceptance (steps 1-10 above) is complete at
    this point, but this document's own status stays `PROPOSED` and Unit 12
    is not yet closed.** Merged, verified behavior on `main` is not, by
    itself, Unit 12's closure — matching the exact pattern
    `docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md`
    established for Unit 11's own closure sequence.
12. The Andrea live evaluation runs as a separate, later, separately-
    authorized human session, using the protocol this unit built. Its result
    is recorded in the proof-pack manifest once complete.
13. The `1.0.0rc1` release candidate is produced and published to TestPyPI
    (governing ruling Holding 5, steps 2-3), under its own separate
    authorization, and the redacted proof pack is filed and reviewed
    (Holding 5, step 4).

**Correction (2026-08-31):** the original version of this section, and the
"Final Unit 12 closure conditions" section below, treated the final `v1.0.0`
PyPI release as an act that "may follow" Unit 12's own closure — inverting
the governing ruling's own explicit, single, numbered ten-step Holding 5
sequence, where step 10 ("Close Unit 12 only after...") comes strictly after
steps 5-9 (final release authorization, tagging, publication, PyPI
verification, and installation-documentation correction). "Separately
authorized" (true — the final release needs its own distinct Principal act,
step 5, distinct from release-candidate authorization) does not mean "may
happen after closure" (false — the ruling's own step numbering is one
sequence, not two independently orderable branches). Corrected below to
match the ruling's own order exactly.

14. The Principal separately authorizes the final release (Holding 5, step 5,
    distinct from and later than the release-candidate authorization in step
    13 above). Master sets the final version and tags the authorized exact
    commit `v1.0.0` (Holding 5, step 6); the existing trusted-publisher
    workflow publishes to PyPI (Holding 5, step 7).
15. Master verifies the published PyPI artifact from outside the
    repository — JSON metadata, wheel and sdist installation, Python floor,
    dependency metadata, CLI, README, repository provenance, and artifact
    digests (Holding 5, step 8) — and corrects installation documentation to
    describe the actually published 1.x line (Holding 5, step 9).
16. Only after that verified, corrected publication exists does the reviewed
    `PROPOSED -> ACCEPTED` flip for this document (in a later, separate
    reviewed change, per this project's own standing convention) follow.
17. Unit 12 is closed only once that flip lands and `main` is gated once more
    from a clean clone (governing ruling Holding 5, step 10).

If `main` advances, reconcile through an auditable PR-based path and rerun
gates and review on the resulting exact head. A prior co-sign does not survive
a head change.

## Documentation deliverables

Add `docs/v1-unit12-release-evaluation.md`, following the shape established by
`docs/v1-unit7-workspace-lifecycle.md` through
`docs/v1-unit11-store-expansion-pilot-start.md`: status header (status
`PROPOSED` until a separate reviewed acceptance flip), the contract as
testable properties, a verified "how to check this document against the
repository" command block (every command run and confirmed working before
being written into the doc), a budget-impact statement, a "what this unit did
not do" section (explicitly naming that the Andrea live evaluation was not
run, no `LIVE_PASS` provider evidence was obtained, and no release tag was
published), and explicit non-claims.

Add `docs/andrea-chapters-0-12-evaluation.md` (§2 above).

Add the additive correction note to
`docs/sows/sovereign-agent-v1-educational-control-plane.md` (§6 above).

Update `CHANGELOG.md` following the established per-unit style. Update
`book/README.md`'s chapter index if it references curriculum completion state
that changes (confirm current wording before deciding whether an update is
needed — do not assume).

## Implementation-acceptance conditions

The Unit 12 **implementation** is technically accepted only when the Principal
can inspect the merged tree and confirm:

- `docs/evidence/unit12/proof-pack.json`'s schema and `verify_proof_pack.py`
  exist, reject every malformed-input class named in "Required implementation"
  §1, and accept a genuinely honest partial manifest (real gate/curriculum/
  installed-wheel/local-pilot evidence, `NOT_RUN_*` for Andrea and all three
  providers);
- `docs/andrea-chapters-0-12-evaluation.md` exists, defines the full protocol
  per Holding 3, and its machine-checkable pre-check
  (`scripts/evaluate_andrea_chapters_0_12.py`) runs and reports honestly what
  it can and cannot itself score;
- `scripts/verify_release_candidate.py` exists, runs the 13 exercises twice
  from fresh roots, verifies the installed-wheel path outside the source
  tree, and is demonstrably distinct from `scripts/verify_curriculum.py`
  (the latter's own scope unchanged);
- provider-status reporting produces exactly the four allowed values, never a
  fabricated `LIVE_PASS`, and this unit's own gate run shows the honest
  `NOT_RUN_*` state for all three providers;
- the stale "Unit 12 Andrea soak" phrasing is corrected additively, and the
  new Andrea document uses only "Andrea live evaluation";
- the top-level design memo
  (`docs/sows/sovereign-agent-v1-educational-control-plane.md`) carries an
  additive correction note identifying its `done_when` clause and sequencing
  amendment 6's own text as superseded by the governing ruling's Holding 1
  replacement, with the original text preserved unedited;
- every new mechanical guarantee is demonstrably load-bearing
  (mutation-checked, not merely present);
- the `src/sovereign_agent/` budget is respected — expected unchanged at
  `27/40 modules, 6208/6250 nonblank lines, 7/30 root exports` — or a precise
  amendment was requested and granted before implementation, never silently
  exceeded or compressed against;
- no live-provider evidence is claimed;
- the Andrea live evaluation was NOT run, and this is stated explicitly, not
  merely omitted;
- no release tag was published and this is stated explicitly;
- **no completed proof pack exists yet, and this is expected, not a gap** —
  the manifest this unit produces is genuinely partial (real gate evidence,
  honest `NOT_RUN` for what this unit cannot itself produce), and completing
  it is later, separately-authorized work, not something this unit's
  implementation needs to finish.

Proceed first by filing and reviewing this SOW. Do not begin implementation
before it is merged unchanged or a subsequent Principal ruling amends it.

## Final Unit 12 closure conditions

**Correction (2026-08-31):** this section previously listed six conditions and
treated the final `v1.0.0` PyPI release as an act that "may follow" closure —
inverting the governing ruling's own single, explicitly numbered Holding 5
sequence, where step 10 ("Close Unit 12 only after...") comes strictly after
steps 5-9 (final release authorization, tagging, publication, PyPI
verification, installation-documentation correction). Corrected to nine
conditions below, matching the ruling's own order exactly — separate
authorization for the final release (a real, distinct Principal act) does not
mean the release may happen after closure; it means closure waits for it.

Unit 12 is closed only when all of the following hold, in this order:

1. Implementation acceptance (above) is satisfied, and the merged
   implementation is gated and audited on a clean `main` clone
   (Review-and-merge-ritual steps 1-10).
2. The Andrea live evaluation has run under its own separate authorization
   (step 12), scoring at least 17/20 with no zero on Tasks 2, 7, 8, 9, or 10,
   within the 60-minute/10-minute bounds.
3. The `1.0.0rc1` release candidate has been produced, published to TestPyPI,
   and verified from outside the repository (Holding 5, steps 2-3).
4. The redacted proof pack has been filed with real evidence for every field
   this unit's own gate and the Andrea evaluation can produce, reviewed by
   Sparring, and accepted by the Principal as a release candidate (Holding 5,
   step 4; governing ruling Holding 2).
5. The Principal has separately authorized the final release — a distinct
   act from release-candidate authorization in step 3 (Holding 5, step 5).
6. The final version has been set, the authorized exact commit tagged
   `v1.0.0`, and the existing trusted-publisher workflow has published it to
   PyPI (Holding 5, steps 6-7).
7. The published PyPI artifact has been verified from outside the
   repository — JSON metadata, wheel and sdist installation, Python floor,
   dependency metadata, CLI, README, repository provenance, artifact digests
   — and installation documentation corrected to describe the actually
   published 1.x line (Holding 5, steps 8-9).
8. This document's own status has flipped `PROPOSED -> ACCEPTED` in a
   separate, reviewed change.
9. `main` has been gated once more from a clean clone after that flip lands
   (Holding 5, step 10).

Only after all nine hold is Unit 12 closed.

## Related documents

- [Sovereign Agent 1.0 — executable textbook (design memo)](sovereign-agent-v1-educational-control-plane.md)
- [Ruling: Unit 12 scope — release evaluation, proof pack, Andrea protocol, provider truthfulness, release sequence](../rulings/2026-08-31-unit12-scope.md)
- [Ruling: Unit 11 closes on local, learner-controlled SQLite — the real-deployment pilot-start gate is withdrawn](../rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md)
- [Deferral: credentialed provider smokes are Unit 12](../rulings/2026-08-26-deferral-unit6-smokes.md)
- [Ruling: the book is published by `zeo-site`; this repository builds no site](../rulings/2026-08-27-book-publication-destination.md)
- [Unit 11 SOW: Store expansion, Chapters 8-12, pilot-start mechanism](sovereign-agent-v1-unit11-store-expansion-pilot-start.md)
- [Unit 10 SOW: curriculum completion, Chapters 0-7](sovereign-agent-v1-unit10-curriculum-completion.md)
- [Unit 9 SOW: Pulse and proactive governed work](sovereign-agent-v1-unit9-pulse-proactive-work.md)
