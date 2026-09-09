## Scheduling converts due times into bounded work

Lucy wants an opening check every hour. The computer may be asleep or unavailable for several
hours. When it wakes, should the agent replay every missed check or prepare one current check?
That is a business policy, not a detail that a loop should choose accidentally. This chapter
uses **coalescing**: create at most one occurrence for each due job in this pass, record the
missed intervals, and move its next due time beyond now.

A **job** stores a recurring request and its timing. A **tick** is one bounded scheduler pass.
A **queue** holds admitted work for execution. Producing a queue item is different from executing
a model or purchasing stock. When nothing is due, the scheduler should create no work and make
no model calls. Scheduling itself is arithmetic and persistence, not language generation.

### Derive catch-up arithmetic on a number line

Let the saved due time be 10, the interval 5, and now 22. Due boundaries were 10, 15 and 20.
We emit one current occurrence, record two skipped intervals, and move next due to 25.
The elapsed whole-interval count is `(now - due) // interval`. Add one interval beyond that
count to reach the first future boundary. Predict the exact-boundary case at now 20.

```python tags=["foundation", "worked-example"]
intro_due = 10
intro_interval = 5
for intro_now in (9, 10, 19, 20, 22):
    if intro_now < intro_due:
        print(intro_now, "not due", intro_due)
    else:
        intro_skipped = int((intro_now - intro_due) // intro_interval)
        intro_next = intro_due + (intro_skipped + 1) * intro_interval
        print(intro_now, "one occurrence", "skipped", intro_skipped, "next", intro_next)
        assert intro_next > intro_now
```

At exactly 20 the occurrence is due, and the next boundary is 25. Advancing only from 10 to 15
would leave the job due; another same-time tick could emit another stale occurrence. Unit B
injects that precise defect and observes repeated work. Merely returning “coalesced” in a report
would not repair the stored next due time.

### A repeatable clock is an input, not a sleep

The tests pass `now` explicitly so they can explore a year's downtime in milliseconds. A fake
clock is an authored input, not a claim that a host actually woke unattended. **Wall-clock time**
represents calendar time; a **monotonic clock** is useful for elapsed durations because it does
not move backward with wall-clock adjustments. This lesson's persisted schedule uses its declared
time convention and validates supplied values. Do not mix two clock domains in one comparison.

```python tags=["foundation", "worked-example"]
import math

for intro_candidate_time in (0.0, 12.5, float("inf"), float("nan")):
    print(repr(intro_candidate_time), "finite:", math.isfinite(intro_candidate_time))
intro_next_due = 10.0
intro_created = 0
for intro_now in (10.0, 10.0):
    if intro_next_due <= intro_now:
        intro_created += 1
        intro_next_due += 5.0
assert (intro_created, intro_next_due) == (1, 15.0)
```

Floating-point infinity and NaN are values Python can represent, but they are unsuitable schedule
inputs here. A positive finite interval is a precondition for catch-up division. Fractional
intervals deserve explicit cases rather than an assumption that every job runs on integer hours.

### Queue capacity is a separate bound

A per-tick admission maximum limits new work in this pass. Total queue capacity limits retained
pending work. They are not interchangeable. If the queue cannot accept a due job, the code must
retain a meaningful deferral instead of advancing as though work was created. Paused control
state and disabled jobs are additional reasons not to enqueue.

The actual `tick` function reads due jobs in a deterministic order, checks control state and
capacity, creates work through the supplied enqueue path, updates timing and records events in
the same SQLite transaction. This data path is the object of the construction exercise. The
transfer uses repeated timestamps, a very long absence and an exact boundary to defeat a
solution that only happens to work for one missed hour.

Before coding, draw columns for due, now, interval, skipped, created work and next due. Fill them
for before-due, exact-due and long-absence cases. Then add “queue full” and explain which columns
are allowed to change. A local tick passing does not certify a service manager, host uptime or
calendar-time accuracy; those require the book's separate operational experiment.
