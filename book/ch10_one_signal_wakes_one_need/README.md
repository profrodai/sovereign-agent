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

## Where to look next

- `src/reference_organizations/store/pulse_gate.py` — `store_wake_gate`, the
  same gate from Chapter 7, now proven across two SKUs at once
- `tests/test_store_multi_sku.py` — the wake-decision-isolation and
  Pulse-origin-isolation tests this chapter's proof extends

`solution.py` imports the production package rather than copying it.

Next: [Chapter 11 — Replenishment scales without losing governance](../ch11_replenishment_scales_without_losing_governance/README.md)
