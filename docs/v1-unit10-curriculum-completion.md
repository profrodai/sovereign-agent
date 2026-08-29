# Unit 10: curriculum completion, Chapters 0-7

- **status:** ACCEPTED (Principal acceptance granted at exact head
  `472b26bc1de525542444eaea550f5d7160dfe7b6`; merged into `main` at
  `3c0460b4b48a9b4dd190cdf8ec60bf0aaedc244d`; Sparring's post-merge
  acceptance-record audit filed as
  [PR #40 comment 5465380470](https://github.com/zeroemployeeorg/sovereign-agent/pull/40#issuecomment-5465380470),
  PASS with no findings; this status flip itself lands as a separate,
  Sparring-reviewed change — review before merge, not authored-and-co-signed
  by the same act, not backdated)
- **authority:** principal (ratified acceptance; implementation was
  authorized separately from this SOW's own merge — see the governing SOW's
  "Authorization" section)
- **base:** `main = 7958f74c96f1e51591e631fb62a7c5af017a794f` (Units 0-9
  ACCEPTED; the exact commit the Unit 10 SOW was reviewed and merged at)
- **governing SOW:**
  [`docs/sows/sovereign-agent-v1-unit10-curriculum-completion.md`](sows/sovereign-agent-v1-unit10-curriculum-completion.md)
- **applies_to:** Sovereign Agent 1.x, Unit 10
- **requested_by:** `docs/sows/sovereign-agent-v1-educational-control-plane.md`
  (sequencing amendment 6) and `docs/units-0-6-contract.md`'s curriculum
  cross-cutting section — the governing SOW states the reconciling reading
  of the two explicitly rather than picking one silently (see its own
  "Binding interpretation of the two curriculum authorities" section)

This document follows `docs/v1-unit9-pulse-proactive-work.md`,
`docs/v1-unit8-supervisor-fencing-recovery.md`, and
`docs/v1-unit7-workspace-lifecycle.md`'s own shape: a contract stated as
testable properties, then how to check each one against the repository. It is
**additive** — nothing in the Units 0-9 acceptance record is touched or
revised here.

## What Unit 10 is, in one sentence

Unit 10 creates **zero new production behavior**. It completes the promised
curriculum range (Chapters 4-7, teaching Units 7-9's already-ACCEPTED
production code), builds instructor-note machinery covering the whole
completed range (Chapters 0-7), makes the curriculum's own drift-verification
machinery falsifiable against the new chapters (including a chapter-scoped,
not removed, Pulse-claim guard), and extends the offline Andrea evaluation
with a genuine post-Unit-9 task and scoring key.

## The contract

### Property 1 — four new chapters, each teaching one already-ACCEPTED concept

| Chapter | Directory | Production subject |
| --- | --- | --- |
| 4 | `ch04_work_stays_inside_its_boundary` | Unit 7 workspace policy, confinement, safe paths, reclaim |
| 5 | `ch05_authority_needs_a_fence` | Unit 8 actor leases, execution attempts, stale-worker refusal |
| 6 | `ch06_the_organization_recovers` | Unit 8 supervisor reconciliation and hard-kill recovery |
| 7 | `ch07_the_organization_wakes_itself` | Unit 9 wake gate, genuine Pulse, structured origin, proactive governed work |

Every chapter's `solution.py` imports and executes real, already-ACCEPTED
production code — `src/sovereign_agent/workspace.py`, `fencing.py`,
`supervisor.py`, and `pulse.py` respectively, plus
`src/reference_organizations/store/pulse_gate.py` for Chapter 7. No teaching
fork: `scripts/verify_curriculum.py`'s existing import/no-copy heuristic
(`solution.py` must import `sovereign_agent`/`reference_organizations` at
module top level, must not contain `class Database` or `CREATE TABLE`)
applies unchanged to all four.

Chapter 6's exercise starts a **real** child process and sends it a **real**
`SIGKILL` — the same fixture (`tests/fixtures/hard_kill_worker.py`) and
deterministic polling discipline `tests/test_supervisor.py`'s own hard-kill
proof matrix uses, not a weaker teaching stand-in with a caught exception.
Chapter 5's decisive two-process proof establishes a genuinely live actor
lease from a separate process identity and shows a second, different
assignment for the same actor refused through the unmodified
`run_assignment` path, before its provider is ever invoked.

Chapter 3's README gained a forward link (it was previously the last
chapter, with none). Chapters 4-6 each end with a forward link to the next
chapter; Chapter 7, now the last chapter, ends by naming Unit 11 as where the
book's next chapters will land, without claiming any of them exist yet.
`book/README.md`'s index and "What is not here yet" section were updated to
include Chapters 4-7 and to state, additively, when and why Pulse became
teachable — Chapters 0-3's own prose is unedited beyond that.

