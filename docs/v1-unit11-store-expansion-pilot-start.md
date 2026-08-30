# Unit 11: Store expansion, Chapters 8-12, and the pilot-start mechanism

- **status:** PROPOSED (implementation complete and self-gated on this
  branch; stays `PROPOSED` until Sparring review, Principal acceptance, a
  clean-`main` gate, and — separately and later — the real pilot-start act
  and its filed governance receipt all land, per the governing SOW's
  "Review and merge ritual" and "Final Unit 11 closure conditions")
- **authority:** principal (implementation authorization requested and
  granted separately from the governing SOW's own merge, per that SOW's
  "Authorization" section)
- **base:** `main = 5933eb75edaa4b00bfaaaffaa6d87ccf33f2e389` (the exact
  merged Unit 11 SOW commit this implementation branched from)
- **governing SOW:**
  [`docs/sows/sovereign-agent-v1-unit11-store-expansion-pilot-start.md`](sows/sovereign-agent-v1-unit11-store-expansion-pilot-start.md)
- **governing ruling:**
  [`docs/rulings/2026-08-30-unit11-scope.md`](rulings/2026-08-30-unit11-scope.md)
- **applies_to:** Sovereign Agent 1.x, Unit 11
- **work branch:** `unit-11/store-expansion-pilot-start`

This document follows `docs/v1-unit10-curriculum-completion.md`,
`docs/v1-unit9-pulse-proactive-work.md`, `docs/v1-unit8-supervisor-fencing-
recovery.md`, and `docs/v1-unit7-workspace-lifecycle.md`'s own shape: a
contract stated as testable properties, then how to check each one against
the repository. It is **additive** — nothing in the Units 0-10 acceptance
record is touched or revised here.

## What Unit 11 is, in one sentence

Unit 11 expands the Store's single-SKU walking skeleton into a genuine
multi-product catalog, proves the existing `inventory.changed -> wake gate
-> Pulse -> replenishment` pipeline generalizes without inventing new
signal kinds, effect kinds, or core organizational primitives, lands
Chapters 8-12 teaching that expansion, and builds — but never invokes
against the real named pilot organization — an atomic, idempotent
pilot-start mechanism.

## The contract

### Property 1 — a genuine multi-SKU catalog, additive alongside the single-SKU fixture

