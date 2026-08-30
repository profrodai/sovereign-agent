# Ruling: Unit 11 closes on local, learner-controlled SQLite — the real-deployment pilot-start gate is withdrawn

- **id:** `ruling-2026-08-30-unit11-local-closure-supersedes-real-deployment-gate`
- **decided:** 2026-08-30
- **authority:** principal, incorporating direct Operator correction (message `SA-P-20260830-UNIT11-LOCAL-001`)
- **applies_to:** Sovereign Agent 1.x, Unit 11 — closure basis; supersedes prior real-deployment requirement
- **status:** ACTIVE

## Why this ruling exists

Unit 11's implementation (multi-SKU catalog, Chapters 8-12, the pilot-start
mechanism) was reviewed, independently falsified, merged, and accepted at
`95f633bb2de066e072638dfb5d18f811f204701b`. What remained open was the real
pilot-start act itself: the governing scope ruling (Holding 1, below) required
that act to run against "the named pilot organization," and the SOW's own
closure sequence made Unit 11's `PROPOSED -> ACCEPTED` flip and final closure
wait on it.

Master filed a complete, reviewed, hash-pinned execution packet
(`.unit11/real-pilot-start-invocation.py`, `sha256:
20bf5e46dac9a19d9b2af5bed0d535eaf88d2613c0862ec1888f3b52974eafcb`) for that act,
independently correspondence-reviewed by Sparring. Four of the five target-tuple
identifiers were fixed by the Principal. The fifth — `TARGET_DB_PATH`, an
absolute path to an *existing, persistent, real* Sovereign Store deployment
database — could not be supplied, because Sparring's own verification correctly
observed that no machinery in this project can distinguish "a freshly-migrated
database" from "a genuine production deployment": that attestation rests
entirely on there being a real deployment to point at, and none exists.

The Operator's direct correction, incorporated into this ruling by the
Principal, holds that requiring a real production deployment to close a
curriculum unit was itself the error: **Sovereign Agent 1.x is an approachable
executable textbook and reference implementation.** It must not require
infrastructure beyond what a student laptop or an ephemeral notebook-style
environment already has. SQLite — already this project's own persistence
choice throughout — is the correct mechanism: standard library, no server, no
new runtime dependency, one inspectable local file, and it already supports
every transactional/concurrency lesson this project teaches. Introducing
DuckDB, or any other new dependency, to manufacture a "more real" deployment
target would add a dependency without solving a problem SQLite does not
already solve here.

## What this ruling holds

1. **Unit 11 acceptance is based on the merged, reviewed pilot-start mechanism
   operating against local, disposable, learner-controlled SQLite databases.**
   The mechanism itself — atomic two-write transaction, CAS idempotency,
   fail-closed refusal on an incompatible active pilot, the identity-conflict
   comparison (F-U11-1) and its per-field mutation coverage, all independently
   falsified by both Master and Sparring against the merged code — remains the
   accepted implementation. Nothing about the mechanism's own correctness
   changes.
2. **No existing production Sovereign Store deployment is assumed.** This
   project does not claim, and this ruling does not require, that one exists.
3. **No `TARGET_DB_PATH` will be supplied.** The execution packet's real-act
   invocation will not run against a production target, because none is
   assumed to exist.
4. **No real 30-day clock, governance receipt, or production pilot-start act
   is required to close Unit 11.** The governance-receipt sequencing work done
   in this SOW's own corrected §4 (separating the receipt from the mechanism's
   atomic transaction) remains correct *as a description of the mechanism's
   own design* — it simply is not invoked for real to close this unit.
5. **The execution packet and its four reserved identifiers
   (`PILOT_ID = "sovereign-store-pilot-001"`, `STORE_ORG_ID = "sovereign-store"`,
   `PILOT_PROFILE_ID = "sovereign-store-30-day-v1"`,
   `EVIDENCE_NAMESPACE = "sovereign-store/pilots/sovereign-store-pilot-001/evidence"`)
   are retired unused.** They authorize nothing. They must never be presented,
   in any document this project produces, as evidence that a real pilot began.
   The untracked file `.unit11/real-pilot-start-invocation.py` should be
   removed once this ruling lands; no production replacement is required.
6. **Unit 12 may teach and verify a local pilot lifecycle, provider smokes,
   the Andrea evaluation, and proof-pack mechanics** — but it must not claim
   that a real 30-day operational pilot occurred, because none will have.
7. **A genuine 30-day deployment pilot belongs to a later, separately
   authorized operational program** — most naturally ZEO Go, per the
   Operator's correction — not to completion of this Python textbook.

## What this ruling explicitly supersedes

Historical text is **preserved, not silently rewritten.** Each superseded
passage is named below by its own exact citation; none is edited or deleted.
A reader following any of these citations will find the original text intact,
with this ruling as the durable record of what no longer binds.

- **`docs/rulings/2026-08-30-unit11-scope.md`, Holding 1**, specifically the
  paragraph beginning "**The pilot does not start merely because Unit 11 code
  merges.**" and ending "...Unit 11 closes only after that act and its
  governance receipt are durably verified — a fourth authorization gate beyond
  the SOW-review, implementation-review, and acceptance gates every prior unit
  has already used." **Superseded**: no such fourth gate against a real
  deployment governs Unit 11's closure. The rest of Holding 1 (the mechanism's
  own required shape: durable SQLite record, `pilot.started` event, stable
  identity, canonical UTC start time, idempotency, incompatible-pilot refusal)
  is **not** superseded — it describes the mechanism actually built and
  accepted, and remains binding as a description of what was implemented.
