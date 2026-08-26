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
