# SOW: Sovereign Agent 1.x — Unit 10 curriculum completion, Chapters 0-7

```yaml
sow: sovereign-agent-v1-unit10-curriculum-completion
project: sovereign-agent
unit: 10
status: PROPOSED
authority: principal
base_commit: e6ce2bd3b3ec266a64c7705b4d55f587eee44730
governing_documents:
  - docs/sows/sovereign-agent-v1-educational-control-plane.md (sequencing amendment 6)
  - docs/units-0-6-contract.md (curriculum cross-cutting section)
work_branch: unit-10/curriculum-completion
runtime: Python 3.14
runtime_dependencies:
  - pydantic
```

## Authorization

This SOW is the Principal's implementation direction for Unit 10, incorporating the
Principal's rulings on the seven open questions the read-only scope descent surfaced
(`.unit10/SCOPE-DESCENT.md`, untracked staging evidence, superseded by this SOW as
the citable authority).

**Filing and reviewing this SOW does not, by itself, authorize implementation.** The
Principal's authorization for Unit 10 was explicitly narrower than prior units:
read-only scope descent and SOW preparation only, with implementation requiring a
*separate* Principal decision after this SOW is merged and verified — not something
this document, or its own merge, may grant itself.

The sequence is:

1. File this SOW in the repository, route it through Sparring review, and merge the
   reviewed text into `main`. Merging establishes the reviewed implementation
   contract; it does not start implementation.
2. Gate merged `main` from a clean clone, confirming the merge introduced no drift
   from the reviewed head.
3. Master requests explicit Principal authorization, bound to the exact merged SOW
   commit, before opening any implementation branch or spawning any stream work.
4. Only on that separate authorization does implementation begin, from the resulting
   exact merged commit — not from the drafting branch and not from `e6ce2bd3` if
   `main` has advanced past this SOW's own merge.

A changed SOW head invalidates an earlier co-sign. Branch reconciliation must use an
allowed, auditable PR-based mechanism; do not substitute a local history rewrite for
the denied `git rebase`, `git merge`, or force-push mechanisms.

## Mission

Complete the promised curriculum range and make Chapters 0-7 one coherent course:

1. Create Chapters 4-7, each teaching one pedagogical concept grounded in real,
   ACCEPTED production behavior from Units 7-9.
2. Establish instructor-note machinery, co-located per chapter and indexed at the
   book level.
3. Make the curriculum's own drift-verification machinery falsifiable against the
   new chapters, including a chapter-scoped (not removed) Pulse-claim guard.
4. Leave Chapters 0-3 historically truthful, edited only additively.
5. Extend the offline Andrea evaluation with a genuine post-Unit-9 task and scoring
   key.

Unit 10 does not create new production behavior. Every chapter exercise imports and
runs existing, already-ACCEPTED code from Units 7, 8, and 9 — it does not invent new
Pulse, supervisor, service-hosting, fencing, or provider behavior merely to make the
curriculum easier to teach.

## Binding interpretation of the two curriculum authorities (Question 5, resolved)

`docs/sows/sovereign-agent-v1-educational-control-plane.md:62-68` (amendment 6) says
Unit 10 "completes... Chapters 0-7." `docs/units-0-6-contract.md:97-100` says Unit 10
"expands, reorganises and polishes Chapters 0-7; it is not where the book first
becomes runnable."

These are compatible, and this SOW states the reconciling reading explicitly rather
than silently picking one, per the A-U8-1 discipline this project already holds
itself to:

- "Completes Chapters 0-7" means Unit 10 completes the promised curriculum range by
  creating Chapters 4-7 and making Chapters 0-7 coherent as one course.
- "Expands, reorganises and polishes" means the book was already runnable before
  Unit 10 (Chapters 0-3 already execute against real production code). Unit 10 does
  not retroactively become the book's beginning.

Consequence: Chapters 0-3 retain their existing behavior and historically truthful
claims. Their edits are additive editorial improvements only — better navigation,
transitions, terminology, forward references. Unit 10 may NOT replace their
exercises or rewrite history as though Pulse existed during their original scope.

