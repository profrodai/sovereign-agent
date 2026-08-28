# Deferral: multi-process fencing is Unit 8, not Unit 4

- **id:** `ruling-2026-08-26-deferral-unit4-fencing`
- **decided:** 2026-08-26
- **authority:** principal
- **applies_to:** Unit 4 mailbox leases; Unit 8 supervisor
- **status:** ACTIVE

## What Unit 4 provides

A durable addressed mailbox with claim leases. Claiming is a compare-and-set:
`UPDATE ... WHERE state = 'NEW' OR the lease has expired`, which must affect
exactly one row. Two **distinct** actors contending for one message produce
exactly one winner, verified by a two-connection barrier test.

## What it does not provide

A second connection using the **same** actor id is granted the claim, because a
claim already held by that actor short-circuits and returns it. That is
actor-level idempotency — it is what makes a retried worker harmless — and it is
**not** process-level exclusivity. Two processes hosting one actor can both
proceed.

## Holdings

1. **One process may host an actor.** Running the same actor id concurrently in
   two processes is outside the 1.x contract and is not defended against.
2. **Fencing is deferred to Unit 8.** A fencing token — a distinct lease/attempt
   id required at completion, so a resumed worker cannot commit under a lease it
   no longer holds — belongs with the supervisor that owns process lifecycle.
   Building it in Unit 4 would mean inventing process lifecycle in a unit that
   has no supervisor to own it.
3. **The property must not be overstated.** No document or test name may
   describe this as "exactly one worker". What is proved is one winner among
   *distinct contenders*.

## Named limit: F-U4-1

Reclaiming an expired lease works through the `inbox()` sweep, which resets an
expired `CLAIMED` message to `NEW`. Calling `claim()` directly on your own
expired lease hits the same-owner short-circuit and returns the stale lease
without renewing it, so the compare-and-set's expired branch is unreachable by
the owner.

Benign under holding 1 — only the addressed recipient can reach that path, so no
other actor can steal a lease — but it is dead code implying an intent the code
does not have. Recorded rather than silently fixed, because the fix belongs with
the fencing work in Unit 8.

## Verification

`tests/test_concurrency.py::test_only_one_contender_wins_a_contested_lease` and
`::test_the_same_actor_from_two_processes_is_idempotent_not_exclusive`. The
second asserts the current behaviour precisely so that a future change to it is
visible rather than silent.

## Closure (2026-08-28, Unit 8)

**F-U4-1 is closed.** `relay.claim()`'s same-owner short-circuit now fires
only when the lease is *both* same-owner *and* unexpired; a same-owner
*expired* reclaim falls through into the compare-and-set exactly like a
takeover attempt would, and wins it the same way, minting a fresh fencing
token from a new monotonic counter (`lease_tokens`, migration 13). The
previously-unreachable expired branch is now reachable by the owner, not
only by a different actor, and is covered directly by
`tests/test_fencing.py::test_same_owner_expired_claim_mints_a_fresh_token_fu4_1`.

`complete()` and `dead_letter()` verify that token atomically against the
durable row before writing, closing the actual consequence F-U4-1 named:
`docs/rulings/2026-08-26-one-process-per-actor.md`'s holding 1
("actor-level idempotency, not process-level exclusivity") is superseded by
holding 3 there, closed the same way. This section is additive -- the
holdings and the named limit above describe accurately what was true before
Unit 8 landed, and are left unedited as the historical record of what F-U4-1
*was*. See `docs/v1-unit8-supervisor-fencing-recovery.md` for the full
fencing contract and its complete proof matrix.
