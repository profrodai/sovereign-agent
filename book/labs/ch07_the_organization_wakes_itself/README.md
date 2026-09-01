# Chapter 7 lab: one signal, one canonical wake

## Challenge

Build one **manual Pulse tick** over SQLite. A durable inventory signal may
create governed work only when the inventory condition still qualifies while
the creation transaction holds the write lock. The same source signal must
always resolve to the same wake decision and work item, even when two database
connections contend.

Your `exercise(root)` implementation should return the observations in
`expected.json`. Keep identifiers deterministic so the result explains the
mechanism instead of timing noise.

## Production map

- `sovereign_agent.pulse.run_pulse_once` performs one deterministic pass. It
  does not sleep, loop, or schedule itself.
- `Organization.create_pulse_work` owns the transaction that revalidates the
  gate and creates the decision, SOW/assignment, event, and origin links.
- `pulse_wake_decisions.source_signal_id` is unique, so the database chooses
  one canonical result under contention.
- `tests/test_pulse.py` proves current-state revalidation, provenance, replay,
  restart, and two-connection contention.

## Run it

From the repository root:

```bash
cp book/labs/ch07_the_organization_wakes_itself/starter.py \
  book/labs/ch07_the_organization_wakes_itself/work.py
python book/labs/ch07_the_organization_wakes_itself/check.py \
  book/labs/ch07_the_organization_wakes_itself/work.py /tmp/sa-ch07-lab
```

Fill the numbered TODO seams in `work.py`, then run the checker. Run it again
after it passes: it should produce the same JSON. Compare with `solution.py`
only after you have a working attempt.

## Break it

Try each mutation separately and predict which assertion fails:

1. Check inventory before `BEGIN IMMEDIATE`, but not again inside it.
2. Remove the unique constraint on `wake_decisions.source_signal_id`.
3. Give each contender a randomly generated work id.
4. Insert the work row and its origin in separate transactions.

The important failure is not merely “two rows exist.” It is that there is no
longer one durable answer to “what work did this signal cause?”

## Explain it back

Why does a pre-transaction gate check describe the past? Why is returning the
winner’s identifiers stronger than merely swallowing a uniqueness error? And
what external component would still be required to call this manual tick on a
schedule?
