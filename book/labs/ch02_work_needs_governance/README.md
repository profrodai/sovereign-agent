# Lab 02 — Try to forge acceptance

## Challenge

Implement a small acceptance verifier that requires several independent layers: the outcome condition is currently true, evidence describes the current state, evidence is bound to this SOW and its execution, and that execution produced the effect the SOW declared. Run a mutation battery against stale, borrowed, and noncausal proof.

## Production map

The exercise mirrors the proof joins enforced by `Organization.verify_sow`, `Organization.review`, and `Organization.accept`. Production evidence carries state digests and exact SOW/execution bindings; effects show contribution rather than merely repeating that the desired condition happens to be true.

## Run it

Copy the starter before editing, then run this lab's checker against your copy:

```bash
cp starter.py work.py
python -c 'from pathlib import Path; import check, work; print(check.check(work, Path(".lab-run")))'
```

Implement `exercise(root)` in `work.py`. Return deterministic verdicts for the valid proof and all three mutations. Persist the cases beneath the supplied root so you can compare the records field by field.

## Break it

First write the naive rule `accept = condition_true`. Watch every forged case pass. Add the checks one at a time and record which lie each layer eliminates. Finally change the order of the checks and decide which refusal gives the learner the most useful next action.

## Explain it back

Explain why fresh evidence can still be borrowed, correctly bound evidence can still be stale, and a true outcome can still be noncausal. What distinct claim does each layer prove?