`src/reference_organizations/store/__init__.py`'s `seed()` is unchanged: it
still seeds exactly one product, `SKU-TEA`, because every chapter and test
written before this unit depends on that exact behavior. A new,
additive entry point, `seed_catalog`, seeds a real catalog of at least two
independently-tracked SKUs (`SKU-TEA`, reorder point 3; `SKU-COFFEE`,
reorder point 6, by default), each with its own `products` row, its own
`inventory` row, its own stock level, and its own reorder point.
`record_sale`, `below_reorder`, `store_wake_gate`, and `apply_restock` were
already SKU-parametric — none of them required a code change to support
more than one SKU; this unit's own diff to `src/reference_organizations/
store/__init__.py` is `seed_catalog`, `CatalogEntry`, and `DEFAULT_CATALOG`
only. No new signal kind, effect kind, governance concept, or
`src/sovereign_agent/` core primitive was added to support this.

### Property 2 — the multi-SKU isolation matrix, all six surfaces, real tests

`tests/test_store_multi_sku.py` proves, with two real SKUs racing and
running concurrently where the property requires it:

- **Sales isolation**: a sale of one SKU never changes another SKU's
  `inventory` row or produces a cash entry naming it.
- **Signal isolation**: two SKUs crossing their own reorder points in the
  same run produce two independently-readable signal rows with distinct
  `dedupe_key` values, extending Unit 9's own per-occurrence fix.
- **Wake-decision isolation**: `store_wake_gate` maps each signal to
  exactly its own SKU's own ACTIVE outcome, never the other's, and never
  fires for a SKU still above its own threshold.
- **Pulse-origin isolation**: `pulse_wake_decisions`/`pulse_origins` trace
  each decision back to the correct SKU's own signal — proven by reading
  `subject` and `source_signal_id` directly off the ledger for both SKUs.
- **Assignment/replenishment isolation**: multiple qualifying SKUs each get
  their own canonical SOW, assignment, and effect row; the `effects` table
  never attributes one SKU's restock to another SKU's assignment.
- **Replay, restart, and concurrency**: per-SKU idempotency survives a
  second `run_pulse_once` pass, a database reopen, and — the binding
  requirement — a REAL two-connection race
  (`test_two_real_connections_racing_two_different_skus_create_two_
  canonical_sows`), extending `tests/test_pulse.py`'s own
  `test_two_real_processes_evaluating_the_same_signal_create_one_canonical_
  sow` rather than forking it.

### Property 3 — Chapters 8-12, each importing and executing real production code

| Chapter | Directory | Teaches |
| --- | --- | --- |
| 8 | `ch08_the_store_becomes_a_catalog` | The single-product fixture becomes a genuine multi-SKU catalog |
| 9 | `ch09_each_product_has_its_own_threshold` | Independent stock state and reorder decisions, per SKU |
| 10 | `ch10_one_signal_wakes_one_need` | The wake gate binds each signal to its own SKU's own outcome |
| 11 | `ch11_replenishment_scales_without_losing_governance` | Multiple governed replenishment chains, idempotency and attribution intact |
| 12 | `ch12_the_pilot_begins_with_a_receipt` | The pilot-start mechanism, run against a disposable identity; "started" vs. "finished" |

Every chapter's `solution.py` imports the production package at module top
level and does not copy implementation (`scripts/verify_curriculum.py:138`'s
existing `class Database`/`CREATE TABLE` heuristic, unchanged, applies to
all thirteen chapters now). Chapter 7's closing gesture now forward-links to
Chapter 8; Chapters 8-11 each carry their own forward link; Chapter 12,
now the last chapter, carries none.

**Chapter 12 never touches the real named pilot organization.** Its
exercise uses `EXERCISE_PILOT_ID = "book-ch12-exercise-pilot"`, a fixture
value carrying a `book-ch12-exercise-` prefix reserved for this chapter and
used nowhere in this project's real-pilot tooling (there is none yet). A
new mechanical guard, `check_pilot_disposable_identity` in
`scripts/verify_curriculum.py`, runs this chapter's own exercise and refuses
if any `pilots` row it wrote does not carry that reserved prefix — making it
mechanically, not just conventionally, impossible for the curriculum gate
or test suite to reach a real pilot identity.

### Property 4 — the pilot-start mechanism: atomic, idempotent, fail-closed, never invoked for real

`src/reference_organizations/store/pilot.py`'s `start_pilot`, backed by
`src/sovereign_agent/database.py` migration 16 (`pilots`, `active_pilot`),
proves in `tests/test_pilot.py`:

- **Atomic terminal persistence**: the `pilots` row and the `pilot.started`
  event commit together, inside one `db.immediate()` transaction, or not at
  all.
- **Idempotent replay**: calling `start_pilot` again with the SAME
  `pilot_id` — even after closing and reopening the database — returns the
  first call's own record, never creates a second row or a second event.
  The CAS key is `pilots.pilot_id`'s own `PRIMARY KEY`, not a preflight
  `SELECT`.
- **Fail-closed refusal**: a DIFFERENT `pilot_id`, while one is active,
  raises `Refusal` (`category="pilot_already_active"`) and rolls back the
  whole transaction — no orphaned `pilots` row is ever left behind by a
  refused start. The CAS key is `active_pilot`'s own singleton `PRIMARY
  KEY`.
- **Real two-connection concurrency**: two genuinely separate `Database`
  connections racing the SAME `pilot_id` produce exactly one winner and one
  idempotent replay; two connections racing DIFFERENT `pilot_id` values
  produce exactly one winner and one fail-closed refusal — both proven with
  a real `threading.Barrier`, no mocks standing in for the SQLite boundary.
- **Fabrication leaves no traceable chain**: a `pilot.started` event
  inserted directly (bypassing `start_pilot` entirely) exists in the
  append-only event log but creates no `pilots` row — the same
  "fabrication is detectable" property Unit 10's own Pulse-guard mutation
  check established for `pulse.*` events
  (`test_a_fabricated_pilot_started_event_creates_no_real_pilots_row`).

**This unit's own implementation never calls `start_pilot` against the real
named pilot organization.** The only caller anywhere in this unit's own
code or curriculum is Chapter 12's exercise, against its own disposable
identity. The governance receipt described in the governing SOW's section 4
is not built or filed by this implementation — it belongs to a later,
separately-authorized step outside this unit's own implementation-
acceptance scope.

### Property 5 — mechanical curriculum guarantees extend to all 13 chapters, unweakened

`scripts/verify_curriculum.py`'s `REQUIRED_CHAPTERS`, `RUNNABLE`, and
`RUNNABLE_ARGS` grew from 8 to 13 entries, following the exact pattern Unit
10 already used growing from 4 to 8. Every existing mechanical guarantee —
chapter-scoped Pulse guard, instructor-note structure, chapter-sequence
coherence, frontmatter absence, import-not-copy, execute-not-merely-import —
applies unchanged to all 13 chapters. One new guarantee was added
(`check_pilot_disposable_identity`, Property 3 above), mutation-checked
alongside three further mutation checks proving the new test suites are
load-bearing (see "Mutation checking" below).

## How to check this document against the repository

Every command below was run against this unit's own implementation head
before being written down.

```bash
uv lock --check
make verify
python scripts/verify_curriculum.py
python scripts/verify_curriculum.py   # run twice consecutively, per the gate
python scripts/verify_source_budget.py
git diff --check

