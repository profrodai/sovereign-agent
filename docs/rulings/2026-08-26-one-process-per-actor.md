# Ruling: one process per actor in 1.x; lease fencing is Unit 8

- **id:** `ruling-2026-08-26-one-process-per-actor`
- **decided:** 2026-08-26
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x mailbox claims and actor hosting
- **status:** ACTIVE

## The question

`claim()` is an atomic compare-and-set, so two *different* actors contending for
one message produce exactly one winner. But a second connection using the **same
actor id** is granted the claim, because a claim already held by that actor short
circuits and returns it.

Two processes hosting one actor can therefore both believe they may proceed.

## Holdings

1. **The mailbox provides actor-level idempotency, not process-level
   exclusivity.** Re-claiming a message you already hold is deliberately safe;
   it is what makes a retried worker harmless.
2. **One process may host an actor.** Running the same actor id in two processes
   concurrently is outside the 1.x contract and is not defended against.
3. **Lease fencing is deferred to Unit 8.** A fencing token — a distinct
   lease/attempt id required at completion, so a resumed worker cannot commit
   under a lease it no longer holds — belongs with the supervisor that owns
   process lifecycle. It is not built in 6.5.
4. **The property must not be described as "exactly one worker."** Documentation
   and test names say what is proved: one winner among *distinct contenders*.

## Why this is a ruling and not a code change

Adding fencing now would mean inventing process lifecycle in a unit that has no
supervisor to own it. The honest move is to state the boundary, name where it
gets closed, and stop any text from implying a guarantee that does not exist.

Verified by `test_the_same_actor_from_two_processes_is_idempotent_not_exclusive`,
which asserts the current behaviour so a future change to it is visible.

## Closure (2026-08-28, Unit 8)

**Lease fencing has landed.** Holding 3 above said fencing "belongs with the
supervisor that owns process lifecycle" and "is not built in 6.5" -- it is
now built in Unit 8, which also owns the supervisor holding 3 said fencing
needed. `fencing.py` implements process identity (never a PID -- PIDs are
reused by the operating system), actor-hosting leases, and execution-attempt
fencing bound to `organization.run_assignment`'s `RUNNING` transition, all
by compare-and-set against SQLite -- the same discipline `relay.claim()`
already used for holding 4's own two-distinct-contenders property, which
holding 4 correctly did not ask this ruling to weaken and which remains
true, unchanged, verified by
`tests/test_fencing.py::test_an_unaddressed_actor_is_still_refused_
regardless_of_fencing` and the original `tests/test_concurrency.py` suite.

Holding 1 ("actor-level idempotency, not process-level exclusivity") is
*narrowed*, not reversed: the mailbox still grants an idempotent return to
the same owner *within* an unexpired lease (retrying inside your own lease
window is still harmless), but an *expired* same-owner reclaim now mints a
fresh fencing token rather than silently returning stale state -- see
`docs/rulings/2026-08-26-deferral-unit4-fencing.md`'s own closure note for
F-U4-1, the named defect this exact gap produced. Holding 2 ("one process
may host an actor") is now *defended*, not merely stated: `acquire_actor_
lease`'s compare-and-set refuses a second process while an unexpired lease
exists, verified by `tests/test_fencing.py::
test_two_racing_acquirers_produce_exactly_one_winner`.

This section is additive. The holdings above describe accurately what was
true in 1.x before Unit 8 landed, and are left unedited as the historical
record. See `docs/v1-unit8-supervisor-fencing-recovery.md` for the complete
contract, proof matrix, and what fencing does and does not claim (it is not
an OS sandbox).
