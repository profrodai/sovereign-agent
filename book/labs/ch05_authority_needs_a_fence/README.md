## Challenge

Turn a durable mailbox claim into an exclusive, leased capability. Begin by reproducing the read-then-write race: two workers read `NEW`, then both write `CLAIMED` and both believe they won. Repair it with one conditional update, mint a monotonically increasing fencing token for every real takeover, and require the current token at completion.

## Production map

- `src/sovereign_agent/relay.py:claim` uses compare-and-set rather than a Python read followed by an unconditional write.
- `src/sovereign_agent/relay.py:_mint_claim_token` shares the monotonic token sequence used for process leases.
- `src/sovereign_agent/relay.py:complete` rejects a worker that resumes with an obsolete token.
- The tests in `lab.json` cover exclusive claims, idempotent retry, takeover after expiry, and stale-token rejection.

## Run it

From this directory, run:

```console
cp starter.py work.py
python check.py work.py /tmp/sa-ch05-lab
```

Fill the numbered TODO seams in `work.py`. Use `python check.py solution.py /tmp/sa-ch05-lab` only after attempting the repair. Use only the standard library; a rerun against the same root must produce the same JSON.

## Break it

Move the state predicate out of the `UPDATE` and into Python. Both contenders can now decide from the same stale read. Next reuse the old token when an expired lease is reclaimed by the same actor; the paused process and the replacement become indistinguishable. Finally, complete by owner alone and show the stale process overwriting the winner.

## Explain it back

Why is a lease owner insufficient without a token? Why does an unexpired retry return the same token, while an expired reclaim by that same actor must mint a larger one? Identify the exact SQL predicate that decides who owns authority.
