# Lab 00 — Trace a governed result

## Challenge

Build a miniature execution trace in which a worker report is only a proposal. A result may become accepted only after the ledger contains an assignment, durable evidence, an independent review, and a principal acceptance. Persist the trace as JSON so you can inspect the exact data that supports the final claim.

## Production map

This lab compresses the control flow in `Organization.run_assignment`, `Organization.verify_outcome`, `Organization.review`, and `Organization.accept`. The real implementation has richer records and SQLite transactions; the same distinction remains: “the provider said completed” is not evidence that the governed outcome is true.

## Run it

Copy the starter before editing, then run this lab's checker against your copy:

```bash
cp starter.py work.py
python -c 'from pathlib import Path; import check, work; print(check.check(work, Path(".lab-run")))'
```

Implement `exercise(root)` in `work.py`, then compare its observations with `expected.json`. Your function must be safe to run twice against the same root.

## Break it

Delete the evidence event while leaving the worker's `completed` report intact. Your acceptance calculation must become false. Then reorder review before evidence and make the trace reject that ordering.

## Explain it back

Explain which record answers each question: Who was assigned? What did the worker claim? What fact was observed? Who reviewed it? Who accepted it? Why can no one record answer all five questions honestly?