# Property 2 -- the multi-SKU isolation matrix, including real concurrency
uv run --python 3.14 python -m pytest -q tests/test_store_multi_sku.py

# Property 4 -- the pilot-start mechanism, including real concurrency and
# the fabrication-detection test
uv run --python 3.14 python -m pytest -q tests/test_pilot.py

# Property 3 -- each new chapter's own exercise, run directly
uv run --python 3.14 python book/ch08_the_store_becomes_a_catalog/solution.py --root /tmp/ch08
uv run --python 3.14 python book/ch09_each_product_has_its_own_threshold/solution.py --root /tmp/ch09
uv run --python 3.14 python book/ch10_one_signal_wakes_one_need/solution.py --root /tmp/ch10
uv run --python 3.14 python book/ch11_replenishment_scales_without_losing_governance/solution.py --root /tmp/ch11
uv run --python 3.14 python book/ch12_the_pilot_begins_with_a_receipt/solution.py --root /tmp/ch12

# Credential absence confirmed -- must be empty, same as every prior unit
env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API" || true

# 9 credentialed provider tests remain collected, deselected, and unrun
uv run --python 3.14 pytest tests/test_providers_live.py --collect-only -q -m live

# CLI artifact, from a built wheel, installed and run outside the source tree
uv run --python 3.14 python -m build --wheel -o /tmp/sovereign-agent-unit11-dist
python3.14 -m venv /tmp/sovereign-agent-unit11-venv
/tmp/sovereign-agent-unit11-venv/bin/pip install \
  /tmp/sovereign-agent-unit11-dist/sovereign_agent-*.whl
/tmp/sovereign-agent-unit11-venv/bin/sovereign-agent --help
/tmp/sovereign-agent-unit11-venv/bin/sovereign-agent doctor
/tmp/sovereign-agent-unit11-venv/bin/sovereign-agent demo store \
  --mode simulated --root /tmp/sovereign-agent-unit11-outside-source