## Required implementation

### 1. Four new chapters — one pedagogical concept each (Questions 1-2, resolved)

The four chapters represent four pedagogical concepts, not one chapter per
implementation unit. Unit 8 is split because fencing and recovery are distinct
ideas. Pulse receives exactly one chapter, teaching both its mechanism and its
end-to-end consequence together — do not split Pulse into separate teaching forks.

| Chapter | Directory | Production subject |
| --- | --- | --- |
| 4 | `ch04_work_stays_inside_its_boundary` | Unit 7 workspace policy, confinement, safe paths, reclaim |
| 5 | `ch05_authority_needs_a_fence` | Unit 8 actor leases, execution attempts, stale-worker refusal |
| 6 | `ch06_the_organization_recovers` | Unit 8 supervisor reconciliation and hard-kill recovery |
| 7 | `ch07_the_organization_wakes_itself` | Unit 9 wake gate, genuine Pulse, structured origin, proactive governed work |

Each new chapter must match `book/CONTENT-SOURCE.md`'s existing contract exactly:
a `chNN_<slug>/` directory containing `README.md` and `solution.py`. `README.md`
carries, in order: `## Learning objective`, an exercise section (`## The exercise`
or `## Exercise N`), expected observations with real command output,
`## Learner verification command`, `## Explain it back`. `solution.py` imports the
production package (`from sovereign_agent...` or `from reference_organizations...`
at module top level) rather than copying implementation — it must not contain
`class Database` or `CREATE TABLE`, matching the exact heuristic
`scripts/verify_curriculum.py:97` already enforces for Chapters 0-3.

Each chapter's exercise must import and run production code with a real,
exercise-able entry point already proven by this project's own test suites — no
teaching forks:

- **Chapter 4** (workspace lifecycle): `src/sovereign_agent/workspace.py`'s
  `safe_join`, `snapshot_boundary`, `diff_boundary`, `reclaim_workspace`.
  Exercise-able precedent: `tests/test_workspace_lifecycle.py` (1187 lines),
  cited with exact `-k` selectors at
  `docs/v1-unit7-workspace-lifecycle.md:513,521,526`.
- **Chapter 5** (fencing): `src/sovereign_agent/fencing.py`'s
  `acquire_actor_lease`, `acquire_execution_attempt`, and the stale-worker refusal
  path exercised by `organization.run_assignment`'s fence check. Exercise-able
  precedent: `tests/test_fencing.py` (752 lines).
- **Chapter 6** (supervisor recovery): `src/sovereign_agent/supervisor.py`'s
  `tick`/`run` — the CLI's `sovereign-agent supervisor --once` entry point
  (`src/sovereign_agent/cli.py:352-357`). Exercise-able precedent:
  `tests/test_supervisor.py` (346 lines), including the real-SIGKILL and
  real-SIGINT proof matrix cited at
  `docs/v1-unit8-supervisor-fencing-recovery.md:387-401`.
- **Chapter 7** (Pulse): `src/sovereign_agent/pulse.py`'s `run_pulse_once` — the
  CLI's `sovereign-agent pulse --once` entry point
  (`src/sovereign_agent/cli.py:215-234`) — combined with
  `src/reference_organizations/store/pulse_gate.py`'s `store_wake_gate`.
  `run_pulse_once` is already deterministic, single-pass, no sleeping/timing
  dependency (`src/sovereign_agent/pulse.py:15-27`), matching
  `supervisor --once`'s own established teaching-safe design. Exercise-able
  precedent: `tests/test_pulse.py` (1091 lines); the reference Store Pulse
  scenario already exists (`run_pulse_simulated`,
  `src/reference_organizations/store/demo.py`), reachable directly per
  `docs/v1-unit9-pulse-proactive-work.md:479`.