### Property 2 — instructor-note machinery, covering the whole completed range

```text
book/INSTRUCTOR.md
book/chNN_<slug>/INSTRUCTOR.md
```

`book/INSTRUCTOR.md` indexes every chapter's own note and states how the
curriculum fits together as one taught course. Every Chapter 0-7
`INSTRUCTOR.md` — including retroactively for the four chapters that existed
before this unit — carries all seven required sections: teaching intent,
prerequisite knowledge, likely misconceptions, observation checkpoints,
discussion prompts, facilitation timing, and exercise debrief/assessment
guidance. No frontmatter, matching every other file in `book/`.

This machinery is wholly new — nothing like it existed anywhere in the tree
before this unit (confirmed at implementation start:
`grep -rni "instructor" book/ docs/ scripts/` returned exactly one hit, in
the governing SOW's own text). The seven-section format and its exact
wording are this unit's own design choice, since no ratified document
specified more than the seven topic names — see "What this unit did not
resolve" below for that boundary stated explicitly.

### Property 3 — the Pulse guard is chapter-scoped, not removed

The pre-Unit-10 guard (`FORBIDDEN_CLAIMS` in `scripts/verify_curriculum.py`)
applied the same two regexes to every chapter regardless of number — global
and chapter-blind, confirmed directly by that gate's own prior source (the
`name` parameter was never referenced inside the forbidden-claims loop).

After this unit:

- **Chapters 0-6 keep the exact unconditional prohibition.** A Pulse-fired
  claim in any of them fails the gate, exactly as before Unit 9 existed.
- **Chapter 7 may claim Pulse fired, but only when its own already-executed
  exercise leaves durable, structured evidence in that exact run's
  database**: a real `pulse.*` event in the append-only `events` table, AND
  a `pulse_origins` row (`origin_kind = 'pulse'`) whose `wake_decision_id`
  resolves to a real `pulse_wake_decisions` row naming a real
  `source_signal_id`. The check (`check_pulse_claims` in
  `scripts/verify_curriculum.py`) runs a fresh `sqlite3` connection against
  the database Chapter 7's own `RUNNABLE` entry point (`check_chapter`
  already calls it as part of the execute-not-merely-import check) produced,
  strictly after that call succeeds — it does not trust the exercise
  script's own printed summary.
- **A claim with no traceable chain fails identically whether Pulse was
  never invoked or its evidence was fabricated** by a direct `append_event`
  call standing in for the real mechanism. Both leave a `pulse.*` event with
  no matching `pulse_origins`/`pulse_wake_decisions` chain (never invoked:
  no event and no chain at all; fabricated: an event with no chain, since
  only `Organization.create_pulse_work`'s single transaction writes the
  matching rows together) — the check does not special-case how the gap
  arose.

### Property 4 — new mechanical checks in `scripts/verify_curriculum.py`

- `REQUIRED_CHAPTERS` extended from 4 to 8 entries, in order; `RUNNABLE`/
  `RUNNABLE_ARGS` extended for the four new chapters.
- `check_instructor_notes`: every required chapter has a co-located
  `INSTRUCTOR.md` with all seven required sections present, plus
  `book/INSTRUCTOR.md` itself — structural only, matching the existing
  `REQUIRED_SECTIONS` pattern applied to a new file.
