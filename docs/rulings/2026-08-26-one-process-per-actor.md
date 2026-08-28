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

### Addendum (2026-08-28, same day): the closure above was correct but incomplete

The paragraph above, describing `acquire_actor_lease`'s own compare-and-set
as "defending" holding 2, is true of the primitive in isolation and remains
true. It did not say the primitive was actually *required* before a
provider could be invoked — Unit 8's first implementation built and tested
the lease mechanism without calling it from `organization.run_assignment`
at all, relying on execution-attempt fencing (assignment-scoped) alone.
Sparring's independent review of PR #31 caught this precisely:
`acquire_execution_attempt` is keyed by `assignment_id`, so two *different*
assignments for the *same* actor could each acquire their own attempt and
run under two separate processes — untouched by anything the first
implementation built, since neither assignment's execution-attempt fence
has any way to know about the other. The Principal ruled this must close
as a real precondition, not remain documented as a scope boundary:
"Assignment fencing prevents stale canonical commits, but it does not
enforce actor-hosting exclusivity before invocation. They are different
guarantees." `run_assignment` now calls `fencing.acquire_or_renew_actor_
lease` as the first thing it does, before anything else is touched, and
`acquire_execution_attempt` requires and re-verifies the resulting token —
connecting the two mechanisms rather than leaving the lease unused. See
`docs/v1-unit8-supervisor-fencing-recovery.md`'s Property 1 for the full,
current account.

### Second addendum (A-U8-1, Unit 8 audit finding, closed same day)

`test_the_same_actor_from_two_processes_is_idempotent_not_exclusive`, cited
above as verification, was the exact test the Unit 8 SOW ordered replaced
with tests proving the new process-level guarantee — "not merely renamed."
That replacement landed (`tests/test_fencing.py::
test_actor_lease_blocks_a_second_assignment_for_the_same_actor_before_invocation`),
but this original test itself survived byte-identical through all three PR
#31 rounds, still asserting a docstring claim — "1.x does not provide
fencing" — that became false the moment Unit 8 merged. A second, independent
Sparring audit of the merged `main` (distinct from the PR review rounds
above) found it. Renamed to
`test_the_same_actor_from_two_processes_is_idempotent_within_an_unexpired_lease`
and its docstring narrowed to state only what remains true — same-owner,
same-lease-window idempotency — with an explicit historical note. The
citation above is left unedited as the historical record of this ruling's
own verification at the time it was written.