Chapter 3's own README currently has no forward link (it is presently the last
chapter). Add one, matching the existing pattern (`book/ch00_first_shift/
README.md:165`, `book/ch01_organization_remembers/README.md:209`,
`book/ch02_work_needs_governance/README.md:285`). Each new chapter must end with
its own forward link, chaining 4→5→6→7. Chapter 7, being currently the last, needs
no forward link but should close the sequence coherently (e.g. a return to
`book/README.md`'s index or a forward gesture to Unit 11's own future chapters,
matching the existing precedent at `book/ch03_actor_is_not_a_model/README.md:89`
of naming a not-yet-written future unit by number).

Vocabulary introduced in Chapters 0-3 (Outcome/SOW/Assignment/Actor, per
`book/ch02_work_needs_governance/README.md:14-25`) must extend consistently — new
terms (actor lease, execution attempt, wake decision, Pulse origin) are introduced
once, in the chapter that first needs them, and reused verbatim afterward, not
re-defined differently in a later chapter.

### 2. Instructor-note machinery (Question 3, resolved)

Co-located notes, indexed at the book level:

```text
book/INSTRUCTOR.md
book/chNN_<slug>/INSTRUCTOR.md
```

`book/INSTRUCTOR.md` defines how to teach the curriculum and indexes every
chapter's own instructor note. Every Chapter 0-7 `INSTRUCTOR.md` — including
retroactively for the four existing chapters, since the machinery must cover the
whole completed range, not just the four new ones — must contain:

- teaching intent
- prerequisite knowledge
- likely misconceptions
- observation checkpoints
- discussion prompts
- facilitation timing
- exercise debrief and assessment guidance

Instructor notes carry no site frontmatter — the same renderer-agnostic constraint
that already governs every chapter `README.md` (see below). `book/CONTENT-SOURCE.md`
must be updated to document this source contract for instructor notes, following
its own existing pattern (the file/contract table at
`book/CONTENT-SOURCE.md:21-26`).

### 3. The Pulse guard becomes chapter-scoped, not removed (Question 4, resolved)

The exact current guard, `scripts/verify_curriculum.py:62-66`
(`FORBIDDEN_CLAIMS`), is global and chapter-blind — confirmed directly: the `name`
parameter passed into `check_chapter` is never referenced inside that loop. It
rejects truthful Chapter-7-shaped prose about real, ACCEPTED Pulse behavior
(independently reproduced: "the organization wakes itself up today by running
pulse --once" and "the pulse fired a wake decision" both trip it) and is also
narrow/brittle by verb form (a differently-phrased but equally true claim evades
it).

Required behavior after this unit:

- Chapters 0-6 remain prohibited from claiming that Pulse fired or woke the
  organization — the guard's existing prohibition stays in force for these
  chapters exactly as written today.
- Chapter 7 may make those claims ONLY because its runnable exercise invokes the
  genuine production Pulse mechanism (`run_pulse_once`/`pulse --once`), not
  because it is chapter 7 by number alone.
- Chapter 7's executed result must leave a real `pulse.work_created` event and
  structured origin linkage (`pulse_origins`, `pulse_wake_decisions`) in the
  ledger — the verifier must check for this durable evidence, not merely permit
  the prose.
- A manually created assignment, a pre-seeded event, a fabricated return value, or
  a prose-only claim does NOT satisfy the guard, in any chapter, including
  Chapter 7. The property that must remain global and absolute regardless of
  chapter number is: no chapter may fabricate or simulate Pulse behavior it does
  not actually produce via the real mechanism.

The verifier must fail when:

- a Pulse claim is introduced into Chapters 0-6 (the existing prohibition,
  preserved);
- Chapter 7 stops invoking production Pulse (the claim survives but the
  mechanism backing it is removed);
- Chapter 7's durable Pulse event or structured attribution is absent (the
  mechanism runs but leaves no evidence, or the wrong evidence);
- simulated evidence replaces the genuine mechanism (e.g. a test double,
  a hardcoded ledger row, or a fabricated `pulse.*` event inserted directly rather
  than produced by `run_pulse_once`).