- **`docs/sows/sovereign-agent-v1-unit11-store-expansion-pilot-start.md`**,
  specifically:
  - The **"Authorization"** section's second authorization gate paragraph
    (beginning "**A second, independent authorization gate governs the real
    pilot-start act specifically**") — **superseded**: no such second gate
    against a real target governs this document's own `ACCEPTED` flip.
  - The **"Final Unit 11 closure conditions"** section's six-step sequence in
    full — **superseded**: closure no longer depends on steps 2-4 of that
    sequence (separate real-act authorization, the real act executing, the
    filed receipt). Step 1 (implementation acceptance, gated and audited on
    clean `main`) already happened and stands. Steps 5-6 (the reviewed
    `PROPOSED -> ACCEPTED` flip, a final clean-`main` gate) are **not**
    superseded — they still describe how this document closes, just without
    the withdrawn real-act precondition. See "Closure sequence" below for the
    corrected version of those two steps.
  - §4's ("The pilot-start mechanism") own text describing the mechanism's
    atomic transaction, idempotency, and refusal behavior is **not**
    superseded — it accurately describes the accepted implementation. Only
    the claim that closure waits on the mechanism's real-target invocation is
    withdrawn.
- **`docs/sows/sovereign-agent-v1-educational-control-plane.md`, sequencing
  amendment 6**, specifically the clause "...then starts the 30-day pilot.
  Unit 12 finishes the pilot..." — **superseded** to the extent it claims Unit
  11 starts, and Unit 12 finishes, an actual real-world 30-day pilot. The rest
  of amendment 6 (Unit 10 completing Chapters 0-7; Unit 11 expanding the Store
  and landing Chapters 8-12) is **not** superseded and remains accurate — Unit
  11 did exactly that.
- **The top-level SOW's `done_when` clause**, specifically the line "30-day
  Sovereign Store pilot -> redacted proof pack accepted" — **superseded** as a
  literal real-deployment requirement. This project's own `done_when` no
  longer requires a real 30-day operational pilot to be considered complete;
  Unit 12's own future scope descent will define what, if anything, replaces
  this line for local/learner-controlled evaluation.

No other holding, section, or document is touched by this ruling. In
particular: the multi-SKU catalog (Holding 2), the Chapters 8-12 map
(Holding 3), Unit 12's own soak definition being undecided (Holding 4), the
soak terminology rule (Holding 5), and the Holding 6 non-conflict finding all
stand exactly as ratified.

## Closure sequence (corrected)

1. Audit Unit 11 against the corrected educational contract (this ruling).
2. Open a separate, reviewed status-flip PR changing the Unit 11 SOW's
   `status` from `PROPOSED` to `ACCEPTED`.
3. Gate clean merged `main`.
4. Close Unit 11.
5. Unit 12 remains separately unauthorized until the Principal opens its own
   scope descent — this ruling does not authorize any Unit 12 work.

No database mutation, real pilot-start act, governance receipt, or Unit 12
work is authorized by this ruling. Filing and merging this ruling is a
docs-only change.

## Next authorized action

Master may file this ruling as an append-only document, update the rulings
index, remove `.unit11/real-pilot-start-invocation.py` (untracked; its
removal itself needs no PR since it was never committed), and route this
ruling through the same review discipline as every prior ruling: exact-head
Sparring review, no merge over `CHANGES_REQUESTED`, explicit Principal
acceptance requested before merge.

After this ruling merges and is verified on clean `main`, Master may prepare
the separate status-flip PR named in the corrected closure sequence above —
but that PR is not authorized by this ruling alone; it follows the same
review-and-merge ritual as this ruling itself.

## How to check this ruling against the repository

```bash
# Confirms the historical text this ruling supersedes is preserved, unedited
grep -n "fourth authorization gate" docs/rulings/2026-08-30-unit11-scope.md
grep -n "A second, independent authorization gate" \
  docs/sows/sovereign-agent-v1-unit11-store-expansion-pilot-start.md
grep -n "Final Unit 11 closure conditions" \
  docs/sows/sovereign-agent-v1-unit11-store-expansion-pilot-start.md
grep -n "starts the" docs/sows/sovereign-agent-v1-educational-control-plane.md
grep -n "30-day pilot. Unit 12 finishes" \
  docs/sows/sovereign-agent-v1-educational-control-plane.md
grep -n "30-day Sovereign Store pilot -> redacted proof pack accepted" \
  docs/sows/sovereign-agent-v1-educational-control-plane.md

# Confirms the mechanism itself (not superseded) still stands, merged and green
python scripts/verify_curriculum.py
uv run --python 3.14 pytest tests/test_pilot.py -q

# Confirms the retired execution packet's reserved identifiers are not
# present anywhere as claimed evidence of a real pilot start
grep -rn "sovereign-store-pilot-001" docs/ | grep -v \
  "2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md"

# The rulings index and directory agree
python scripts/verify_curriculum.py
```
