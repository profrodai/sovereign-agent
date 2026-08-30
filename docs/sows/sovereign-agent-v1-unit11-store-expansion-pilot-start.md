# SOW: Sovereign Agent 1.x — Unit 11 Store expansion, Chapters 8-12, pilot-start mechanism

```yaml
sow: sovereign-agent-v1-unit11-store-expansion-pilot-start
project: sovereign-agent
unit: 11
status: PROPOSED
authority: principal
base_commit: e9a067087b8cd09f33d046b9402f4c0976167c5e
governing_documents:
  - docs/sows/sovereign-agent-v1-educational-control-plane.md (sequencing amendment 6)
  - docs/rulings/2026-08-30-unit11-scope.md (Unit 11 scope ruling, all six holdings binding)
work_branch: unit-11/store-expansion-pilot-start
runtime: Python 3.14
runtime_dependencies:
  - pydantic
```

## Authorization

This SOW is the Principal's implementation direction for Unit 11, incorporating the
Principal's Unit 11 scope ruling (`docs/rulings/2026-08-30-unit11-scope.md`) in full.

**Filing and reviewing this SOW does not, by itself, authorize implementation** —
the same boundary Unit 10's own SOW had to state explicitly after an earlier
correction, restated here from the start rather than discovered by review. Merging
this SOW establishes the reviewed implementation contract; it does not start
implementation.

The sequence is:

1. File this SOW in the repository, route it through Sparring review, and merge the
   reviewed text into `main`. Merging establishes the contract; it does not start
   implementation.
2. Gate merged `main` from a clean clone, confirming the merge introduced no drift
   from the reviewed head.
3. Master requests explicit Principal authorization, bound to the exact merged SOW
   commit, before opening any implementation branch or spawning any stream work.
4. Only on that separate authorization does implementation begin, from the
   resulting exact merged commit — not from the drafting branch and not from
   `e9a06708` if `main` has advanced past this SOW's own merge.

**A second, independent authorization gate governs the real pilot-start act
specifically** (Holding 1 of the governing ruling): even after Unit 11's
implementation is itself accepted and verified on clean `main`, the real pilot-start
act against the named pilot organization requires its own separate Principal
authorization, distinct from and later than implementation authorization. **Unit 11
acceptance does not mean the 30-day pilot has finished** — it does not even mean the
pilot has started; only the separately-authorized real pilot-start act, and its
durable governance receipt, mean that.

A changed SOW head invalidates an earlier co-sign. Branch reconciliation must use an
allowed, auditable PR-based mechanism; do not substitute a local history rewrite for
the denied `git rebase`, `git merge`, or force-push mechanisms.

## Mission

Close the three components the governing ruling authorized:

1. Expand the Store's single-SKU walking skeleton into a small multi-product
   catalog, proving the existing `inventory.changed -> wake gate -> Pulse ->
   replenishment` pipeline generalizes without inventing new signal kinds, effect
   kinds, or core organizational primitives.
2. Land Chapters 8-12, teaching that expansion and the pilot-start mechanism, each
   importing and executing real production code.
3. Build the pilot-start mechanism itself — an atomic, idempotent, structured
   ledger act — without executing it against the real named pilot organization.
   Executing it is a separate, later, separately-authorized act, not part of this
   unit's own acceptance.

Unit 11 does not perform the real pilot start, does not run credentialed provider
smokes, does not conduct the Andrea live evaluation, does not claim pilot
completion or proof-pack acceptance, and does not release. All of that remains
Unit 12's, per the governing ruling's Holding 4 and the boundary collected in that
ruling's own grounding.

**Terminology**, per the governing ruling's Holding 5, binding on this SOW and its
own deliverables, not merely a note for future work: this document and everything
it produces uses **"30-day Store pilot"** for the operational production run this
unit's mechanism starts, **"Andrea live evaluation"** when referring to Unit 12's
own future timed human learner session (never "soak" unqualified), and, if the
unrelated v0.6-era concept needs mentioning at all, **"v0.6 infrastructure soak"**
by its full name. Historical `docs/v0.6-soak.md` and `site/v0.6-soak/` remain
untouched by this unit.

## Required implementation

### 1. Multi-SKU Store catalog (governing ruling Holding 2)