Do not simply widen the existing regex or add a chapter-number exemption without
also verifying the durable ledger evidence — a wording-only fix would let Chapter 7
claim Pulse fired without ever actually running it, reintroducing exactly the
defect class this guard exists to prevent.

### 4. Mechanical enforcement (Question 6, resolved — mixed approach)

Extend `scripts/verify_curriculum.py` to mechanically enforce:

- Chapters 0-7 exist and appear in exact sequence (`REQUIRED_CHAPTERS` extended
  from 4 to 8 entries, in order).
- Every chapter has a co-located `INSTRUCTOR.md` with all seven required sections
  present (teaching intent, prerequisite knowledge, misconceptions, observation
  checkpoints, discussion prompts, facilitation timing, debrief/assessment
  guidance) — a structural check, matching the existing `REQUIRED_SECTIONS`
  pattern (`scripts/verify_curriculum.py:54-60`) applied to a new file.
- Every exercise imports and executes production code (already-proven mechanism,
  `scripts/verify_curriculum.py:95-129`, extended to the 4 new chapters via new
  `RUNNABLE`/`RUNNABLE_ARGS` entries).
- Previous/next chapter links and the book index (`book/README.md`) form one
  coherent sequence — a new check, since the current `check_chapter:132-136`
  verifies individual link resolution but not sequential chaining.
- No source Markdown begins with site frontmatter — a new check (a leading `---`
  block at the top of any `book/**/*.md` file fails the gate), formalizing the
  constraint `book/CONTENT-SOURCE.md:65-69` already states in prose but nothing
  currently verifies mechanically.
- The chapter-scoped Pulse guarantees above (§3), including the durable-evidence
  check, not merely the prose-pattern check.
- The existing section, script-reference, and local-link checks, unchanged and
  extended to cover 8 chapters instead of 4.

