# Chapter 10 — One signal wakes one need

It's a busy Saturday. Lucy's vanilla drops below its line at 2:00 and her
chocolate drops below its line at 2:05. Two alarms, close together. The one thing
that must never happen is a crossed wire: the vanilla alarm starting a chocolate
reorder, or both alarms collapsing into a single order that restocks one flavor
twice and the other not at all. Each signal has to wake *its own* need, and only
its own.

This sounds trivial — of course a vanilla alarm is about vanilla — but "which
signal is about which product" is precisely the kind of thing that goes wrong
when work is created from events rather than from a human pointing at a form. In
Chapter 7 you watched one signal correctly wake one need. This chapter makes sure
that stays true when two needs are in flight at once, by pinning the decision to a
fact carried *on the signal itself*, not to timing or arrival order.

## Learning objective

Watch the Store's own wake gate (`store_wake_gate`, the exact mechanism
Chapter 7 exercised for one SKU) correctly bind each of two DIFFERENT
signals to its own SKU's own outcome — never the other SKU's, and never
both — using nothing but the signal's own `subject_ref`.

Chapter 7 proved the gate correctly decides for one SKU. This chapter is
the smallest possible extension of that proof: two SKUs, two outcomes, two
signals, and the requirement that the gate never confuses which signal
belongs to which outcome.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Signal-to-SKU binding** | A signal's own `subject_ref` field is what the wake gate reads to decide which outcome it is about — not the order signals arrive in, not which one was created first. |

## Three different questions that all sound like "is it done?"

Before building anything, split one innocent question into the three it
actually contains, because the whole chapter turns on refusing to let them
blur:

