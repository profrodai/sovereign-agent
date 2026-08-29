# Instructor note — Chapter 4: Work stays inside its boundary

## Teaching intent

This chapter turns a sentence from Chapter 3 ("`--workspace` selects a
directory; it is not a sandbox") into something checkable. The teaching
payoff is `boundary_scope` — a value on the report, not a docstring the
learner has to trust — and the honest limit it names: the workspace itself
and the SQLite ledger are structurally invisible to the check, on purpose,
and `violated: False` never means more than "nothing changed in what this
check can see." This chapter is a direct application of Chapter 2's whole
thesis (a claim needs a check behind it) to a new domain: filesystem
isolation.

## Prerequisite knowledge

Chapter 3's actor/provider distinction, specifically the isolation warning
that some providers have no OS-level sandbox. A learner who has not accepted
that gap yet will treat this chapter's detection mechanism as redundant
rather than necessary.

## Likely misconceptions

- **"A clean boundary report means the provider was contained."** It means
  no tracked file OUTSIDE the workspace changed during THIS ONE invocation —
  detected, not prevented. If a provider's subprocess is still running after
  the after-snapshot, this check says nothing about what it does next.
  Correct this explicitly; it is the single most easily overclaimed fact in
  the chapter.
- **"`safe_join` refusing an absolute path that would resolve inside root is
  overly strict."** Walk through why: acceptance would then depend on where
  the caller's filesystem happens to put things, which is not a property
  about the INPUT's shape — it's an accident of deployment. The function's
  contract is "a workspace-relative path," and an absolute string is never
  one, regardless of where it lands.
- **"Reclaim deletes everything in the workspace when the policy is
  `temporary_directory`."** It preserves the receipt and `.sovereign-out` —
  have the learner actually read the before/after directory listings in the
  exercise output rather than assuming from the policy name alone.

## Observation checkpoints

1. After the `safe_join` results: confirm the learner notices the absolute
   path is refused with a DIFFERENT reason (`path_traversal`, "must be
   relative, not absolute") than the `..`-traversal case, even though both
   are ultimately about escaping the root.
2. After the boundary violation section: confirm the learner can name both
   things `boundary_scope` explicitly excludes (the workspace itself, the
   SQLite ledger files) without looking them up.
3. After the reclaim section: confirm the learner checks `receipt_preserved`
   and `output_dir_preserved` are both `true` while `scratch_removed` is
   also `true` — three separate facts, not one blanket "cleaned up."

## Discussion prompts

- "Only Codex's adapter gives real OS-level containment. What would you tell
  a team relying on Claude or Cursor for workspace-write assignments about
  what this chapter's boundary check does and does not protect them from?"
- "A dirty boundary report does not block the assignment from completing —
  it's recorded, not enforced. Do you agree with that design choice for a
  system handling real money? What would you change, and what would you
  risk breaking?"

## Facilitation timing

Roughly 30 minutes guided: 10 minutes on `safe_join`'s refusal shapes, 10
minutes on the boundary snapshot/diff mechanism and what `boundary_scope`
excludes, 10 minutes on reclaim as a policy choice plus "Explain it back."

## Exercise debrief and assessment

A learner has landed this chapter if they can state, unprompted, that
`violated: False` is a claim about what the check COULD see, not an
unqualified guarantee — this is the chapter's own central correction (review
round two's own finding) and the property most likely to get overclaimed by
a learner moving quickly. If a learner describes the boundary check as
"proving the provider was sandboxed," they have not yet landed this chapter;
revisit the "Why detection, not prevention" section before moving on.
