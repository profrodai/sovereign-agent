# Instructor note — Chapter 2: Work needs governance

## Teaching intent

This is the conceptual center of the whole book. Every later chapter's
"claim" is a specific instance of this chapter's general pattern: a claim,
the check that would falsify it, and the refusal that fires when the check
fails. If a learner does not leave this chapter fluent in the full
vocabulary table (Outcome through Ruling), Chapters 3 through 7 will read as
a list of unrelated mechanisms rather than one consistent design.

## Prerequisite knowledge

Chapter 1's canonical/projection distinction is load-bearing here: this
chapter's whole argument about evidence, review, and acceptance only makes
sense once the learner already accepts that SQLite — not a status field
someone could hand-edit — is where the truth lives. A learner who has not
internalized that yet will find Exercise 2 (accepting a false claim) far
less surprising than it should be.

## Likely misconceptions

- **"Governance is bureaucracy layered on top of the real work."** The whole
  point of Exercise 2 is the opposite: governance IS the mechanism that
  makes the work's own claims trustworthy. Correct this before it hardens —
  ask the learner directly whether they think the checks are optional
  overhead, and use their answer to calibrate how hard to lean on Exercise 2.
- **"Evidence is basically a log entry."** Exercise 2's own history (an
  earlier version accepted `["evd_i_just_made_this_up"]` as valid evidence)
  is the concrete counter-example: a log entry that nobody looks up is
  indistinguishable from a lie. Evidence has to be BOUND — to a check, an
  outcome, and an execution — or it proves nothing.
- **"Append-only on `events` covers everything the system needs to protect."**
  This chapter's own history is explicit that the guarantee had to migrate:
  append-only started on `events`, then the load of proof moved to evidence,
  reviews, verifications, and effects while those tables stayed unprotected
  for a while. Have the learner articulate WHY that gap was dangerous before
  reading the fix.
- **"If I can write arbitrary SQL, I've broken the whole system anyway, so
  what's the point of any of this?"** This is actually correct, and the
  chapter says so explicitly (the ruling on writers being inside the
  boundary) — the goal here is calibration, not overclaiming. Reward a
  learner who reaches this conclusion themselves; it's the sign they
  understood the limit rather than missing it.

## Observation checkpoints

1. After Exercise 1: confirm the learner can point to which table row proves
   each of the three acceptance checks was run, not just that three rows
   exist.
2. Exercise 2 is the decisive moment of this chapter. Do not let the learner
   skim past the refusal message — have them read
   `inventory_at_or_above_reorder_point` in the output and connect it back
   to the SPECIFIC check they just broke (`on_hand=0`).
3. After Exercise 3 (`test_acceptance_falsification.py`): confirm the
   learner reads at least five of the test names aloud and can explain, in
   one sentence each, which lie each one catches — the point is the taxonomy
   of lies, not the pass/fail count.
4. After Exercise 6 (append-only + the authenticity limit): confirm the
   learner can distinguish "detects inconsistency" from "proves authenticity"
   in their own words before reading the chapter's own explanation of the
   difference.
5. After Exercise 7 (recovery): confirm the learner notices that recovery
   creates a NEW assignment rather than reusing the failed one, and can say
   why that matters for auditability.
6. After Exercise 8 (the vacuous-guard mutation): confirm the learner can
   explain, without rereading, why `bool(contributors) and execution_id not
   in contributors` fails silently exactly when `contributors` is empty —
   the short-circuit is the whole bug. A learner who can only say "it's
   wrong" without locating the `and` has not yet landed this one.

## Discussion prompts

- "Acceptance re-runs the checks instead of trusting that they passed
  earlier. What's a real system you've used where 'it passed before' quietly
  became the same thing as 'it's still true'?"
- "No self-approval is enforced by deriving the performer from the ledger,
  not by asking the caller. Why does that specific design choice matter more
  than just adding a rule that says 'don't self-approve'?"
- "The organization 'remembers being wrong' after recovery — two
  verifications, two reviews, nothing deleted. What's the cost of that
  design, and is it worth it?"

## Facilitation timing

This is the longest chapter and deserves it — budget 60-75 minutes guided.
Exercise 2 alone deserves 15 minutes given its centrality. Do not compress
Exercise 7 (recovery) to save time elsewhere: Chapter 6 depends on the
learner already having internalized "refusal is not the end," and skipping
it here creates a real gap three chapters later.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain, unprompted, what
makes `ACCEPTED` mean something — this chapter's own stated learning
objective — and can name at least three of the ten falsification categories
from Exercise 3 without looking. This maps directly onto Andrea Alpha
evaluation Tasks 4 and 6 (`docs/andrea-alpha-evaluation.md`), which require a
human reader to judge whether the explanation is genuine understanding or
memorized vocabulary — a confidently wrong answer scores below a hesitant
right one, and that same discipline applies to a facilitator's own live
assessment here, not only to the written evaluation.