- `check_chapter_sequence`: previous/next chapter links and `book/README.md`'s
  own index form one coherent sequence — each chapter's forward link points
  at the immediate next required chapter, the last chapter carries none, and
  the index lists every required chapter in order. The pre-Unit-10 gate only
  verified that individual links resolved, never that they chained
  correctly.
- `check_no_frontmatter`: no `book/**/*.md` file begins with a leading `---`
  YAML block — formalizes what `book/CONTENT-SOURCE.md` already stated in
  prose.
- `check_pulse_claims`, chapter-scoped as described in Property 3.
- The pre-existing section, import/no-copy, execute, local-link, and
  script-reference checks are unchanged in shape, now applied to 8 chapters
  instead of 4.

**Deliberately not built**: a mechanical check for additive-only editing of
Chapters 0-3. The governing SOW is explicit that this stays an exact-diff
review requirement, not a brittle heuristic dressed up as proof — see "What
this unit did not do" below.

### Property 5 — the Andrea evaluation carries a genuine post-Unit-9 Task 7

`docs/andrea-alpha-evaluation.md` is preserved exactly as the historical
Units 0-6.5 record: its title, original Task 7, and original scoring key are
untouched. The only edit is one additive link in its existing Unit 9 note,
pointing at the new document now that it exists.

`docs/andrea-chapters-0-7-evaluation.md` is new. It references Tasks 1-6 from
the historical document by number and brief description rather than
duplicating their text, and provides its own complete, replacement Task 7
assessing whether Andrea can explain and **independently verify** genuine
proactive Pulse behavior — reading the `pulse_origins`/`pulse_wake_decisions`
chain back from a fresh `sqlite3` connection, not trusting the exercise
script's own printed summary. This does not authorize or perform the Unit 12
Andrea soak; every task runs entirely offline on the `scripted` provider.

`scripts/evaluate_andrea_chapters_0_7.py` mechanically validates the new
document's offline commands and the underlying production behavior,
following `scripts/evaluate_andrea_alpha.py`'s own shape as a standalone
script. `scripts/evaluate_andrea_alpha.py` itself is unmodified.

## How to check this document against the repository

Every command below was run and confirmed working before being written into
this document.

```bash
# Baseline, still green after Unit 10 lands
uv run --python 3.14 python -m pytest -q
uv run --python 3.14 python scripts/verify_source_budget.py
uv run --python 3.14 python scripts/verify_runtime_dependencies.py
python scripts/verify_curriculum.py   # run twice consecutively

# Property 1 -- Chapter 4-7 exercises each run cleanly, real output
python book/ch04_work_stays_inside_its_boundary/solution.py --root /tmp/unit10-ch04
python book/ch05_authority_needs_a_fence/solution.py --root /tmp/unit10-ch05
python book/ch06_the_organization_recovers/solution.py --root /tmp/unit10-ch06
python book/ch07_the_organization_wakes_itself/solution.py --root /tmp/unit10-ch07

# Property 1 -- the production tests each new chapter's exercise draws from
uv run --python 3.14 python -m pytest -q tests/test_workspace_lifecycle.py -k \
  "reclaimed_after_terminal_state or persistent_policy or temporary_directory_policy or detects_write_outside or do_not_trip_the_boundary or traversal or absolute_deliverable or legitimate_nested"
uv run --python 3.14 python -m pytest -q tests/test_fencing.py -k \
  "acquire_actor_lease_succeeds_with_no_prior_lease or acquire_execution_attempt_succeeds_for_a_fresh_assignment or acquire_execution_attempt_refuses_without_a_live_actor_lease or actor_lease_blocks_a_second_assignment_for_the_same_actor_before_invocation or the_ordinary_run_assignment_path_cannot_bypass_the_actor_lease"
uv run --python 3.14 python -m pytest -q tests/test_supervisor.py -k \
  "sigkilled or recovers_a_real or idempotent or never_guesses_success or workspace_reclaim"
uv run --python 3.14 python -m pytest -q tests/test_pulse.py -k \
  "full_teaching_slice or attribution or does_not_bypass"

# Property 5 -- both Andrea evaluation scripts
python scripts/evaluate_andrea_alpha.py
python scripts/evaluate_andrea_chapters_0_7.py

# Credential absence confirmed -- must be empty, same as every prior unit
env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API" || true

# CLI artifact, from a built wheel outside the source tree
uv run --python 3.14 python -m build --wheel -o /tmp/sovereign-agent-unit10-dist
python3.14 -m venv /tmp/sovereign-agent-unit10-venv
/tmp/sovereign-agent-unit10-venv/bin/pip install \
  /tmp/sovereign-agent-unit10-dist/sovereign_agent-*.whl
/tmp/sovereign-agent-unit10-venv/bin/sovereign-agent --help
/tmp/sovereign-agent-unit10-venv/bin/sovereign-agent doctor
/tmp/sovereign-agent-unit10-venv/bin/sovereign-agent demo store \
  --mode simulated --root /tmp/sovereign-agent-unit10-outside-source
```

