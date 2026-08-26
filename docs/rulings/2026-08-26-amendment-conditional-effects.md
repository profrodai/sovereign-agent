# Ruling amendment: effects are required where a SOW declares them

- **id:** `ruling-2026-08-26-amendment-conditional-effects`
- **decided:** 2026-08-26
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x acceptance semantics
- **status:** ACTIVE
- **amends:** [`ruling-2026-08-26-outcomes-are-conditions-sows-are-work`](2026-08-26-outcomes-are-conditions-sows-are-work.md)

## Why this amendment exists

The amended ruling holds, in its acceptance requirements:

> **(b) the bound execution contributed** — the assignment being accepted on
> actually produced an effect

and rules out "deleting the governance records for outcomes that need no work",
saying the right answer is "a refusal that says so".

The implementation then introduced `StatementOfWork.required_effect_kind`, under
which a SOW with no declared effect completes without changing the world — and a
test pins that behaviour. **The code overturned a holding without changing the
holding.**

Raised in review of PR #24. The reviewer was right twice: the conditional model
is better, *and* changing the code instead of the ruling is the wrong way round.
A ruling the code contradicts is worse than no ruling, because it teaches a
learner that the governance records are decoration — the exact failure the Unit 0
branch amendment exists to correct, reproduced inside Unit 6.5.

## What was wrong with the original holding

It assumed every SOW is effectful. Investigations, reports and reviews are
legitimate units of work that deliver without moving inventory. Requiring a
world-changing effect from all of them would either forbid such SOWs or invite
fake effects to satisfy the check — and a system that rewards manufacturing an
effect to pass a gate has learned the wrong lesson from this unit.

## Amended holdings

Acceptance of an **outcome** requires all of the following, checked separately:

1. **Every SOW has a completed execution** with a successful receipt whose
   canonical record and indexed columns agree.
2. **Every SOW produced its declared deliverables.** For a non-effectful SOW the
   deliverable *is* the proof: outcome-level store checks say nothing about
   whether a report was written. Judging an investigation by an inventory check
   would be a check named for one fact measuring another — this unit's signature
   defect, one scope up.
3. **Every SOW has an independent review of its own current verification**,
   bound relationally: `verification.sow_id → assignment.sow_id → the reviewed
   SOW`.
4. **Only a SOW declaring `required_effect_kind` must have changed the world**,
   and then its own execution must have produced an effect of exactly that kind.
   Supersedes holding (b) of the amended ruling, which required this of every
   SOW.
5. **The outcome's condition holds now**, re-executed at acceptance time.
   Unchanged.

## What is unchanged

- An outcome is still a standing condition; a SOW is still a unit of work.
- `ACCEPTED` still means the outcome is true *now*.
- "No work was required" still refuses — but the refusal is now precise: a SOW
  that declares an effect and produces none is refused for that, while a SOW
  that never claimed to change the world is judged on its deliverable instead.

## Verification

- `test_a_sow_with_no_declared_effect_need_not_change_the_world` — holding 4.
- `test_condition_true_but_no_effects_exist_at_all_is_refused` — an effectful
  SOW that changed nothing is still refused.
- `Organization._require_deliverables` and its refusal — holding 2.
- `test_core_and_the_truth_verifier_agree_on_a_multi_sow_organization` — the
  core and the release oracle enforce the same amended model.
