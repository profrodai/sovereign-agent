# Instructor note — Chapter 12: The pilot begins with a receipt

## Teaching intent

This is the last chapter of the book as it currently stands, and its
teaching intent is unusually specific: not "here is a new mechanism" alone,
but "here is a new mechanism, and here is exactly how far its own proof
reaches, stated as precisely as everything else this book has taught you to
demand." The chapter's own title is deliberately narrow — "begins," not
"runs," not "completes." A facilitator should treat the disposable-identity
discipline and the started-vs-finished distinction as equally important to
the mechanism itself, not as a caveat tacked onto the end.

## Prerequisite knowledge

Chapter 2's whole thesis (a claim needs a check behind it) and Chapter 7's
CAS/idempotency vocabulary (`UNIQUE` constraints as compare-and-set, not
preflight `SELECT`s). A learner who has not internalized why
`pulse_wake_decisions.source_signal_id` being `UNIQUE` matters (Chapter 7's
own "Explain it back" question 2) will not immediately see why `pilots.
pilot_id` being the CAS key here is the same idea applied to a different
table.

## Likely misconceptions

- **"This chapter starts the real pilot."** It does not, and this is the
  single most important thing to correct before running anything. Have the
  learner read `EXERCISE_PILOT_ID`'s own comment and explain, in their own
  words, why the prefix makes this structurally safe rather than merely
  named safely.
- **"A pilot record existing means the pilot succeeded, or is even
  running well."** `pilots` and `pilot.started` record only that a start
  ACT happened, atomically and durably. Nothing here evaluates whether the
  pilot is going well, and nothing here can, because that evaluation
  mechanism (Unit 12's own Andrea live evaluation and proof-pack
  acceptance) does not exist in this codebase yet.
- **"The second `start_pilot` call in this exercise is testing something
  different from the concurrency tests."** It is testing a WEAKER form of
  the same property: this chapter's two calls are sequential, in one
  process, one connection. `tests/test_pilot.py`'s own two-connection tests
  prove the same idempotency and refusal properties hold under a genuine
  race. Point the learner there explicitly — this chapter's own "Explain it
  back" question 4 asks exactly this.
- **"`active_pilot` and `pilots` are redundant tables."** They serve
  different questions: `pilots` answers "does a record for THIS identity
  exist" (the replay/idempotency question); `active_pilot` answers "which
  ONE pilot, if any, currently occupies the single active slot" (the
  fail-closed-refusal question). A learner should be able to say which
  table answers which question.

## Observation checkpoints

1. Before running: have the learner read `start_pilot`'s own docstring in
   `src/reference_organizations/store/pilot.py` and identify, before
   running anything, which INSERT is the CAS key for replay and which is
   the CAS key for refusal.
2. After running: confirm the learner reads `exactly_one_despite_the_
   replay_above: true` and connects it to the SAME class of proof Chapter 7
   already taught (one canonical row, enforced at the SQLite boundary, not
   a preflight check).
3. On `no_completion_table_exists`: confirm the learner can articulate WHY
   this chapter bothers to check for an absence, rather than dismissing it
   as an obvious or unnecessary assertion.
4. Have the learner actually run `tests/test_pilot.py`'s own two-connection
   concurrency tests and read the assertions, connecting them back to this
   chapter's own single-process replay as the stronger property being
   proven elsewhere.

## Discussion prompts

- "This chapter's own exercise never calls `start_pilot` with a SECOND,
  DIFFERENT pilot identity — only a replay of the same one. Where is the
  fail-closed refusal property actually proven, and why wasn't it also
  shown directly in this chapter's own exercise?" (Answer: it IS
  demonstrable safely — a disposable second identity could be added — but
  the exercise deliberately keeps to one clean success-path narrative;
  the refusal property is proven in `tests/test_pilot.py` instead.)
- "What would the governance receipt described in the governing SOW's
  section 4 need to cite, given what this chapter's own `pilots` row
  actually stores? Why can that receipt not be written by this chapter's
  own exercise, or by anything in this unit's implementation?"
- "This is the last chapter. What would Chapter 13 need to teach, if this
  book continues past Unit 11? Name at least one mechanism this book has
  now built the vocabulary for but not yet exercised."

## Facilitation timing

Roughly 25-30 minutes: 10 minutes on the disposable-identity discipline and
why it is structural, not conventional, 10 minutes on the exercise output
and the `sqlite3` cross-check, 5-10 minutes connecting to the real
two-connection tests and closing the book's own overall arc.

## Exercise debrief and assessment

A learner has landed this chapter if they can state, unprompted, the exact
difference between what this chapter's own database proves ("a pilot
started, exactly once, durably") and what it does not and cannot prove ("the
pilot is going well" or "the pilot has finished") — and can name the
specific table (or its absence) that makes each of those distinctions
checkable rather than merely asserted.
