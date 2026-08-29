# Instructor note — Chapter 3: The actor is not a model

## Teaching intent

This chapter separates two ideas that are easy to collapse into one:
accountability (the actor, a governed organizational identity) and
capability (the provider, a swappable intelligence CLI). The teaching payoff
is the `identity_unchanged: true` line — a learner needs to see, not just
hear, that rebinding `scripted` to `claude`/`codex`/`cursor` changes nothing
about who is authorized or accountable. This is also the chapter where the
book's stance on provider sandboxing gets stated honestly (`--workspace` is
not a sandbox), which Chapter 4 then makes checkable.

## Prerequisite knowledge

Chapter 2's no-self-approval property (performer derived from the ledger,
never supplied by the caller) is the direct ancestor of this chapter's
central claim: "the provider that proposed the restock cannot become the
authority that blesses it, no matter which model is bound to the actor." A
learner who has not internalized Chapter 2's derivation logic will find this
chapter's argument circular rather than a natural extension.

## Likely misconceptions

- **"A more capable model gets more authority."** This is the single
  misconception this chapter exists to prevent. Point directly at the
  `identity_unchanged` line and the `actor.provider_rebound` event — the
  Principal has to explicitly perform a governed rebind act, it is not a
  config edit that silently expands what an actor can do.
- **"`--workspace` in Claude/Cursor/Codex is a sandbox."** It is explicitly
  not, for two of the three providers, and this chapter says so in its own
  "Isolation warning" section. If the learner has used any of these CLIs
  directly before, they may have an intuition that the flag means
  containment — correct this before Chapter 4, which depends on the learner
  already accepting that the boundary needs to be CHECKED rather than
  trusted.
- **"If the live CLI is missing, the exercise is broken."** A refusal here is
  the CORRECT outcome, not a failure of the exercise — capability claims come
  from probing the installed CLI, and an unprovable capability fails closed.
  A facilitator running this live with no provider CLIs installed should
  treat that as a teaching opportunity, not an inconvenience to route around.

## Observation checkpoints

1. After running with `--provider scripted` (or any live provider available):
   confirm the learner reads `identity_unchanged: true` and can say what
   stayed the same versus what changed (only `provider`).
2. After the `actor.provider_rebound` event query: confirm the learner
   notices this is exactly ONE row — rebinding is a recorded governed act,
   not a silent state change.
3. If a live provider is unavailable and the exercise reports a refusal:
   confirm the learner reads the refusal message rather than treating the
   exercise as having failed to run.

## Discussion prompts

- "Why does the SAME authority list produce different concrete flags across
  providers (`--permission-mode acceptEdits` for Claude, `--force` for
  Cursor, `--sandbox workspace-write` for Codex)? What does that tell you
  about where 'authority' actually lives in this design?"
- "If you were choosing a provider for a task involving real money, would
  you weight 'more capable model' or 'stronger sandbox' more heavily — and
  does this chapter's design let you have both independently?"

## Facilitation timing

Roughly 30-40 minutes guided, more if a facilitator wants to actually run
against a live installed provider CLI (add 10-15 minutes and budget for
possible refusals if capability probing fails — treat that as content, not
a delay). If no live CLI is available, the scripted-only run plus discussion
fits comfortably in 25 minutes.

## Exercise debrief and assessment

A learner has landed this chapter if they can explain, unprompted, why a
provider cannot approve its own work — connecting directly back to Chapter
2's derivation-from-the-ledger mechanism rather than restating it as an
unrelated rule. This is Andrea Alpha evaluation Task 4's first sub-question
verbatim (`docs/andrea-alpha-evaluation.md`): "why is an actor not a
provider?" — looking for accountable identity vs. swappable intelligence,
not a memorized definition.