```

Confirmed at implementation head: `uv lock --check` resolves cleanly;
`make verify` passes format, lint, mypy, all non-live tests (353 passed, 9
deselected), runtime-dependency check (`pydantic` only), and the source
budget; `verify_curriculum.py` reports `curriculum sound: 13 chapters, 13
exercises executed, all links resolve` on two consecutive runs;
`git diff --check` reports no whitespace errors, including across newly
added files; the wheel builds, installs into a clean Python 3.14
virtualenv outside the source tree, and all three CLI commands run
successfully from that installed wheel.

## Mutation checking

Every new mechanical guarantee was falsified before being reported as done:
a plausible break was reproduced, confirmed to have actually landed (diff
against a pristine copy), confirmed caught by the relevant check or test
suite, then restored to byte-identical and the check reconfirmed green.

1. **`check_pilot_disposable_identity` (new curriculum guard).** Chapter
   12's own `EXERCISE_PILOT_ID` was changed from the reserved
   `book-ch12-exercise-pilot` to a plausible real-looking value,
   `pilot-real-store-org-2026`. `diff` against a pristine copy confirmed
   the mutation landed. `verify_curriculum.py` correctly refused: "exercise
   created a pilot row whose identity ['pilot-real-store-org-2026'] does
   not carry the reserved disposable prefix." Restored; `diff` confirmed
   byte-identical; `verify_curriculum.py` reconfirmed
   `curriculum sound: 13 chapters, 13 exercises executed, all links
   resolve`.
2. **Multi-SKU isolation matrix, cross-SKU contamination.**
   `store_wake_gate`'s own `subject == sku` filter was dropped, so the gate
   matched ANY active outcome regardless of SKU. `diff` confirmed the
   mutation landed. Six of `tests/test_store_multi_sku.py`'s twelve tests
   correctly failed (wake-decision, Pulse-origin, assignment/replenishment
   isolation, and replay/restart properties all depend on the dropped
   filter). Restored; `diff` confirmed byte-identical;
   `tests/test_store_multi_sku.py` reconfirmed 12 passed.
3. **Pilot-start idempotency/refusal.** `start_pilot`'s plain `INSERT INTO
   pilots` (the CAS key for idempotent replay) was changed to `INSERT OR
   REPLACE`, removing the `try/except sqlite3.IntegrityError` replay
   handling. `diff` confirmed the mutation landed. Three of
   `tests/test_pilot.py`'s eight original tests correctly failed — the
   `pilots` table's own append-only trigger (migration 16) additionally
   caught the attempted replace at the database boundary
   (`sqlite3.IntegrityError: pilots are append-only: replace refused`),
   surfacing as an unhandled exception once the mutation removed the
   catch, which is itself further evidence the append-only guard and the
   idempotency tests are independently load-bearing. Restored; `diff`
   confirmed byte-identical; `tests/test_pilot.py` reconfirmed 8 passed (9
   after the fabrication test below was added).
4. **Fabricated `pilot.started` event, bypassing the mechanism.** Confirmed
   directly (and now pinned as
   `test_a_fabricated_pilot_started_event_creates_no_real_pilots_row`):
   inserting a `pilot.started` event via `append_event` without calling
   `start_pilot` leaves the append-only event log carrying the event but
   the `pilots` table empty — the same "fabrication leaves no traceable
   chain" property Unit 10's own Pulse-guard mutation check established for
   `pulse.*` events, applied here to the pilot-start mechanism.

`verify_curriculum.py` was run twice consecutively after every restoration
and at final completion; both runs reported `curriculum sound: 13 chapters,
13 exercises executed, all links resolve`. The full non-live test suite
(`make verify`'s own pytest step) was reconfirmed at 353 passed, 9
deselected after every restoration.

## Budget impact

Reproduced by `scripts/verify_source_budget.py`, before and after this
unit's change:

| | modules | nonblank lines | root exports |
| --- | --- | --- | --- |
| Before (Unit 10 accepted, this SOW's base) | 27/40 | 6139/6250 | 7/30 |
| After (this unit) | 27/40 | 6208/6250 | 7/30 |

**+69 nonblank lines, entirely migration 16** (`pilots`, `active_pilot`, and
their append-only triggers) in `src/sovereign_agent/database.py` — the only
`src/sovereign_agent/` file this unit touches. 42 lines of headroom remain
against the 6250 ceiling; no budget amendment was requested or needed.
`seed_catalog`/`CatalogEntry`/`DEFAULT_CATALOG` (Store-domain code) and
`start_pilot`/`PilotRecord` (also Store-domain code, in the new
`src/reference_organizations/store/pilot.py`) both live outside this
budget's own scope, matching the split Unit 9 established for
`pulse_gate.py`. Module count and root-export count are unchanged.

## What this unit did not do

- **Did not execute the real pilot-start act against the real named pilot
  organization.** `start_pilot` is called exactly once in this unit's own
  code paths outside its test suite — Chapter 12's exercise, against the
  disposable identity `book-ch12-exercise-pilot`. No real pilot identity,
  real Store organization id, or real pilot-profile id appears anywhere in
  this unit's implementation.
- **Did not build or file a governance receipt.** The governing SOW's
  section 4 places that step entirely outside this unit's implementation-
  acceptance scope, after a later, separate Principal authorization.
- **Did not flip this document's own status to `ACCEPTED`.** It stays
  `PROPOSED` until Sparring review, Principal acceptance, a clean-`main`
  gate, and — separately and later — the real pilot-start act and its
  filed governance receipt all complete, per the governing SOW's own closing
  sequence.
- **Did not run or claim credentialed provider smokes.** The 9 `live`-marked
  tests remain deselected and unrun, confirmed by direct collection.
- **Did not begin the Andrea live evaluation, pilot completion, proof-pack
  acceptance, release, or any Unit 12 work.**
- **Did not create Chapters 13 or beyond.**
- **Did not add any new signal kind, effect kind, governance concept, or
  `src/sovereign_agent/` core primitive beyond migration 16's own schema**
  — the multi-SKU expansion required zero changes to `record_sale`,
  `store_wake_gate`, `apply_restock`, or `run_pulse_once`; every one of
  those functions was already SKU-parametric.
- **Did not weaken any existing fencing, mailbox, workspace, or
  Pulse-attribution guarantee from Units 7-9.** `make verify`'s own full
  non-live suite (353 passed) includes every pre-existing test file,
  unmodified in substance.
- **Did not change the runtime dependency surface.**
  `scripts/verify_runtime_dependencies.py` reports `pydantic` before and
  after.
- **Did not open or merge its own pull request.** Implementation happened
  on `unit-11/store-expansion-pilot-start`; Master opens the PR after
  independently reproducing this unit's own mutation-testing evidence from
  scratch.

## Explicit non-claims

- No live-provider evidence is claimed anywhere in this document or this
  unit's own tests.
  `env | grep -Ei "ANTHROPIC|CLAUDE_CODE_OAUTH|CODEX_API|CURSOR_API"` is
  empty, same as every prior unit.
- No claim that the real 30-day Store pilot has started. Only Chapter 12's
  own disposable exercise identity has ever been passed to `start_pilot`.
- No claim that a governance receipt exists — its absence at this stage is
  the correct, expected state per the governing SOW's own corrected
  sequence, not a gap this unit's implementation needed to close.
- No claim that this document's status is anything other than `PROPOSED`,
  or that Unit 11 is closed.
- No claim that Chapters 13 or beyond exist, or that any Unit 12 work has
  begun.

## Related documents

- [SOW: Sovereign Agent 1.x — Unit 11 Store expansion, Chapters 8-12, pilot-start mechanism](sows/sovereign-agent-v1-unit11-store-expansion-pilot-start.md)
- [Ruling: Unit 11 scope — pilot start marker, multi-SKU catalog, Chapters 8-12](rulings/2026-08-30-unit11-scope.md)
- [Unit 10: curriculum completion, Chapters 0-7](v1-unit10-curriculum-completion.md)
- [Unit 9: Pulse and proactive governed work](v1-unit9-pulse-proactive-work.md)
- [Unit 8: supervisor, fencing, and hard-kill recovery](v1-unit8-supervisor-fencing-recovery.md)
- [Unit 7: workspace lifecycle](v1-unit7-workspace-lifecycle.md)
