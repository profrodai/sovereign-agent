## Challenge

A killed worker cannot report its own death, and an output file is not proof of completion. Build a supervisor recovery transaction that records a terminal `FAILED` assignment and `worker_lost` receipt while clearing the current execution fence. Make two supervisors contend for the same abandoned attempt and prove that exactly one wins.

## Production map

- `src/sovereign_agent/supervisor.py:recover_abandoned_assignments` never guesses success and uses the current attempt as its compare-and-set guard.
- `src/sovereign_agent/fencing.py:release_execution_attempt` clears the fence inside the same transaction as terminal state.
- `src/sovereign_agent/supervisor.py:tick` is a deterministic reconciliation pass, not a work creator.
- The tests in `lab.json` use a real hard kill, assert a failed receipt, prove idempotency, and verify terminal-before-reclaim ordering.

## Run it

From this directory, run:

```console
cp starter.py work.py
python check.py work.py /tmp/sa-ch06-lab
```

Fill the numbered TODO seams in `work.py`. Use `python check.py solution.py /tmp/sa-ch06-lab` only after attempting the repair. Your experiment must inject a failure between the terminal update and receipt insert, demonstrate rollback, then perform two recovery attempts without leaving duplicate evidence.

## Break it

Infer `COMPLETED` from a pre-existing output file and explain which unobserved writes could still be missing. Commit the terminal state before inserting the receipt and inject a crash between them. Remove `current_attempt = ?` from the update predicate and watch both supervisors claim recovery credit. Reclaim the workspace before committing recovery and identify what evidence a second supervisor loses.

## Explain it back

Why is `FAILED/worker_lost` the only honest inference from an expired execution attempt? Which three facts must change atomically? How does compare-and-set make a second supervisor race an ordinary no-op rather than a second recovery?
