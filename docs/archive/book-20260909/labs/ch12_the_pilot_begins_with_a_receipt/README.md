# Chapter 12 lab: begin with a durable, honest receipt

## Challenge

Build a replayable pilot-start transaction and a small proof-pack verifier.
The same complete pilot identity must replay without another row or event. The
same ID with changed identity must conflict, a different active pilot must be
refused, and an injected fault must leave no orphan. Evidence paths must remain
inside the root, digests must match bytes, and NOT_RUN prose must not claim a
success that never occurred.

## Production map

Read `start_pilot`, `active_pilot_id`, and `verify_proof_pack.verify`, then run
the exact regression tests named in `lab.json`. The local model keeps the
essential production invariants while avoiding credentials, live providers,
and any named real pilot organization.

## Run it

```bash
python book/labs/ch12_the_pilot_begins_with_a_receipt/check.py \
  book/labs/ch12_the_pilot_begins_with_a_receipt/solution.py /tmp/sa-ch12-lab
```

Run the same command twice. The second run must describe the same one pilot,
one active slot, and one start event.

Copy the scaffold to a working file before implementing it:

```bash
cp book/labs/ch12_the_pilot_begins_with_a_receipt/starter.py \
  book/labs/ch12_the_pilot_begins_with_a_receipt/work.py
python book/labs/ch12_the_pilot_begins_with_a_receipt/check.py \
  book/labs/ch12_the_pilot_begins_with_a_receipt/work.py /tmp/sa-ch12-work
```

## Break it

Treat every matching `pilot_id` as a replay without comparing the other three
identity fields. Commit the pilot row before reserving the singleton active
slot. Replace resolved-path containment with a string-prefix test. Finally,
change the NOT_RUN note to “passed” and remove the lie scan. Each mutation
should create a specific checker failure.

## Explain it back

Why is a replay an exact identity claim rather than merely a duplicate-key
case? Why must the row, active slot, and event share one transaction? Explain
how a digest detects changed bytes yet cannot prove who produced them, and why
an internally consistent proof pack can honestly report `authenticated: false`.
