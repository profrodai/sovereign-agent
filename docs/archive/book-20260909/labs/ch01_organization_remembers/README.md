# Lab 01 — Keep authority in the ledger

## Challenge

Use SQLite as the authoritative ledger and a JSON file as a disposable projection. Demonstrate three properties: a failed transaction leaves no partial fact, a pure verifier detects projection drift without repairing it, and an explicit reconciliation regenerates the projection from the ledger.

## Production map

`Database.transaction` owns commit and rollback. `render_outcome` computes expected bytes without writing, while `project_outcome` performs the write. That separation prevents a verifier from “checking” drift by silently erasing it.

## Run it

Copy the starter before editing, then run this lab's checker against your copy:

```bash
cp starter.py work.py
python -c 'from pathlib import Path; import check, work; print(check.check(work, Path(".lab-run")))'
```

Implement `exercise(root)` in `work.py` and use only files under the supplied root. The checker runs it twice: observations must remain identical and the database must contain one authoritative outcome, not duplicates.

## Break it

Move projection writing inside the verifier and observe how the drift check becomes a liar. Then remove the transaction around the deliberately failing insert and inspect the orphaned row.

## Explain it back

Why is the Markdown or JSON projection useful but not authoritative? Describe the different jobs of rollback, pure verification, and reconciliation.