- **Authentication** — *who or what produced this artifact?* (Out of scope
  for this ledger, honestly and explicitly — Chapter 2's Exercise 6.)
- **Corroboration** — *do independent observations agree the world is in
  the right state?* (Chapter 2's re-run-the-checks discipline.)
- **Causal binding** — *did THIS exact execution contribute the required
  effect to THIS exact subject and outcome?*

The third is the deepest idea in this system, and the easiest to fake:
"the world looks right" is necessary — and radically insufficient — for
"this work made it right." Build the check that only asks the second
question, and watch what it credits.

## Build the acceptance check yourself, five generations of it

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
    CREATE TABLE inventory (sku TEXT PRIMARY KEY, on_hand INT, reorder INT);
    CREATE TABLE outcomes (id TEXT PRIMARY KEY, subject TEXT);
    CREATE TABLE sows (id TEXT PRIMARY KEY, outcome_id TEXT, required_kind TEXT);
    CREATE TABLE executions (id TEXT PRIMARY KEY, sow_id TEXT, actor TEXT);
    CREATE TABLE effects (id TEXT PRIMARY KEY, execution_id TEXT, kind TEXT, subject TEXT);
""")
db.execute("INSERT INTO inventory VALUES ('SKU-TEA', 8, 3)")
db.execute("INSERT INTO inventory VALUES ('SKU-COFFEE', 9, 6)")
db.execute("INSERT INTO outcomes VALUES ('out-tea', 'SKU-TEA')")
db.execute("INSERT INTO outcomes VALUES ('out-coffee', 'SKU-COFFEE')")
db.execute("INSERT INTO sows VALUES ('sow-tea', 'out-tea', 'replenishment')")
db.execute("INSERT INTO sows VALUES ('sow-coffee', 'out-coffee', 'replenishment')")
db.execute("INSERT INTO executions VALUES ('run-t', 'sow-tea', 'operator-lucy')")
db.commit()
```

Note the opening state carefully: tea is at 8 against a reorder point of 3 —
**comfortably stocked** — and `run-t`, the execution assigned to keep it
that way, has done *nothing yet*. The freezer is full because the delivery
driver restocked it this morning, off the books.

### Generation 1: the check that sees a full freezer

```python
def world_is_right(db, sku):
    on_hand, reorder = db.execute(
        "SELECT on_hand, reorder FROM inventory WHERE sku = ?", (sku,)
    ).fetchone()
    return on_hand >= reorder


def accept_v1(db, sku, execution_id):
    if world_is_right(db, sku):
        return f"ACCEPTED: {sku} is stocked, crediting {execution_id}"
    return "refused: condition false"


print(accept_v1(db, "SKU-TEA", "run-t"))
count = db.execute("SELECT COUNT(*) FROM effects WHERE execution_id = 'run-t'").fetchone()[0]
print("effects recorded by run-t:", count)
```

```text
ACCEPTED: SKU-TEA is stocked, crediting run-t
effects recorded by run-t: 0
```

Accepted, with a straight face, on **zero recorded effects**. The condition
is true — for reasons that have nothing to do with the execution being
credited. v1 asked the corroboration question and then answered the causal
one. Every downstream consumer of this acceptance — payment, reputation,
Chapter 12's release evidence — now believes `run-t` did work it never did.

### Generation 2: "did it do anything?" — the wrong repair

```python
def accept_v2(db, sku, execution_id):
    if not world_is_right(db, sku):
        return "refused: condition false"
    effects = db.execute(
        "SELECT COUNT(*) FROM effects WHERE execution_id = ?", (execution_id,)
    ).fetchone()[0]
    if effects == 0:
        return f"refused: {sku} is stocked, but {execution_id} contributed nothing"
    return f"ACCEPTED: {sku} stocked AND {execution_id} did something"


print(accept_v2(db, "SKU-TEA", "run-t"))
db.execute("INSERT INTO effects VALUES ('eff-1', 'run-t', 'replenishment', 'SKU-COFFEE')")
db.commit()
print(accept_v2(db, "SKU-TEA", "run-t"))
```

```text
refused: SKU-TEA is stocked, but run-t contributed nothing
ACCEPTED: SKU-TEA stocked AND run-t did something
```

The first refusal is progress. Then `run-t` records one effect — a
replenishment of **coffee** — and v2 accepts the **tea** outcome on the
strength of it. "Did something" is a nonzero row count; "did *the* thing"
is a binding. Activity is not contribution.

### Generation 3: the right effect — presented by the wrong hands

```python
def accept_v3(db, sku, execution_id, required_kind):
    if not world_is_right(db, sku):
        return "refused: condition false"
    match = db.execute(
        "SELECT COUNT(*) FROM effects WHERE execution_id = ? AND kind = ? AND subject = ?",
        (execution_id, required_kind, sku),
    ).fetchone()[0]
    if match == 0:
        return f"refused: no {required_kind} effect on {sku} by {execution_id}"
    return f"ACCEPTED: {execution_id} caused a {required_kind} on {sku}"


print(accept_v3(db, "SKU-TEA", "run-t", "replenishment"))
db.execute("INSERT INTO executions VALUES ('run-x', 'sow-coffee', 'operator-mo')")
db.execute("INSERT INTO effects VALUES ('eff-2', 'run-x', 'replenishment', 'SKU-TEA')")
db.commit()
print(accept_v3(db, "SKU-TEA", "run-x", "replenishment"))  # crediting sow-tea with run-x's work
```

```text
refused: no replenishment effect on SKU-TEA by run-t
ACCEPTED: run-x caused a replenishment on SKU-TEA
```

v3 binds kind and subject correctly — and is defeated by its own argument
list. `run-x` belongs to `sow-coffee`; it happened to restock tea; and
because the *caller* chooses which execution id to present, tea's SOW just
took credit for the coffee crew's work. Chapter 2 met this exact disease:
**a caller-supplied fact is a fact the caller chose.** The execution must be
*derived* from the SOW under judgment, never handed in beside it.

### Generation 4: derive the execution — and meet the swapped subject

```python
def accept_v4(db, sow_id, sku, required_kind):
    if not world_is_right(db, sku):
        return "refused: condition false"
    row = db.execute("SELECT id FROM executions WHERE sow_id = ?", (sow_id,)).fetchone()
    if row is None:
        return f"refused: {sow_id} has no execution of its own"
    execution_id = row[0]
    match = db.execute(
        "SELECT COUNT(*) FROM effects WHERE execution_id = ? AND kind = ? AND subject = ?",
        (execution_id, required_kind, sku),
    ).fetchone()[0]
    if match == 0:
        return f"refused: {sow_id}'s own {execution_id} produced no {required_kind} on {sku}"
    return f"ACCEPTED: {sow_id} -> {execution_id} -> {required_kind} on {sku}"


print(accept_v4(db, "sow-tea", "SKU-TEA", "replenishment"))
db.execute("INSERT INTO effects VALUES ('eff-3', 'run-t', 'replenishment', 'SKU-TEA')")
db.commit()
print(accept_v4(db, "sow-tea", "SKU-TEA", "replenishment"))
```

```text
refused: sow-tea's own run-t produced no replenishment on SKU-TEA
ACCEPTED: sow-tea -> run-t -> replenishment on SKU-TEA
```

The refusal fires on the borrowed-credit attack — and then, at last, `run-t`
actually restocks tea (`eff-3`) and the chain accepts honestly. Done? One
argument is still caller-supplied. Watch:

```python
print(accept_v4(db, "sow-tea", "SKU-COFFEE", "replenishment"))
```

```text
ACCEPTED: sow-tea -> run-t -> replenishment on SKU-COFFEE
```

The crossed wire this chapter opened with, in its purest form: tea's SOW,
**accepted against coffee's condition**, credited by `eff-1` — that stray
coffee side-effect from Generation 2. Every individual binding held; the
caller simply pointed the whole apparatus at the wrong subject.

### Generation 5: the caller supplies one fact only

```python
def accept_v5(db, sow_id):
    outcome_id, required_kind = db.execute(
        "SELECT outcome_id, required_kind FROM sows WHERE id = ?", (sow_id,)
    ).fetchone()
    sku = db.execute("SELECT subject FROM outcomes WHERE id = ?", (outcome_id,)).fetchone()[0]
    if not world_is_right(db, sku):
        return "refused: condition false"
    row = db.execute("SELECT id FROM executions WHERE sow_id = ?", (sow_id,)).fetchone()
    if row is None:
        return f"refused: {sow_id} has no execution of its own"
    execution_id = row[0]
    match = db.execute(
        "SELECT COUNT(*) FROM effects WHERE execution_id = ? AND kind = ? AND subject = ?",
        (execution_id, required_kind, sku),
    ).fetchone()[0]
    if match == 0:
        return f"refused: {sow_id}'s own {execution_id} produced no {required_kind} on {sku}"
    return f"ACCEPTED: {outcome_id}[{sku}] <- {sow_id} <- {execution_id} <- {required_kind}"


print(accept_v5(db, "sow-tea"))
print(accept_v5(db, "sow-coffee"))
```

```text
ACCEPTED: out-tea[SKU-TEA] <- sow-tea <- run-t <- replenishment
refused: sow-coffee's own run-x produced no replenishment on SKU-COFFEE
```

The caller names the SOW. *Everything else* — outcome, subject, required
kind, execution — is read from the ledger's own bindings. And the final
refusal is this chapter's quiet masterpiece: `sow-coffee` is refused because
its execution, `run-x`, spent its one effect restocking **tea**. Doing
*someone else's* work does not satisfy *your own* SOW — the sibling that
donated its labor in Generation 3 cannot claim it back for itself either.
Causal binding cuts in both directions.

The chain v5 walks is worth seeing as a graph — each arrow is a foreign key
the caller cannot forge, plus the one live check:

```text
Outcome  out-tea  (subject: SKU-TEA) ......... world_is_right(SKU-TEA), NOW
   ^  sows.outcome_id
SOW      sow-tea  (required_kind: replenishment)
   ^  executions.sow_id
Execution run-t
   ^  effects.execution_id  AND  effects.kind = required_kind
      AND  effects.subject = outcome's subject
Effect   eff-3   (replenishment on SKU-TEA)
```

Production's `accept()` walks exactly this graph — "Subject is read from the
outcome, not supplied" is a literal comment in `organization.py`, the
`required_effect_kind` clause carries the no-vacuous-guard rule Chapter 2
quoted, and `tests/test_causal_binding.py` attacks every arrow above the
same way this section did. What the graph still does *not* prove is
authentication: an actor with raw database access could forge every row in
it, agreeing with itself perfectly. Chapter 2 drew that boundary; Chapter 12
will price it.

## The exercise

```bash
python book/ch10_one_signal_wakes_one_need/solution.py --root /tmp/lucy-ch10
```

Read the file first. Two outcomes are created, one per SKU. Two sales
happen, each crossing its own SKU's reorder point. `store_wake_gate` is
called directly, once per signal, so you can see each individual decision
before the aggregate Pulse pass runs.

## Expected observations

```json
{
  "two_signals_two_outcomes": {
    "tea_outcome_id": "out_...",
    "coffee_outcome_id": "out_..."
  },
  "gate_decisions": {
    "tea_signal_maps_to_tea_outcome": true,
    "coffee_signal_maps_to_coffee_outcome": true,
    "decisions_never_cross": true
  },
  "pulse_pass_result": {
    "tea_status": "created",
    "coffee_status": "created",
    "each_signal_got_its_own_sow": true
  }
}
```

Three facts this run proves:

1. **`tea_signal_maps_to_tea_outcome: true`, `coffee_signal_maps_to_
   coffee_outcome: true`.** Each signal's own gate decision names the
   CORRECT outcome, read back from the decision object the production gate
   actually returned — never assumed from which sale ran first.
2. **`decisions_never_cross: true`.** The two decisions' `outcome_id`
   values are different — the gate did not, even by coincidence, hand both
   signals the same outcome.
3. **`each_signal_got_its_own_sow: true`.** The full Pulse pass, run after
   the direct gate calls, independently confirms the same binding survives
   all the way through canonical creation: two signals, two SOWs, never one
   shared SOW standing in for both SKUs' work.

Confirm it yourself:

```bash
sqlite3 /tmp/lucy-ch10/.sovereign/organization.db <<'SQL'
SELECT wd.source_signal_id, wd.subject, po.sow_id
FROM pulse_wake_decisions wd JOIN pulse_origins po ON po.wake_decision_id = wd.id
ORDER BY wd.decided_at;
SQL
```

Expected: two rows, one `subject = SKU-TEA`, one `subject = SKU-COFFEE`,
each naming a different `sow_id`.

## Learner verification command

```bash
python -m pytest tests/test_store_multi_sku.py -k "wake_decision or pulse_origins_trace"
python scripts/verify_curriculum.py
```

Expected: all pass.

## Explain it back

1. `store_wake_gate` takes a `Signal`, not a SKU string, as its argument.
   Where inside the gate does it decide WHICH outcome the signal is about?
2. This chapter creates two ACTIVE outcomes, one per SKU. What would
   `store_wake_gate` do if TWO active outcomes both named the same SKU as
   their subject? (Look at the gate's own docstring, not just its code, for
   the answer.)
3. `decisions_never_cross` compares two `outcome_id` strings for
   inequality. Why is that a meaningful proof of isolation, rather than an
   accident of how identifiers happen to be generated?
4. State the three questions (authentication, corroboration, causal
   binding) and say which one each of accept_v1 through accept_v5 actually
   answers. Which generation is the first to answer the causal one at all?
5. Generation 4 had every individual binding right and was still defeated.
   What single design rule closes it, and where else in this book have you
   seen the same rule?
6. `sow-coffee` was refused even though its execution genuinely restocked a
   real SKU. Explain why "causal binding cuts in both directions" is a
   feature and not bureaucratic cruelty — what would crediting `run-x`'s
   tea work to `sow-coffee` corrupt downstream?
7. Every arrow in the proof graph is a foreign key. Name the one claim in
   the graph that is NOT a stored row but a live act, and say why it cannot
   be replaced by a stored row.

## Where to look next

- `src/reference_organizations/store/pulse_gate.py` — `store_wake_gate`, the
  same gate from Chapter 7, now proven across two SKUs at once
- `tests/test_store_multi_sku.py` — the wake-decision-isolation and
  Pulse-origin-isolation tests this chapter's proof extends

`solution.py` imports the production package rather than copying it.

Next: [Chapter 11 — Replenishment scales without losing governance](../ch11_replenishment_scales_without_losing_governance/README.md)