## Mutation checking

Every new mechanical guarantee in `scripts/verify_curriculum.py` was
falsified before being reported as done: a plausible break was reproduced, the
gate confirmed it caught the break, the mutation was confirmed to have
actually landed (diff against a pristine copy), then restored to
byte-identical and the gate reconfirmed green.

1. **The chapter-scoped Pulse guard, fabricated evidence.** A `pulse.*`
   event was committed directly via `append_event`, bypassing
   `run_pulse_once` entirely — no matching `pulse_origins`/
   `pulse_wake_decisions` chain existed. `check_pulse_claims` correctly
   refused: "claims Pulse behaviour, and a pulse.* event exists, but no
   traceable pulse_origins -> pulse_wake_decisions chain backs it."
2. **The chapter-scoped Pulse guard, never invoked.** A real sale was
   committed against a fresh organization, but `run_pulse_once` was never
   called — simulating a future edit that quietly dropped the call while a
   Chapter-7-shaped Pulse claim survived. Correctly refused: "claims Pulse
   behaviour, but its own exercise's database has no durable pulse.* event."
3. **The unconditional early-chapter prohibition.** A Pulse-fired sentence
   was appended to `ch00_first_shift/README.md`. The full end-to-end gate
   caught it ("claims Pulse behaviour that does not exist until Chapter 7");
   restored, confirmed byte-identical via `diff`, gate reconfirmed green.
4. **A required `INSTRUCTOR.md` section.** The "Facilitation timing" section
   was removed from `ch02_work_needs_governance/INSTRUCTOR.md`. Caught
   ("INSTRUCTOR.md has no facilitation timing section"); restored, confirmed
   byte-identical, gate reconfirmed green.