Expand `src/reference_organizations/store/__init__.py`'s `seed()` (currently
`:59-76`, hardcoding exactly one `Product(sku="SKU-TEA", ...)`) into a small
catalog of at least two distinct SKUs, each with independent stock levels and
reorder points, and independent supplier/replenishment routing where the existing
model already permits it.

Minimum accepted behavior, verbatim from the governing ruling:

- At least two distinct SKUs.
- Independent stock levels and reorder points.
- Independent supplier/replenishment routing where the existing model permits it.
- A sale or inventory change for one SKU cannot wake or replenish another.
- Multiple qualifying SKUs can each create one canonical governed replenishment
  chain.
- Replay, restart, and concurrency preserve per-SKU idempotency.
- The existing `inventory.changed -> wake gate -> Pulse -> replenishment`
  vocabulary remains intact.

**Do not add new signal kinds, effect kinds, governance concepts, or core
organizational primitives merely to make the expansion appear larger.** The point
is proving the accepted pipeline generalizes, not inventing new production
surfaces. If a design choice would require touching `src/sovereign_agent/` core
primitives beyond what multi-SKU support genuinely requires, stop and report — that
is a stop condition, not a judgment call to make silently.

### 2. Multi-SKU isolation matrix — binding acceptance requirement

This is not a nice-to-have; the governing ruling and the Principal's authorization
of this SOW both name it as a binding acceptance requirement. Prove, with real
tests, not prose:

- **Sales isolation**: a sale of SKU A does not create, touch, or influence any
  signal, wake decision, Pulse origin, assignment, or replenishment effect for SKU
  B.
- **Signal isolation**: `record_sale`'s signal-per-occurrence discipline (Unit 9's
  own fix, `src/reference_organizations/store/__init__.py`'s `dedupe_key`
  suffixing) extends correctly to multiple SKUs — no signal for SKU A can be
  conflated with, replace, or be replaced by a signal for SKU B.
- **Wake-decision isolation**: the Store's wake gate (`store_wake_gate`,
  `src/reference_organizations/store/pulse_gate.py`) correctly maps each qualifying
  signal to exactly the one outcome for its own SKU — never a different SKU's
  outcome, never an ambiguous match across SKUs.
- **Pulse-origin isolation**: the `pulse_wake_decisions`/`pulse_origins` structured
  attribution chain (established in Unit 9, `docs/v1-unit9-pulse-proactive-work.md`)
  correctly distinguishes concurrent or sequential decisions for different SKUs —
  each decision's `source_signal_id` traces back to the correct SKU's own signal,
  never conflated.
- **Assignment and replenishment isolation**: multiple qualifying SKUs, evaluated
  in the same or different `run_pulse_once` passes, each produce their own
  canonical governed replenishment chain (SOW, assignment, receipt) — never a
  shared or cross-attributed chain.
- **Replay, restart, and concurrency**: per-SKU idempotency survives all three,
  matching the same class of proof F-U9-1 required for the single-SKU case,
  extended to confirm no cross-SKU duplication or contamination under concurrent
  multi-SKU qualification. Use the project's own established real-two-connection
  test discipline (`tests/test_pulse.py`'s existing concurrency tests are the
  precedent to extend, not fork).

A concurrent race MUST be proven with real, separate database connections — the
same discipline every prior unit's own proof matrix has required (Unit 8's
fencing tests, Unit 9's Pulse tests). A pair of mocks calling one shared helper
does not prove the SQLite-boundary property this matrix requires.

### 3. Chapters 8-12 (governing ruling Holding 3, exact chapter map)

| Chapter | Directory | Teaching responsibility |
| --- | --- | --- |
| 8 | `ch08_the_store_becomes_a_catalog` | Replace the single-product fixture with a genuine multi-product catalog. |
| 9 | `ch09_each_product_has_its_own_threshold` | Independent stock state and reorder decisions per SKU. |
| 10 | `ch10_one_signal_wakes_one_need` | Signal-to-SKU binding; no cross-product wake or replenishment. |
| 11 | `ch11_replenishment_scales_without_losing_governance` | Multiple governed replenishment chains while preserving idempotency, evidence, and fencing. |
| 12 | `ch12_the_pilot_begins_with_a_receipt` | Execute and inspect the pilot-start mechanism while distinguishing "started" from "finished." |

