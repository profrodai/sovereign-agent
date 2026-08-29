# Instructor note — Chapter 5: Authority needs a fence

## Teaching intent

This chapter introduces the process/actor distinction that Chapters 6 and 7
both depend on without re-explaining. The teaching payoff is the two-process
proof: two genuinely separate `Organization` instances contending for the
same actor, through the real `run_assignment` path, with the second refused
before its provider is ever invoked. The point is not "leases exist" — it is
that a crashed-and-restarted worker and a still-live worker are
indistinguishable to actor-level reasoning alone, and this chapter's
mechanism is what makes them distinguishable.

## Prerequisite knowledge

Chapter 4's workspace vocabulary is not strictly required, but the chapter
ordering assumes the learner has already seen `run_assignment` invoked at
least once (Chapter 4's own exercise does this). No new database concepts
are needed beyond Chapter 1's compare-and-set intuition from the
append-only triggers.

## Likely misconceptions

- **"An actor and a process are the same thing."** This is the exact
  misconception the chapter exists to correct. An actor
  (`operator-course`) is a durable, config-declared identity with no
  lifetime of its own; a process is one running instance of the program,
  bounded by the OS. Two different PROCESSES can both claim to be the same
  ACTOR — that is the ordinary shape of a crash-and-restart, not an edge
  case.
- **"Why not just use the PID to tell processes apart?"** The chapter states
  this directly: PIDs are reused by the operating system. A resumed stale
  process must not be able to pass a "same PID" check against a genuinely
  new process the OS later assigned that same number by coincidence. Have
  the learner articulate a concrete scenario where PID reuse would cause a
  real bug before reading the chapter's own answer.
- **"The fencing token check is redundant with the actor lease check."** They
  are two separate compare-and-set mechanisms bound together — an execution
  attempt requires a CURRENT lease, RE-VERIFIED inside its own transaction,
  not merely trusted from an earlier acquisition. The exercise's
  `stale_lease_token` refusal demonstrates this is load-bearing, not
  decorative.

## Observation checkpoints

1. After the actor-lease CAS section: confirm the learner notices the token
   increments (`1` then `2`) rather than being reused — ask them to predict
   what would go wrong if takeover tokens could repeat.
2. After the execution-attempt section: confirm the learner reads BOTH
   refusal categories (`execution_attempt_held` for a second attempt on the
   same assignment, `actor_lease_lost` for a stale token) and can tell them
   apart.
3. The two-process section is decisive. Confirm the learner notices
   `assignment_never_reached_running: "CREATED"` — the refusal happens
   BEFORE the provider is invoked, not merely that the result was discarded
   afterward. This distinction (refused before vs. discarded after) recurs
   in Chapter 4's own workspace-policy validation and should be named as the
   same pattern if the learner has already internalized it there.

## Discussion prompts

- "The fence is a LEDGER guarantee, not a filesystem one — a process that
  lost its lease can still be running and writing files. What's the
  practical consequence of that gap for someone deploying this system?"
- "Why does releasing a lease need to be a compare-and-set too (matching
  both process identity AND token), rather than a plain delete?"

## Facilitation timing

Roughly 30-35 minutes guided: 10 minutes on the actor-lease CAS, 10 minutes
on execution-attempt fencing and its binding to the lease, 10-15 minutes on
the two-process proof plus discussion — do not rush the two-process section,
it is the chapter's whole point.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain, unprompted, why "an
actor" and "a process hosting that actor" are different things that need
different fencing mechanisms — and can name what specifically the fence
guarantees (canonical writes never come from a stale process) versus what it
explicitly does not guarantee (a stale process's subprocess is not killed).
A learner who conflates the two levels has not yet landed this chapter and
will find Chapter 6's recovery mechanism confusing, since recovery is
specifically about a PROCESS dying while its ACTOR lease bookkeeping is still
technically live.