5. **A wrong-pointing forward link.** `ch04`'s own "Next:" link was
   retargeted from Chapter 5 to Chapter 7. Caught ("forward link does not
   point at the next chapter (ch05_authority_needs_a_fence)"); restored,
   confirmed byte-identical, gate reconfirmed green.
6. **Injected frontmatter.** A leading `---`/`---` YAML block was prepended
   to `ch01_organization_remembers/README.md`. Caught ("begins with a site
   frontmatter block"); restored, confirmed byte-identical, gate reconfirmed
   green.

`verify_curriculum.py` was run twice consecutively after every restoration
and at final completion; both runs reported
`curriculum sound: 8 chapters, 8 exercises executed, all links resolve`.

## Budget impact

Reproduced by `scripts/verify_source_budget.py`, before and after this
unit's change:

| | modules | nonblank lines | root exports |
| --- | --- | --- | --- |
| Before (Unit 9 accepted) | 27/40 | 6139/6250 | 7/30 |
| After (this unit) | 27/40 | 6139/6250 | 7/30 |

**Unchanged.** `scripts/verify_source_budget.py` scopes only to
`src/sovereign_agent/`; this unit's entire diff lives in `book/`, `docs/`, and
`scripts/verify_curriculum.py` (plus the two new `scripts/evaluate_*` and
`docs/andrea-*` files) — nothing in `src/sovereign_agent/` was touched, as
the governing SOW requires.

## What this unit did not do

- **No new production behavior anywhere.** Every chapter exercise imports
  and runs existing, already-ACCEPTED code from Units 7, 8, and 9. No new
  Pulse, supervisor, service-hosting, fencing, or provider behavior was
  added to `src/sovereign_agent/` or `src/reference_organizations/`.
- **No mechanical check for additive-only Chapters 0-3 editing.** This
  stays an exact-diff review requirement. No heuristic (e.g. "no line was
  deleted") would actually prove the property it claims to — a line can be
  deleted and re-added with different meaning, or left alone while its
  surrounding claim is quietly undermined elsewhere. This is a permanent
  limit, stated here and in `book/CONTENT-SOURCE.md`, not a gap silently
  papered over with a check that cannot verify what it claims.
- **No Chapters 8-12.** No Unit 11 Store expansion, no 30-day pilot start.
- **No Unit 12 release work.** The Andrea soak was not run — it was authored
  and mechanically validated offline, never performed on a person. No
  credentialed provider smokes were run; the 9 deselected `live`-marked
  tests remain unchanged and unrun.
- **No site frontmatter, no publishing pipeline, no claim the book is
  published.** `book/CONTENT-SOURCE.md`'s own commitment (this repository
  builds no site of its own) is unchanged; the new `check_no_frontmatter`
  check formalizes part of that commitment mechanically rather than
  weakening it.
- **No new runtime dependency.** Still exactly `pydantic` plus the standard
  library — `scripts/verify_runtime_dependencies.py` reports `pydantic`
  before and after.
- **No rewriting or weakening of Chapters 0-3.** Their exercises, claims, and
  verification are unchanged in substance; the only edits are additive
  (ch03's forward link, `book/README.md`'s index and "What is not here yet"
  section, the Unit 9 note's additional link in
  `docs/andrea-alpha-evaluation.md`).

## What this unit did not resolve

The exact section wording/format of each `INSTRUCTOR.md` beyond the seven
required topic names was not specified by any ratified document before this
unit — the governing SOW named the seven topics and left the exact prose a
stream's own reasonable, well-justified choice. Content quality (whether a
listed misconception is accurate, whether a timing estimate is realistic) is
explicitly not something `scripts/verify_curriculum.py` can grade, and is not
claimed to be graded anywhere in this unit's own text.

## Explicit non-claims

- No live-provider evidence is claimed anywhere in this document or this
  unit's own tests. `env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API"`
  is empty, same as every prior unit.
- No claim that the Unit 12 Andrea soak has been performed. Its rubric was
  authored and offline-validated only.
- No claim that Chapters 8-12 exist, or that Unit 11's Store expansion has
  begun.
- No claim that the additive-only Chapters 0-3 editing requirement is
  mechanically enforced — it is a review-discipline requirement, stated
  plainly as such.

## Related documents

- [SOW: Sovereign Agent 1.x — Unit 10 curriculum completion, Chapters 0-7](sows/sovereign-agent-v1-unit10-curriculum-completion.md)
- [Unit 9: Pulse and proactive governed work](v1-unit9-pulse-proactive-work.md)
- [Unit 8: supervisor, fencing, and hard-kill recovery](v1-unit8-supervisor-fencing-recovery.md)
- [Unit 7: workspace lifecycle](v1-unit7-workspace-lifecycle.md)
- [Units 0-6 contract](units-0-6-contract.md)
- [Andrea Alpha evaluation (Units 0-6.5, historical)](andrea-alpha-evaluation.md)
- [Andrea Chapters 0-7 evaluation (post-Unit-9)](andrea-chapters-0-7-evaluation.md)