Keep additive-only treatment of Chapters 0-3 as an exact-diff review requirement,
not a mechanical check. Do not build a brittle heuristic (e.g. "no line was
deleted") and present it as proof of additive-only editing — that would be exactly
the kind of overclaimed-check-vs-actual-property gap this project's own review
discipline exists to catch. State this limitation plainly in the Unit 10
documentation deliverable rather than papering over it with a check that cannot
actually verify the property it claims to.

Every new mechanical guarantee requires a mutation check before this unit is
reported complete: for each new `scripts/verify_curriculum.py` check, demonstrate
a plausible break (e.g. a chapter fabricating a Pulse event; an `INSTRUCTOR.md`
missing a required section; a chapter's forward link pointing at the wrong
chapter; a `README.md` with injected frontmatter) that the new check catches,
confirm the mutation actually landed (diff-stat), then restore and confirm green.

### 5. Andrea evaluation extension (Question 7, resolved)

The post-Unit-9 evaluation task belongs to Unit 10, not left unassigned — closing
the gap that `docs/andrea-alpha-evaluation.md`'s own A-U9-2 note named: "A future
evaluation covering post-Unit-9 curriculum will need its own task 7 and its own
scoring key" (`docs/andrea-alpha-evaluation.md:169-170`).

**A new task must not be added to `docs/andrea-alpha-evaluation.md` itself.** That
document's own title — "Andrea Alpha evaluation (Units 0–6.5)" — is a historical
scope statement; adding a post-Unit-9 task to it while leaving that title unedited
would make the file internally contradictory, claiming one scope while containing
an evaluation task from a later one.

Required instead:

- **`docs/andrea-alpha-evaluation.md` is preserved exactly as the historical
  Units 0–6.5 evaluation**, including its original Task 7 and scoring key
  (`docs/andrea-alpha-evaluation.md:152-160`), untouched. That document's own
  title correctly scopes it, and a session run against that curriculum state
  still correctly used the original criterion — it is not edited, not
  superseded, not deprecated.
- **Create `docs/andrea-chapters-0-7-evaluation.md`** for the post-Unit-9
  evaluation. It may reference Tasks 1-6 from the historical document rather than
  duplicating them, but must provide its own complete, replacement Task 7 and its
  own complete scoring instructions — assessing whether Andrea can explain and
  verify genuine proactive Pulse behavior after completing Chapter 7.
- **Add an additive link** from the historical document's existing Unit 9 note
  (`docs/andrea-alpha-evaluation.md:161-172`, the note added by the A-U9-2 fix) to
  the new evaluation document — following the same additive-historical pattern
  this project already established for exactly this file, extended one step
  further: not just noting that a future evaluation is needed, but pointing at it
  once it exists.
- **Mechanically validate** the new document's Task 7 offline commands and the
  production behavior underlying them, matching how
  `scripts/evaluate_andrea_alpha.py` already validates the machine-checkable
  parts of the historical document's six tasks — either by extending that script
  to cover the new document, or by an equivalent new script; do not add an
  untested rubric.

This does NOT authorize the Unit 12 Andrea soak. The boundary is exact: Unit 10
authors and mechanically validates the new offline task and rubric; Unit 12
performs the timed, human, Andrea-profile soak and release evaluation using it. No
credentialed provider execution is introduced in Unit 10 — the new task, like
every existing one, runs entirely offline on the `scripted` provider.

## Explicit non-scope

Do not:

- create Chapters 8-12;
- perform any Unit 11 Store expansion or begin the 30-day pilot;
- perform any Unit 12 release work, run the Andrea-profile soak itself, or run
  credentialed provider smokes;
- add new Pulse, supervisor, service-hosting, fencing, or provider behavior to
  `src/sovereign_agent/` or `src/reference_organizations/` merely to make the
  curriculum easier to teach — every chapter exercise must import and run
  EXISTING, already-ACCEPTED production code;
- rewrite or weaken any existing Chapters 0-3 exercise, claim, or verification
  beyond additive editorial improvement;
- introduce site frontmatter, a publishing pipeline, or any claim that the
  downstream site has published the book (`book/CONTENT-SOURCE.md`'s explicit
  commitment: this repository builds no site of its own);
- change the runtime dependency surface beyond Pydantic plus stdlib.

The nine credentialed provider tests remain deselected and explicitly deferred to
Unit 12.

## Budget

`scripts/verify_source_budget.py` scopes only to `src/sovereign_agent/` (confirmed:
`PACKAGE = ROOT / "src" / "sovereign_agent"`, `scripts/verify_source_budget.py:10`).
Unit 10 is curriculum, documentation, and `scripts/verify_curriculum.py`
extension work — none of it lives inside `src/sovereign_agent/`, so this unit is
not expected to touch that budget at all. Confirm this explicitly in the gate
(the budget script's own output must be unchanged from the Unit 9 baseline:
`27/40 modules, 6139/6250 lines, 7/30 exports`). If any change to
`src/sovereign_agent/` proves necessary, stop and request a ruling — this SOW does
not authorize new production code.

## Gate

Run at the exact implementation head:

```bash
uv lock --check
make verify
python scripts/verify_curriculum.py
python scripts/verify_source_budget.py   # must be unchanged from Unit 9 baseline
git diff --check
```

Also build and install the wheel into a clean Python 3.14 environment outside the
source tree, then run:

```bash
sovereign-agent --help
sovereign-agent doctor
sovereign-agent demo store --mode simulated --root /tmp/sovereign-agent-unit10
```

Run the extended `verify_curriculum.py` twice consecutively. Run each new chapter's
`solution.py` exercise directly, confirming it executes cleanly against a fresh
organization root, matching the discipline `scripts/verify_curriculum.py:100-129`
already applies. Live-provider tests remain deselected and must be reported as
unrun.

## Review and merge ritual

This ritual governs the implementation PR, which may only begin after the separate
Principal authorization required by the "Authorization" section above — not
immediately on this SOW's own merge.

1. Stream implements on `unit-10/curriculum-completion`; it does not open or merge
   its own PR.
2. Master independently reads the new chapters, runs each exercise directly, and
   reproduces the mutation checks for every new mechanical guarantee (§4).
3. Master independently mutation-checks at least:
   - a fabricated `pulse.*` event inserted directly into Chapter 7's exercise
     (bypassing `run_pulse_once`) — the chapter-scoped guard must still catch this;
   - a Pulse claim introduced into a pre-Chapter-7 chapter's prose — the
     unconditional prohibition must still catch this;
   - a missing required section in a new `INSTRUCTOR.md` — the new structural
     check must catch this;
   - injected frontmatter into a chapter `README.md` — the new frontmatter check
     must catch this.
4. Master opens the PR and names its exact head.
5. Sparring reviews that exact head against this SOW and the Principal's seven
   resolved questions above.
6. No merge over `CHANGES_REQUESTED`.
7. Principal acceptance is requested explicitly after Sparring co-signs.
8. Merge only through the allowed GitHub PR mechanism.
9. Gate merged `main` from a clean clone.
10. Audit `docs/v1-unit10-curriculum-completion.md` (the documentation deliverable
    this unit adds, following the established `docs/v1-unitN-...md` shape) against
    merged behavior.
11. Flip its status to `ACCEPTED` only in a separate, reviewed change.
12. Unit 11 remains unstarted until that closure lands.

If `main` advances, reconcile through an auditable PR-based path and rerun gates
and review on the resulting exact head. A prior co-sign does not survive a head
change.

## Documentation deliverables

Add `docs/v1-unit10-curriculum-completion.md`, following the shape established by
`docs/v1-unit7-workspace-lifecycle.md`, `docs/v1-unit8-supervisor-fencing-recovery.md`,
and `docs/v1-unit9-pulse-proactive-work.md`: status header block (status `PROPOSED`
until a separate reviewed acceptance flip), the contract as testable properties, a
verified "how to check this document against the repository" command block (every
command run and confirmed working before it is written into the doc — this project
has now caught a broken check-command in review multiple times; do not be the
next), a budget-impact statement (expected: unchanged, per the Budget section
above), a "what this unit did not do" section, and explicit non-claims (no
credentialed provider evidence, no Chapters 8-12, no Unit 11/12 work).

Update `CHANGELOG.md` following the established per-unit style. Update
`book/CONTENT-SOURCE.md` to document the instructor-note contract and the new
mechanical guarantees (§4). Update `book/README.md`'s chapter index to include
Chapters 4-7.

## Acceptance conditions

Unit 10 is accepted only when the Principal can inspect the merged tree and
confirm:

- Chapters 0-7 all exist, execute, and chain coherently;
- every new chapter's exercise imports and runs real production code with no
  teaching fork;
- Chapter 7 genuinely invokes Pulse and leaves durable, structured ledger
  evidence — never a fabricated claim;
- Chapters 0-6 remain unable to claim Pulse fired, mechanically enforced;
- Chapters 0-3 are unchanged in substance, only additively edited;
- instructor notes exist for all eight chapters with every required section;
- the new mechanical checks are demonstrably load-bearing (mutation-checked, not
  merely present);
- the Andrea evaluation carries a genuine, working post-Unit-9 task and scoring
  key, without claiming or performing the Unit 12 soak;
- the source remains renderer-agnostic, with no frontmatter or publishing claim
  anywhere;
- the `src/sovereign_agent/` budget is unchanged;
- no live-provider evidence is claimed.

Proceed first by filing and reviewing this SOW. Do not begin implementation before
it is merged unchanged or a subsequent Principal ruling amends it.

## Related documents

- [Sovereign Agent 1.0 — executable textbook (design memo)](sovereign-agent-v1-educational-control-plane.md)
- [Unit 9 SOW: Pulse and proactive governed work](sovereign-agent-v1-unit9-pulse-proactive-work.md)
- [Unit 9: Pulse and proactive governed work](../v1-unit9-pulse-proactive-work.md)
- [Unit 8: supervisor, fencing, and hard-kill recovery](../v1-unit8-supervisor-fencing-recovery.md)
- [Unit 7: workspace lifecycle](../v1-unit7-workspace-lifecycle.md)
- [Units 0-6 contract](../units-0-6-contract.md)
