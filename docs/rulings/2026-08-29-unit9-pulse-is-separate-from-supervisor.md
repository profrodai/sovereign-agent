# Ruling: Unit 9 Pulse is a separate mechanism from the supervisor; attribution is structured and durable

- **id:** `ruling-2026-08-29-unit9-pulse-is-separate-from-supervisor`
- **decided:** 2026-08-29
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x, Unit 9 (Pulse) — scope, not implementation
- **status:** ACTIVE

This ruling records the Principal's decision on the two open design questions a
read-only Unit 9 scope descent surfaced but explicitly did not resolve. The
descent itself (`.unit9/SCOPE-DESCENT.md` at the time of this ruling, untracked
investigation evidence, not a durable record) is superseded as the citable
scope authority by this file. No code exists for Unit 9 yet; this ruling
authorizes scope only, not implementation.

## The two questions this ruling answers

1. **6a — trigger mechanism.** Does Unit 9 extend `Supervisor.tick()` with a
   fourth step that fires the wake gate and creates Pulse work, or does it
   build a separate mechanism under the reserved `pulse` CLI surface?
2. **6b — Pulse attribution.** Is "created without a human prompt"
   (`docs/sows/sovereign-agent-v1-educational-control-plane.md:60`) durably
   provable in the ledger after the fact, or does it rest only on the absence
   of a human CLI call at the instant of creation?

## Holding 1 — Pulse is a separate mechanism; the supervisor is not extended

Unit 9 must **not** add Pulse behavior to `Supervisor.tick()`.

Pulse is implemented as a distinct component under the reserved `pulse`
command surface (`docs/v1-unit8-supervisor-fencing-recovery.md:304-307`,
`src/sovereign_agent/cli.py:205,322` — `pulse` already named there as a
future, unimplemented, *separate* thing, not a `supervisor` extension). Pulse
owns:

```text
source signal
→ wake-gate decision
→ durable Pulse event
→ proactive governed-work creation
```

The Unit 8 supervisor remains responsible only for leases, fencing,
reconciliation, and hard-kill recovery — exactly its accepted contract
(`docs/v1-unit8-supervisor-fencing-recovery.md`, Properties 1-5). Its accepted
claim — "never reads a Pulse signal, never fires a wake gate"
(`src/sovereign_agent/supervisor.py:23`;
`docs/v1-unit8-supervisor-fencing-recovery.md:284`) — remains **literally
true** after Unit 9 lands. Unit 9 does not require, and must not produce, any
additive-historical correction to Unit 8's accepted record, because nothing
in Unit 8's text becomes false.

A single foreground runtime may eventually compose supervisor and Pulse
operations — nothing in this holding forbids one process running both — but
composition must call two distinct mechanisms with two distinct receipts. It
must not turn `Supervisor.tick()` into the Pulse engine, and must not blur a
supervisor reconciliation event with a Pulse event.

### Why this reading, not the alternative

The descent found the accepted Unit 8 record uses unqualified, present-tense
"never" for Pulse in three independent places (code docstring, and Properties
5 and 6 of the accepted doc), while using "not (yet)" elsewhere in the same
document specifically where a future extension was intended
(`docs/v1-unit8-supervisor-fencing-recovery.md:549`, lease renewal). That
textual distinction is deliberate, not incidental, and the extension reading
would have required reopening and correcting an already-accepted record as a
consequence of Unit 9's own work — a cost this ruling avoids by choosing the
reading under which nothing accepted becomes false.

## Holding 2 — Pulse attribution is structured, durable, and queryable

Pulse origin must be first-class, durable, and queryable — never inferred
from unindexed JSON, logs, process history, or the mere absence of a human
CLI call at creation time. The canonical ledger must be able to prove, after
the fact:

- whether a given SOW/assignment originated from manual dispatch or a Pulse;
- the source signal that triggered the wake-gate evaluation;
- the deterministic wake-gate decision itself;
- the Pulse event that created the work;
- the SOW and assignment produced from that Pulse.

At minimum, the design needs equivalents of these as structured columns or a
relational origin table with enforced references and uniqueness:

```text
origin_kind
source_event_id
wake_decision_id
pulse_event_id
```

This is the same discipline Unit 8 already applied to fencing: do not hide
the only authoritative fact in unindexed JSON (see
`docs/v1-unit8-supervisor-fencing-recovery.md`'s persistence requirements for
`current_execution_attempt`/`actor_lease_fencing_token` as structured
columns, not JSON blob fields).

Pulse replay, restart, or concurrent evaluation of the same qualifying signal
must resolve to the same canonical proactive-work creation, not duplicates —
an idempotency requirement analogous to Unit 8's mailbox and lease
compare-and-set discipline, applied here to wake-gate evaluation.

## Boundaries this ruling reaffirms, unchanged

- **Unit 8's boundary is unchanged.** Leases, fencing, reconciliation,
  hard-kill recovery remain exactly as accepted
  (`docs/v1-unit8-supervisor-fencing-recovery.md`). Nothing in this ruling
  reopens Unit 8.
- **OS-service hosting remains unscheduled.** No ratified source assigns it
  to Unit 9 or any other unit number as of this ruling.
- **Unit 12's boundary is unchanged.** Credentialed Claude/Codex/Cursor
  provider smokes (the 9 tests under the `live` marker) remain deferred to
  Unit 12; nothing about Pulse changes that.
- **No creation from nothing.** A wake-gate evaluation that finds no
  qualifying signal must create no work — the same "the supervisor
  reconciles, it does not invent" discipline Unit 8 established for
  `Supervisor.tick()` (`docs/v1-unit8-supervisor-fencing-recovery.md`,
  Property 5) applies to Pulse's own wake-gate evaluation: absence of a
  qualifying condition is not itself a trigger.

## What this ruling does not do

It does not write the Unit 9 SOW. It does not specify the exact schema, table
names, or CLI argument shapes for the Pulse mechanism — those are
implementation decisions for the SOW and its stream to make, falsify, and
have reviewed, same as every prior unit. It does not authorize any code
change. The next step is requesting the Unit 9 implementation SOW against
the exact `main` head this ruling merges at.

## How to check this ruling against the repository

```bash
# Unit 8's accepted "never" claims, unchanged and still literally true —
# re-run after Unit 9 lands, not merely at ruling time. The phrase wraps
# across lines in both files, so match the tail that survives wrapping.
grep -n "never fires a wake gate" \
  src/sovereign_agent/supervisor.py docs/v1-unit8-supervisor-fencing-recovery.md

# pulse is reserved as a distinct CLI surface, not a supervisor flag
grep -n "pulse" src/sovereign_agent/cli.py

# no Pulse event exists yet -- must be true until Unit 9 implements it
grep -rn "pulse\." src/sovereign_agent/ | grep -v "^src/sovereign_agent/cli.py" || true

# the rulings index and directory agree
python scripts/verify_curriculum.py
```
