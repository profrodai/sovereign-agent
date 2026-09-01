# Chapter 10 lab: prove the path, not merely the condition

## Challenge

An inventory check says tea is low, and a later observation says stock rose.
That is useful corroboration, but it does not prove which assignment caused the
rise. Implement `exercise(root)` so acceptance requires an unbroken graph from
the intended outcome to its SOW, completed execution, effect, and exact SKU.
Make sibling proof, an old execution, and a different subject fail separately.

## Production map

Read `Organization.verify_sow` and `Organization.accept`, then descend into
`apply_restock`. The corresponding falsification tests are named in
`lab.json`. Notice that the world-condition check and the contribution proof
answer different questions; neither can substitute for the other.

## Run it

```bash
python book/labs/ch10_one_signal_wakes_one_need/check.py \
  book/labs/ch10_one_signal_wakes_one_need/solution.py /tmp/sa-ch10-lab
```

Copy `starter.py` to `work.py`, implement its seams, and point the checker at
your copy:

```bash
cp book/labs/ch10_one_signal_wakes_one_need/starter.py \
  book/labs/ch10_one_signal_wakes_one_need/work.py
python book/labs/ch10_one_signal_wakes_one_need/check.py \
  book/labs/ch10_one_signal_wakes_one_need/work.py /tmp/sa-ch10-work
```

No network access or credentials are needed.

## Break it

Remove one comparison at a time from your validator. Confirm that the checker
catches wrong outcome and wrong effect kind. Then invent an attack where the
right execution produces an effect for the right subject but for a sibling
outcome. Add the smallest assertion that rejects it without rejecting the
repaired graph.

## Explain it back

Why can two consistent observations detect a contradiction without
authenticating an actor? Draw the minimum proof graph and explain which edge
rejects a sibling SOW, which rejects replayed old work, and which prevents a
valid tea restock from being presented as proof about cones.