Each chapter must match `book/CONTENT-SOURCE.md`'s existing contract exactly (as
extended by Unit 10): a `chNN_<slug>/` directory containing `README.md`,
`solution.py`, and `INSTRUCTOR.md`. `README.md` carries, in order: `## Learning
objective`, an exercise section, expected observations with real command output,
`## Learner verification command`, `## Explain it back`. `solution.py` must import
the production package at module top level and must not copy implementation
(`class Database`/`CREATE TABLE` forbidden, matching
`scripts/verify_curriculum.py:138`'s existing heuristic). `INSTRUCTOR.md` must carry
all seven sections Unit 10 established: teaching intent, prerequisite knowledge,
likely misconceptions, observation checkpoints, discussion prompts, facilitation
timing, exercise debrief and assessment guidance.

Each chapter's exercise must import and run production code with a real,
exercise-able entry point — no teaching forks. Chapter 12 specifically **must not
accidentally start the real 30-day pilot during the curriculum gate or any test
run**: its exercise must operate against an exercise-scoped, disposable pilot
identity, structurally distinct from the real named pilot organization the
separately-authorized pilot-start act (§4 below) targets — never the same database,
never the same pilot identity value, never reachable by accident through a shared
default.

Chapter 7's existing closing gesture (`book/ch07_the_organization_wakes_itself/
README.md`'s final lines, "There is no Chapter 8 yet — Unit 11 is where the
Store's own governed territory expands...") must be updated with a forward link to
Chapter 8, matching the established forward-chaining pattern (each non-last chapter
ends with a `Next:` link to the immediate next chapter). Chapters 8-11 each need
their own forward link; Chapter 12, now the last chapter, needs none but should
close coherently.

### 4. The pilot-start mechanism (governing ruling Holding 1) — built, never executed against the real pilot organization by this unit

Build an explicit, durable pilot-start act producing, atomically, in one
transaction:

- A first-class, queryable SQLite record — not an inference from prose or
  arbitrary JSON, matching the same discipline the Unit 9 ruling already required
  for Pulse attribution (structured columns, not unindexed JSON).
- An append-only `pilot.started` event (or equivalently explicit event kind — name
  it once, use it consistently, matching Unit 8's own "one canonical failure-
  category term" discipline).
- A stable pilot identity.
- A canonical UTC start time.
- The Store organization and pilot-profile identity.
- A reference to the evidence namespace where Unit 12 can later assemble the
  redacted proof pack.

Required behavior, proven with real tests:

- **Idempotent**: replaying the same start request cannot create another pilot —
  the same CAS/UNIQUE-constraint discipline this project has used throughout
  (`relay.claim()`, `fencing.acquire_actor_lease()`, `create_pulse_work()`'s own
  `UNIQUE(source_signal_id)`), not a preflight `SELECT`.
- **Refuses when an incompatible pilot is already active** — a second, different
  pilot-start attempt while one is live must fail closed, not silently proceed or
  silently no-op as if it were a legitimate replay.
- **Terminal persistence is atomic**: the SQLite record, the `pilot.started` event,
  and the governance receipt (see below) commit together or not at all.
- **Concurrent start attempts produce exactly one canonical pilot, proven with real,
  separate database connections** — two processes racing to start the same pilot
  identity at the same moment is a distinct property from idempotent replay and
  must be tested separately: one wins, the other either observes the winner's
  identical identity (a legitimate concurrent replay) or is refused (a genuinely
  incompatible concurrent start), never both creating their own record. Same
  real-two-connection discipline as §2's multi-SKU concurrency proofs — no mocks
  standing in for the SQLite boundary.

**This unit builds the mechanism and proves it with tests. It does not invoke it
against the real named pilot organization.** Chapter 12's own exercise (§3) invokes
it only against a disposable, exercise-scoped identity. The real pilot-start act
requires the separate Principal authorization named in "Authorization" above and
in the governing ruling's Holding 1 — that authorization, and the act it
authorizes, are both explicitly out of this SOW's own acceptance scope.

A short, append-only governance receipt (a durable record, matching the pattern
this project's own acceptance records already use) must cite the real marker's
identity and timestamp without pretending the pilot has finished — the receipt
proves a start happened, never a completion.

### 5. Mechanical curriculum guarantees and mutation checks

Extend `scripts/verify_curriculum.py`'s `REQUIRED_CHAPTERS`/`RUNNABLE`/
`RUNNABLE_ARGS` from 8 to 13 entries, following the exact pattern Unit 10 already
established growing from 4 to 8 — nothing in the current structure assumes exactly
8 chapters.

Every existing mechanical guarantee (chapter-scoped Pulse guard, instructor-note
structure, chapter-sequence coherence, frontmatter absence, import-not-copy,
execute-not-merely-import) must continue to apply to all 13 chapters, unweakened.

New mutation-check obligation, matching this project's own established discipline:
for every new guarantee this unit adds (the multi-SKU isolation checks, the
pilot-start idempotency/refusal checks, Chapter 12's disposable-identity
enforcement if made mechanically checkable), demonstrate a plausible break the
check catches, confirm the mutation actually landed (diff-stat), then restore and
confirm green.

## Explicit statements this SOW must make, and does — restated here per the
## Principal's own instruction, not left implicit

- **Merging this SOW establishes the reviewed contract but does not authorize
  implementation.** Stated in "Authorization" above.
- **Implementation requires a separate Principal decision bound to the verified
  SOW merge commit.** Stated in "Authorization" above.
- **Unit 11 acceptance does not mean the 30-day pilot has finished** — nor does it
  mean the pilot has started; only the separately-authorized real pilot-start act
  means that. Stated in "Authorization" above and in §4.
- **Credentialed provider smokes, Andrea live evaluation, pilot completion,
  proof-pack acceptance, and release remain Unit 12 work.** Stated in "Mission"
  above and in "Explicit non-scope" below.

## Explicit non-scope

Do not:

- add new signal kinds, effect kinds, governance concepts, or core
  `src/sovereign_agent/` primitives merely to make the Store expansion appear
  larger;
- create Chapters 13+ or any Unit 12-owned content;
- execute the real pilot-start act against the real named pilot organization;
- perform pilot completion, elapsed-time acceptance, proof-pack assembly, or
  proof-pack acceptance;
- conduct the Andrea live evaluation, decide its duration/sampling/participant
  count/aggregation/pass-fail criteria, or run any credentialed provider smoke;
- release;
- weaken any existing fencing, mailbox, workspace, or Pulse-attribution guarantee
  from Units 7-9;
- change the runtime dependency surface beyond Pydantic plus stdlib;
- silently exceed or silently compress against the current source budget (see
  "Budget" below).

The nine credentialed provider tests remain deselected and explicitly deferred to
Unit 12.

## Budget

`scripts/verify_source_budget.py` scopes only to `src/sovereign_agent/`. At this
SOW's base commit: `27/40 modules, 6139/6250 nonblank lines, 7/30 root exports` —
111 lines of headroom. Store-domain code (`src/reference_organizations/store/`) and
curriculum content (`book/`) live outside this budget, as they have since Unit 9's
own SOW established the same split for `pulse_gate.py`.

**If implementation genuinely requires more `src/sovereign_agent/` core-primitive
code than the remaining 111-line headroom** — for example, if the pilot-start
mechanism's own structured tables/functions cannot fit inside `sovereign_agent`
without exceeding it, or must live there rather than in `reference_organizations/`
for architectural reasons — **stop and request a precise budget amendment before
writing code**, matching F-U9-1's own precedent (that unit's budget was raised from
6000 to 6250, explicitly not as a target, only as permission to implement the
correct solution without compressing correctness to fit or padding to consume
headroom). Do not silently exceed the current ceiling. Do not treat a granted
amendment as license to pad.

## Gate

Run at the exact implementation head:

```bash
uv lock --check
make verify
python scripts/verify_curriculum.py
python scripts/verify_source_budget.py
git diff --check
```

Run `verify_curriculum.py` twice consecutively. Build the wheel, install into a
clean Python 3.14 environment outside the source tree, run `sovereign-agent
--help`, `sovereign-agent doctor`, `sovereign-agent demo store --mode simulated
--root /tmp/<somewhere-outside-source>` from that installed wheel. Run every new
chapter's `solution.py` exercise directly and confirm it executes cleanly,
producing the real captured output that goes into that chapter's README — never a
guessed expected-observations block. Live-provider tests remain deselected and
must be reported as unrun.

## Review and merge ritual

1. Stream implements on `unit-11/store-expansion-pilot-start`; it does not open or
   merge its own PR.
2. Master independently reads the implementation, runs the new chapter exercises
   directly, runs the multi-SKU isolation and pilot-start idempotency tests
   directly, and reproduces the mutation checks for every new mechanical
   guarantee.
3. Master independently mutation-checks at least:
   - a cross-SKU contamination (a sale of SKU A wrongly creates or influences work
     for SKU B) — the isolation guarantee must catch this;
   - a duplicate pilot-start (the same start request replayed, or two concurrent
     start attempts) — idempotency/refusal must catch this;
   - Chapter 12's exercise accidentally targeting the real pilot identity instead
     of a disposable one — the disposable-identity separation must catch this;
   - a fabricated `pilot.started` event inserted directly, bypassing the real
     mechanism — matching the same discipline Unit 10's Pulse-guard mutation
     check already established for `pulse.*` events.
4. Master opens the PR and names its exact head.
5. Sparring reviews that exact head against this SOW and the governing scope
   ruling.
6. No merge over `CHANGES_REQUESTED`.
7. Principal acceptance is requested explicitly after Sparring co-signs.
8. Merge only through the allowed GitHub PR mechanism.
9. Gate merged `main` from a clean clone.
10. Audit `docs/v1-unit11-store-expansion-pilot-start.md` (the documentation
    deliverable this unit adds) against merged behavior.
11. Flip its status to `ACCEPTED` only in a separate, reviewed change.
12. **Unit 11 acceptance at this point does not authorize the real pilot-start
    act.** That remains a separate, later, separately-authorized decision (see
    "Authorization" above). Unit 12 remains unstarted until both this unit's
    closure lands and any further Principal decision on the real pilot-start act
    is made.

If `main` advances, reconcile through an auditable PR-based path and rerun gates
and review on the resulting exact head. A prior co-sign does not survive a head
change.

## Documentation deliverables

Add `docs/v1-unit11-store-expansion-pilot-start.md`, following the shape
established by `docs/v1-unit7-workspace-lifecycle.md` through
`docs/v1-unit10-curriculum-completion.md`: status header (status `PROPOSED` until a
separate reviewed acceptance flip), the contract as testable properties, a verified
"how to check this document against the repository" command block (every command
run and confirmed working before being written into the doc), a budget-impact
statement, a "what this unit did not do" section (explicitly naming that the real
pilot-start act was not performed), and explicit non-claims.

Update `CHANGELOG.md` following the established per-unit style. Update
`book/README.md`'s chapter index to include Chapters 8-12.

## Acceptance conditions

Unit 11 is accepted only when the Principal can inspect the merged tree and
confirm:

- the Store catalog has at least two independently-tracked SKUs, with real tests
  proving cross-SKU isolation across sales, signals, wake decisions, Pulse
  origins, assignments, and replenishment effects;
- replay, restart, and concurrent qualification preserve per-SKU idempotency with
  no cross-SKU contamination or duplicate governed work, proven with real,
  separate database connections;
- Chapters 8-12 all exist, execute, chain coherently, and each imports and runs
  real production code with no teaching fork;
- Chapter 12 genuinely exercises the pilot-start mechanism against a disposable
  identity, never the real named pilot organization;
- the pilot-start mechanism is atomic, idempotent, and refuses on an incompatible
  active pilot, proven with real tests, not merely built and asserted;
- every new mechanical curriculum guarantee is demonstrably load-bearing
  (mutation-checked, not merely present);
- the `src/sovereign_agent/` budget is respected, or a precise amendment was
  requested and granted before implementation, never silently exceeded or
  compressed against;
- no live-provider evidence is claimed;
- the real pilot-start act was NOT performed, and this is stated explicitly, not
  merely omitted.

Proceed first by filing and reviewing this SOW. Do not begin implementation before
it is merged unchanged or a subsequent Principal ruling amends it.

## Related documents

- [Sovereign Agent 1.0 — executable textbook (design memo)](sovereign-agent-v1-educational-control-plane.md)
- [Ruling: Unit 11 scope — pilot start marker, multi-SKU catalog, Chapters 8-12](../rulings/2026-08-30-unit11-scope.md)
- [Unit 10 SOW: curriculum completion, Chapters 0-7](sovereign-agent-v1-unit10-curriculum-completion.md)
- [Unit 10: curriculum completion, Chapters 0-7](../v1-unit10-curriculum-completion.md)
- [Unit 9: Pulse and proactive governed work](../v1-unit9-pulse-proactive-work.md)
- [Unit 8: supervisor, fencing, and hard-kill recovery](../v1-unit8-supervisor-fencing-recovery.md)
