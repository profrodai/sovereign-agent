# Unit 12: release evaluation, redacted proof pack, Andrea protocol extension

- **status:** PROPOSED (implementation on `unit-12/release-evaluation`, not
  yet independently reviewed or merged; this document's own status flips
  `PROPOSED -> ACCEPTED` only in a later, separate reviewed change, per the
  governing SOW's own "Review and merge ritual")
- **authority:** principal (implementation authorization requested and
  granted separately from the governing SOW's own merge, per that SOW's
  "Authorization" section)
- **base:** `main = a17a01a6926168234ebf9622076ac2cf258da5ed` (the exact
  merged Unit 12 SOW commit this implementation branched from)
- **governing SOW:**
  [`docs/sows/sovereign-agent-v1-unit12-release-evaluation.md`](sows/sovereign-agent-v1-unit12-release-evaluation.md)
- **governing ruling:**
  [`docs/rulings/2026-08-31-unit12-scope.md`](rulings/2026-08-31-unit12-scope.md)
- **applies_to:** Sovereign Agent 1.x, Unit 12
- **work branch:** `unit-12/release-evaluation`

This document follows `docs/v1-unit11-store-expansion-pilot-start.md`,
`docs/v1-unit10-curriculum-completion.md`, `docs/v1-unit9-pulse-proactive-
work.md`, `docs/v1-unit8-supervisor-fencing-recovery.md`, and
`docs/v1-unit7-workspace-lifecycle.md`'s own shape: a contract stated as
testable properties, then how to check each one against the repository. It
is **additive** — nothing in the Units 0-11 acceptance record is touched or
revised here.

## What Unit 12 is, in one sentence

Unit 12 builds the redacted proof-pack manifest and its field-schema-aware
verifier, extends the Andrea evaluation protocol to the full 13-chapter
curriculum with three new scored tasks, builds a distinct release-candidate
gate covering the installed-wheel path, wires conditional truthful
provider-status reporting, and additively corrects two stale passages
(the "Unit 12 Andrea soak" phrasing and the top-level design memo's
withdrawn pilot-completion `done_when` clause) — without performing the real
pilot-start act, running the Andrea live evaluation itself, obtaining live
provider credentials, or publishing any release.

## The contract

### Property 1 — the redacted proof-pack manifest and its field-schema-aware verifier

`docs/evidence/unit12/proof-pack.json` records, exactly as governing ruling
Holding 2 requires: exact source and release-candidate commits, Python and
package versions and artifact digests, deterministic gate and curriculum
results, installed-wheel results outside the source tree, local disposable
pilot-mechanism evidence, the Andrea live-evaluation result, one status row
per provider, redactions performed, explicit non-claims, and evidence-file
paths with SHA-256 digests. Provider status is exactly one of `LIVE_PASS`,
`NOT_RUN_UNAVAILABLE`, `NOT_RUN_UNAUTHENTICATED`, `FAIL`
(`scripts/proof_pack_schema.py`'s own `PROVIDER_STATUSES`), enforced by the
manifest's own schema, not left to free text.

`scripts/verify_proof_pack.py` rejects, each with a specific named reason:
missing required fields, an unknown provider status value, a SHA-256 digest
mismatch, any evidence path escaping `docs/evidence/unit12/` (mirroring
`sovereign_agent.workspace.safe_join`'s own `resolve()`-based discipline —
`..`, absolute paths, and symlink traversal are all caught the same way),
and secret-shaped content.

**The secret-shaped-content check is field-schema-aware, not a blind
content scan** — the exact contract the SOW's own §1 was rewritten twice to
state precisely. Fields with a known fixed shape (commit SHAs: 40 lowercase
hex characters; SHA-256 digests: 64 lowercase hex characters; semantic
versions; evidence paths) are validated against that shape alone and are
**never** rejected merely for being long. Free-text fields (redaction notes,
non-claims, descriptions) are scanned for exactly two narrow patterns: (a) a
known credential environment-variable name — `ANTHROPIC_API_KEY`,
`ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, `CODEX_API_KEY`,
`CURSOR_API_KEY`, read directly from each provider adapter's own
`authentication_environment` tuple — immediately followed by `=` and a real
value; a bare variable name, or a redaction note merely naming one, is never
itself a rejection; (b) a literal `Bearer <token>` shape. No entropy
heuristic anywhere.

This unit's own gate produced a real, genuinely partial manifest: real
commit SHA, real wheel digest, real deterministic-gate and installed-wheel
evidence, real local disposable pilot-mechanism evidence — and honest
`NOT_RUN` states for the Andrea live evaluation and all three providers,
because this unit's own implementation cannot itself produce those.

### Property 2 — the Andrea evaluation, extended to the full curriculum

`docs/andrea-chapters-0-12-evaluation.md` retains Tasks 1-7 verbatim
(maximum 14) and adds three new scored tasks: Task 8 (multi-SKU isolation),
Task 9 (pilot-start structured evidence, replay, and refusal), Task 10
(distinguishing the local mechanism from a real deployment and identifying
ZEO Go as the production graduation path). New maximum 20. Pass criteria:
at least 17/20, no zero on Tasks 2, 7, 8, 9, or 10, first accepted outcome
within 10 minutes, complete session within 60 minutes. It does not rewrite
either historical Andrea document and uses only "Andrea live evaluation"
throughout, never unqualified "soak."

`scripts/evaluate_andrea_chapters_0_12.py` covers Tasks 8-9's own
machine-checkable reachability/evidence portions: it runs Chapter 8's
exercise and independently re-queries the resulting database for a genuinely
isolated multi-SKU catalog, runs Chapter 12's exercise and independently
re-verifies the idempotent replay, then drives one further refusal case (a
different `pilot_id` while one is active) against the same database and
confirms no orphaned `pilots` row results. It explicitly declines to score
Task 10, a comprehension question only a human reader can score.

### Property 3 — a distinct release-candidate gate covering the installed-wheel path

`scripts/verify_release_candidate.py` is a new, distinct script —
`scripts/verify_curriculum.py`'s own scope (chapter structure, sequence,
instructor notes, frontmatter, rulings-index agreement) is unchanged. The
new gate:

- runs all 13 chapter exercises twice from fresh roots, against the
  source-tree package;
- builds the wheel, installs it into a clean Python 3.14 venv **outside**
  the source tree, and runs every exercise against that installed artifact
  — proving isolation directly, not assuming it: it asks the venv's own
  interpreter where `sovereign_agent` and `reference_organizations` resolve
  from and refuses unless that path sits inside the venv's own
  site-packages and outside this repository entirely;
- mechanically validates the new Chapters 0-12 Andrea rubric's
  machine-checkable portions;
- confirms `verify_proof_pack.py` passes against whatever manifest state
  exists at gate time;
- confirms no provider-status row claims `LIVE_PASS` without a real,
  existing evidence file backing it;
- confirms no evidence committed anywhere under `docs/evidence/unit12/`
  claims the real pilot-start act occurred — both by grepping for the exact
  retired real-pilot identifiers
  (`docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md`'s
  own Holding 5) and by a narrow real-pilot-claim shape pattern.

### Property 4 — truthful, conditional provider-status reporting

For each of Claude, Codex, and Cursor, this unit reuses the existing
non-submitting capability probe (the same one `sovereign-agent doctor`
already runs) and the existing `tests/test_providers_live.py` (9 tests,
opt-in via `SOVEREIGN_AGENT_LIVE_ASSIGNMENTS=1`, confirmed still collected
and deselected). This implementation environment holds all three provider
executables but no credentials
(`env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API"` empty),
so this unit's own gate run correctly and honestly reports
`NOT_RUN_UNAUTHENTICATED` for all three — the correct state for this unit's
own acceptance, not a gap.

### Property 5 — soak terminology corrected additively

`docs/andrea-chapters-0-7-evaluation.md`'s stale "Unit 12 Andrea soak"
phrasing is unedited at its own citation; a dated terminology note directly
below it names the phrase as superseded, states the current terminology
("Andrea live evaluation"), and cites
`docs/rulings/2026-08-31-unit12-scope.md`'s Holding 7. `docs/v0.6-soak.md`
and every historical accepted SOW/acceptance record are untouched. The new
`docs/andrea-chapters-0-12-evaluation.md` uses only "Andrea live evaluation"
throughout.

### Property 6 — the top-level design memo corrected additively

`docs/sows/sovereign-agent-v1-educational-control-plane.md` carries a dated
additive correction note (inserted directly after its own intro paragraph,
before "Decision in one sentence") identifying that the `done_when` clause's
"30-day Sovereign Store pilot -> redacted proof pack accepted" line and
sequencing amendment 6's "then starts the 30-day pilot. Unit 12 finishes the
pilot..." clause are both superseded, citing
`docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md`
and `docs/rulings/2026-08-31-unit12-scope.md`'s Holding 1, and quoting that
holding's exact replacement text. Both original passages remain intact,
unedited, at their own original citations.

## How to check this document against the repository

Every command below was run against this unit's own implementation head
before being written down.

```bash
uv lock --check
make verify
python scripts/verify_curriculum.py
python scripts/verify_curriculum.py   # run twice consecutively, per the gate
python scripts/verify_source_budget.py
python scripts/verify_proof_pack.py
python scripts/verify_release_candidate.py
git diff --check

# Property 1 -- the manifest exists and verifies
cat docs/evidence/unit12/proof-pack.json | python3 -m json.tool >/dev/null

# Property 2 -- the new Andrea document and its pre-check
python scripts/evaluate_andrea_chapters_0_7.py
python scripts/evaluate_andrea_chapters_0_12.py

# Property 4 -- credential absence confirmed, same as every prior unit
env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API" || true

# 9 credentialed provider tests remain collected, deselected, and unrun
uv run --python 3.14 pytest tests/test_providers_live.py --collect-only -q -m live

# Property 5 -- the stale phrase is preserved, and a dated correction note follows it
grep -n "Unit 12 Andrea soak" docs/andrea-chapters-0-7-evaluation.md
grep -n "Terminology correction (2026-08-31)" docs/andrea-chapters-0-7-evaluation.md

# Property 6 -- both original superseded passages remain intact, and the
# correction note citing their replacement exists
grep -n "30-day Sovereign Store pilot -> redacted proof pack accepted" \
  docs/sows/sovereign-agent-v1-educational-control-plane.md
grep -n "30-day pilot. Unit 12 finishes the" \
  docs/sows/sovereign-agent-v1-educational-control-plane.md
grep -n "Correction (2026-08-31), additive" \
  docs/sows/sovereign-agent-v1-educational-control-plane.md
```

Confirmed at implementation head: `uv lock --check` resolves cleanly;
`make verify` passes format, lint, mypy strict, the full non-live test suite
(358 passed, 9 deselected), the runtime-dependency check (`pydantic` only),
and the source budget; `verify_curriculum.py` reports `curriculum sound: 13
chapters, 13 exercises executed, all links resolve` on two consecutive runs
(unchanged in scope by this unit); `verify_proof_pack.py` reports the
manifest valid; `verify_release_candidate.py` passes all six stages (twice
from fresh roots, installed-wheel isolation proven, the new Andrea
rubric's machine-checkable portions, the proof-pack manifest, the
no-unbacked-LIVE_PASS check, the local-pilot non-claim boundary); `git diff
--check` reports no whitespace errors.

## Mutation checking

Every new mechanical guarantee was falsified before being reported as done:
a plausible break was reproduced, confirmed to have actually landed (`diff`
against a pristine copy), confirmed caught with a specific named reason,
then restored to byte-identical and the check reconfirmed green.

1. **Missing required field.** `andrea_live_evaluation` was deleted from
   the manifest. `diff` confirmed the mutation landed.
   `verify_proof_pack.py` correctly refused: `FAIL: missing required field:
   andrea_live_evaluation`. Restored; `diff` confirmed byte-identical;
   `verify_proof_pack.py` reconfirmed valid.
2. **`LIVE_PASS` with no real evidence file.** `provider_status.claude`'s
   own status was changed to `LIVE_PASS` with no `evidence_path` at all,
   then (a second variant) with an `evidence_path` naming a file that does
   not exist. Both were caught: the first by `verify_proof_pack.py`
   directly (`status is LIVE_PASS but no evidence_path is recorded`); the
   second was **not** caught by the verifier's original form — a genuine
   gap found during this unit's own mutation testing, closed by adding a
   file-existence check to `verify_proof_pack.py`'s own `LIVE_PASS`
   handling (previously only `scripts/verify_release_candidate.py`'s own
   `confirm_no_false_live_pass` caught the missing-file case). After the
   fix, `verify_proof_pack.py` itself correctly refuses:
   `status is LIVE_PASS but evidence_path 'nonexistent_live_evidence.json'
   does not exist -- an unbacked LIVE_PASS claim`. Restored; `diff`
   confirmed byte-identical; reconfirmed valid.
3. **Path-escaping evidence reference.** `evidence_files[0].path` was
   changed to `../../../etc/passwd`, then to the absolute path
   `/etc/passwd`. `diff` confirmed each mutation landed. Both were
   correctly refused: `evidence path '../../../etc/passwd' escapes
   docs/evidence/unit12/` and `evidence path '/etc/passwd' is absolute
   (escapes evidence dir)`. Restored; `diff` confirmed byte-identical;
   reconfirmed valid.
4. **Mismatched digest.** `evidence_files[0].sha256` was overwritten with
   64 `a` characters. `diff` confirmed the mutation landed.
   `verify_proof_pack.py` correctly refused: `recorded sha256
   'aaaa...' does not match the file's actual digest 'e8ed...'`. Restored;
   `diff` confirmed byte-identical; reconfirmed valid.
5. **Valid manifest with real commit SHAs and real digests passes (the
   decisive field-schema-aware falsification).** The pristine manifest's
   own `source_commit`
   (`a17a01a6926168234ebf9622076ac2cf258da5ed`, 40 lowercase hex
   characters) and `artifact_digests.wheel_sha256`
   (`f53a4558a475d8cf3c379ff2bd2dc5cfa2362aa496b2d05594ce2e9bbade332d`, 64
   lowercase hex characters) were confirmed present, unmodified, and
   `verify_proof_pack.py` reported the manifest **valid** — neither field
   was rejected as secret-shaped. This is the exact case the SOW's own
   verifier contract was rewritten twice to guarantee, proven here for
   real, not merely asserted.
6. **The same valid manifest with an injected unredacted secret (paired
   with 5 above).** A credential assignment
   (`ANTHROPIC_API_KEY=sk-ant-real-looking-secret-value-123456`) was
   appended to `redactions_performed[0]`'s own free-text prose; a separate
   mutation appended a `Bearer <token>` shape
   (`Authorization: Bearer sk-live-abcdef123456`) to `non_claims[0]`.
   `diff` confirmed each mutation landed. Both were correctly refused:
   `redactions_performed[0]: contains an unredacted credential assignment
   (ANTHROPIC_API_KEY=...)` and `non_claims[0]: contains a literal
   Bearer-token shape`. Restored; `diff` confirmed byte-identical;
   reconfirmed valid. Together with check 5, this proves the
   field-schema-aware fix works on both sides: known-shape fields pass,
   free-text fields carrying an actual secret fail.
7. **Unknown provider status value.** `provider_status.codex.status` was
   changed to `PROBABLY_FINE`. `diff` confirmed the mutation landed.
   Correctly refused: `unknown value 'PROBABLY_FINE'`. Restored;
   reconfirmed valid.
8. **The "NOT_RUN means PASS" lie.** `provider_status.claude.reason`'s own
   free text had `"live evaluation passed anyway"` appended. `diff`
   confirmed the mutation landed. Correctly refused: `prose claims success
   ('passed live') alongside a NOT_RUN status`. Restored; reconfirmed
   valid.
9. **The installed-wheel exercise path silently falling back to the
   source-tree package.** `confirm_installed_package_is_actually_used`
   was mutated to inject `PYTHONPATH=<repo>/src` into the venv-interpreter
   probe's own environment, reproducing exactly the defect class this
   check exists to catch. `diff` confirmed the mutation landed. Both
   modules correctly resolved to the source tree under the mutated
   environment, and `verify_release_candidate.py` correctly refused:
   `installed-wheel exercise path is NOT isolated from the source tree:
   sovereign_agent resolved to .../src/sovereign_agent/__init__.py, inside
   ... -- this is exactly the silent source-tree fallback this gate exists
   to catch` (and identically for `reference_organizations`). This
   falsification also surfaced a genuine secondary bug in the isolation
   check's own control flow (an `if`/`else` that still fell through to a
   second, misleadingly-worded check after the first had already failed);
   fixed to a clean `if ... continue` while the mutation was still in
   place, reconfirmed the fix produces exactly one correctly-worded
   failure per module, then the `PYTHONPATH` mutation itself was reverted.
   `diff` against the pristine file confirmed only the legitimate bugfix
   remained; `verify_release_candidate.py` reconfirmed passing all six
   stages.
10. **The local-pilot non-claim boundary.** The real pilot's disposable
    identifier in `local_pilot_mechanism_evidence.json` had the text
    `" A real production pilot started and is running."` appended. `diff`
    confirmed the mutation landed. Two independent checks both correctly
    fired: the digest mismatch (`verify_proof_pack.py`, since the file no
    longer matched its recorded `sha256`) and, independently, the
    release-candidate gate's own Stage 5 real-pilot-claim pattern
    (`text matches the shape of a real-pilot claim`) — proving Stage 5 is
    genuinely load-bearing on its own, not merely redundant with the
    digest check. Restored; `diff` confirmed byte-identical; reconfirmed
    clean.

`verify_proof_pack.py` and `verify_release_candidate.py` were both
reconfirmed green after every restoration and at final completion.

## Budget impact

Reproduced by `scripts/verify_source_budget.py`, before and after this
unit's change:

| | modules | nonblank lines | root exports |
| --- | --- | --- | --- |
| Before (this SOW's base) | 27/40 | 6208/6250 | 7/30 |
| After (this unit) | 27/40 | 6208/6250 | 7/30 |

**Zero change to `src/sovereign_agent/`.** Every deliverable this unit adds
(the proof-pack schema and verifier, the release-candidate gate, the new
Andrea document and its pre-check script, the evidence files) lives in
`scripts/`, `docs/`, and `docs/evidence/unit12/` — outside this budget's own
scope, the same split Unit 9 established for `pulse_gate.py` and Unit 11
continued for `pilot.py`. No budget amendment was requested or needed; the
42-line headroom against the 6250 ceiling this SOW's own "Budget" section
named is untouched.

## What this unit did not do

- **Did not perform the real pilot-start act or claim a real 30-day
  deployment pilot occurred.** `start_pilot` is called only against the
  disposable identity `book-ch12-exercise-pilot`, by Chapter 12's own
  exercise and by this unit's own Andrea pre-check script. No real pilot
  identity, real Store organization id, or real pilot-profile id appears
  anywhere in this unit's own implementation or evidence.
- **Did not run the Andrea live evaluation itself.** Only its
  machine-checkable pre-check (Tasks 8-9's reachability/evidence portions)
  ran. The proof-pack manifest's own `andrea_live_evaluation` field records
  `NOT_RUN`, explicitly, not merely by omission.
- **Did not obtain or claim `LIVE_PASS` provider evidence.** This
  environment holds no live credentials
  (`env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API"`
  empty). All three providers show `NOT_RUN_UNAUTHENTICATED` in the
  manifest, honestly, because their executables are present but no
  credential is available.
- **Did not publish `1.0.0rc1` to TestPyPI, tag `v1.0.0`, or publish to
  PyPI.** The manifest's own `release_candidate_commit` field is `null`.
  This unit builds the mechanism the eventual release-candidate sequence
  will use; it does not invoke that sequence.
- **Did not itself flip this document's own status to `ACCEPTED`, or the
  governing SOW's own status.** Both flips happen in later, separate
  reviewed changes, per the governing SOW's own "Review and merge ritual."
- **Did not add a Chapter 13 or any content beyond the existing 13-chapter
  curriculum.** `verify_curriculum.py`'s own `REQUIRED_CHAPTERS` is
  unchanged at 13 entries.
- **Did not rewrite `docs/andrea-alpha-evaluation.md` or
  `docs/andrea-chapters-0-7-evaluation.md`.** The latter received only an
  additive terminology-correction note; neither historical document's own
  task text was altered.
- **Did not touch `docs/v0.6-soak.md` or any historical accepted SOW or
  acceptance record.**
- **Did not weaken any existing fencing, mailbox, workspace,
  Pulse-attribution, or Store-isolation guarantee from Units 7-11.**
  `make verify`'s own full non-live suite (358 passed) includes every
  pre-existing test file, unmodified in substance.
- **Did not change the runtime dependency surface.**
  `scripts/verify_runtime_dependencies.py` reports `pydantic` before and
  after.
- **Did not overload `scripts/verify_curriculum.py` with release-gate
  responsibilities.** That script's own `REQUIRED_CHAPTERS`, `RUNNABLE`,
  and every existing check are unchanged; the new release-gate
  responsibilities live entirely in the new, distinct
  `scripts/verify_release_candidate.py` (which imports
  `verify_curriculum`'s own chapter tables rather than duplicating them, to
  avoid a second, drifting copy of "13 chapters, 13 entry points").
- **Did not open or merge its own pull request.** Implementation happened
  on `unit-12/release-evaluation`; Master opens the PR after independently
  reproducing this unit's own mutation-testing evidence from scratch.

## Explicit non-claims

- No live-provider evidence is claimed anywhere in this document, this
  unit's own tests, or the proof-pack manifest.
  `env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API"` is
  empty, same as every prior unit.
- No claim that the real 30-day Store pilot has started, at any point,
  including after this document's own eventual `ACCEPTED` flip. Only
  Chapter 12's own disposable exercise identity, and this unit's own
  pre-check script using the same disposable prefix, have ever been passed
  to `start_pilot`.
- No claim that the Andrea live evaluation has run. Only its
  machine-checkable pre-check has run, and the manifest records that
  distinction explicitly.
- No claim that a completed, filed, or Sparring-reviewed proof pack exists.
  The manifest this unit produces is genuinely partial by design — real
  gate evidence, honest `NOT_RUN` for what this unit's own implementation
  cannot itself produce — and completing it is later, separately-authorized
  work.
- No claim that any release candidate, release tag, or PyPI publication
  exists.
- No claim that Chapters 13 or beyond exist.

## Related documents

- [SOW: Sovereign Agent 1.x — Unit 12 release evaluation, proof pack, Andrea protocol, 1.0.0 release](sows/sovereign-agent-v1-unit12-release-evaluation.md)
- [Ruling: Unit 12 scope — release evaluation, proof pack, Andrea protocol, provider truthfulness, release sequence](rulings/2026-08-31-unit12-scope.md)
- [Ruling: Unit 11 closes on local, learner-controlled SQLite — the real-deployment pilot-start gate is withdrawn](rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md)
- [Unit 11: Store expansion, Chapters 8-12, pilot-start mechanism](v1-unit11-store-expansion-pilot-start.md)
- [Unit 10: curriculum completion, Chapters 0-7](v1-unit10-curriculum-completion.md)
- [Unit 9: Pulse and proactive governed work](v1-unit9-pulse-proactive-work.md)
- [Unit 8: supervisor, fencing, and hard-kill recovery](v1-unit8-supervisor-fencing-recovery.md)
- [Unit 7: workspace lifecycle](v1-unit7-workspace-lifecycle.md)
