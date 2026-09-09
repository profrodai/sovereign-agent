## A live worker may no longer own the work

A worker process can pause for a long time and resume after another worker has taken over.
Its memory still says “I own this job.” The database may disagree. **Concurrency** means more
than one execution can interact with shared state. Correctness must therefore depend on current
shared evidence rather than one process's stale local belief.

A **claim** identifies the owner of a work item. A **lease** limits that ownership in time.
A **generation** distinguishes successive claims. An **epoch** distinguishes a larger authority
era, such as before and after restoring a database. A **fence** is a check that refuses a stale
claim before the protected operation. These terms name different fields because one matching
field cannot compensate for another stale one.

### Isolate a generation mismatch

Keep work identity, worker name and time valid. Change only generation. If the stale claimant
can still write, the generation check is missing. If you also expire its lease, another check
could hide that defect. This is why a good failure experiment varies one protection at a time.

```python tags=["foundation", "worked-example"]
intro_current_claim = {"work": "opening", "worker": "worker-1", "generation": 8, "epoch": "era-b"}
intro_old_claim = {**intro_current_claim, "generation": 7}
intro_effects = []


def intro_guarded_append(claim, value):
    if any(
        claim[key] != intro_current_claim[key] for key in ("work", "worker", "generation", "epoch")
    ):
        raise PermissionError("claim is stale")
    intro_effects.append(value)


try:
    intro_guarded_append(intro_old_claim, "stale observation")
except PermissionError:
    pass
intro_guarded_append(intro_current_claim, "current observation")
assert intro_effects == ["current observation"]
print(intro_effects)
```

The positive case is essential. A function that refuses every write would prevent stale writes
but also prevent useful work. The actual exercise observes durable transcript rows after both
admitted and refused attempts, not just the returned error strings.

### Restoring state creates an authority boundary

A restored database may contain a claim whose worker name and generation match a surviving old
process. An external authority marker and a fresh epoch distinguish the restored era from the
old one. Comparing only the database to itself would not expose every stale process. The chapter
checks the control epoch, claim epoch and retained marker before accepting a protected write.

```python tags=["foundation", "worked-example"]
intro_restored_control = {"epoch": "after-restore", "paused": False}
intro_marker = "after-restore"
intro_claim_before_restore = {"epoch": "before-restore", "lease_until": 200.0}
intro_now = 100.0
intro_authorized = (
    not intro_restored_control["paused"]
    and intro_marker == intro_restored_control["epoch"]
    and intro_claim_before_restore["epoch"] == intro_restored_control["epoch"]
    and intro_claim_before_restore["lease_until"] > intro_now
)
print("Unexpired but authorized:", intro_authorized)
assert intro_authorized is False
```

The lease is still in the future, but the epoch is stale. Explain which equality fails and why
extending the lease cannot repair it. The construction task also checks pause, full running-claim
identity, delegation deadline and parent cancellation. A delegated child's authority can end
because its parent no longer permits the work even while the child's own process remains alive.

### Recovery is not replaying every model call

If durable records already identify pending work and known effects, recovery should use them.
Starting another model conversation can invent a new intent or duplicate cost. **Recovery** here
means reconciling current authority and retained work so an admitted worker can proceed from
evidence. It does not mean a failed process gets to reclaim its former rights automatically.

The actual `assert_current` helper sits in the write path. Your implementation must be invoked
where observations or other protected changes occur. Calling it once during startup would leave
a gap: ownership can change between startup and a later write. A fence also cannot recall an
external request already admitted before ownership changed; that interval requires the operation
identity and reconciliation reasoning from the order chapter.

Before the exercise, create a case matrix varying epoch, generation, lease, marker, pause and
parent cancellation one at a time. Keep the remaining conditions valid. For every refused case,
record the durable row count before and after. Then test a fresh claim. The changed-constraint
task asks you to make the decision explainable without letting one stale field hide another.
