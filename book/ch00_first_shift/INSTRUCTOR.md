# Instructor note — Chapter 0: Andrea's first shift

## Teaching intent

This chapter exists to give the learner one complete, working mental model of
the whole system before any of it is explained. It is deliberately magic on
first read — the point is not that the learner understands every step yet,
it is that they SEE a real accepted outcome happen, on their own machine,
with no credentials, in under two minutes. Everything after this chapter is
taking one piece of this magic apart. If a learner leaves this chapter unable
to explain how it worked, that is fine. If they leave doubting that it
actually happened, the chapter has failed — the whole point is that this is
real, checkable, and not a demo video.

## Prerequisite knowledge

None beyond "can run a command in a terminal" and "has Python 3.14
installed." This is the cold-start chapter — nothing about outcomes, SOWs,
governance, or the database schema is assumed yet. Do not pre-explain
vocabulary from Chapter 2 here; let the learner meet it as unexplained
labels first, then formally in Chapter 2.

## Likely misconceptions

- **"This is just a demo script, not the real system."** Correct this
  immediately with the "why this is not a toy" section: an earlier version of
  this exact demo printed `ACCEPTED` while the shelf was actually empty. The
  paperwork was perfect and the claim was false. This chapter's whole
  argument rests on that history being true, not hypothetical.
- **"`ACCEPTED` means the code ran without crashing."** The verifier script
  (`scripts/verify_store_outcome.py`) exists specifically to separate "the
  system said so" from "the world agrees." Have the learner break it
  themselves (set `on_hand = 0` and re-run) before moving on — reading about
  the distinction is not the same as watching it fail.
- **"The organization did this on its own."** It did not. Every step was
  dispatched by the learner's own command. This is the seed of Chapter 7's
  entire subject, and planting it correctly here (with the ledger proof: no
  `pulse.*` event anywhere) makes Chapter 7 land as a payoff rather than a
  surprise.

## Observation checkpoints

1. After running the demo: confirm the learner actually reads the printed
   `out_...  ACCEPTED` line, not just that the command exited 0.
2. After the first `sqlite3` query: confirm the learner can say, in their own
   words, what `SKU-TEA|8|3` means (on-hand is at or above reorder point) —
   do not let them treat the row as opaque.
3. After breaking the verifier: confirm the learner notices the outcome's
   `status` field STILL reads `ACCEPTED` even though the verifier now fails.
   This is the single most important observation in the chapter — if it is
   rushed past, the rest of the book's governance model will not stick.

## Discussion prompts

- "The demo used no API key and no network. What does that tell you about
  what this book is actually testing?"
- "If you were auditing this organization a year from now, which of the
  things you just saw would you trust, and which would you re-verify?"
- "The organization has 'no heartbeat yet.' What would have to be true for
  it to develop one, and would you want it to, for a system handling real
  money?"

## Facilitation timing

Roughly 25-30 minutes guided: 5 minutes running the demo and reading output,
10 minutes on the three `sqlite3` observation queries, 5 minutes breaking the
verifier and discussing why `ACCEPTED` did not change, 5-10 minutes on
"Explain it back" as a group discussion rather than individual silent
writing (this early in the course, verbalizing beats writing alone).

## Exercise debrief and assessment

A learner has landed this chapter if they can, unprompted, state the
difference between "the demo printed ACCEPTED" and "the verifier confirmed
it's true" — this is exactly Andrea Alpha evaluation Task 2's own pass
criterion (`docs/andrea-alpha-evaluation.md`), so a facilitator running this
chapter live is rehearsing that same evaluation question. A learner who can
run the demo but cannot articulate this distinction should not move on to
Chapter 1 yet — everything in Chapter 2 assumes this distinction is already
felt, not just heard.
