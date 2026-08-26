# Ruling: an outcome is a standing condition; a SOW is a unit of work

- **id:** `ruling-2026-08-26-outcomes-are-conditions-sows-are-work`
- **decided:** 2026-08-26
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x acceptance semantics
- **status:** ACTIVE

## The question

Raised by Sparring on PR #24 as a design fork deserving a ruling rather than a
patch. Reproduced in full:

```text
Week 1: real work, real restock, accepted legitimately.
Week 2: an assignment runs and does NOTHING. Inventory is still stocked
        from week 1. *** WEEK 2 ACCEPTED ***
```

Is week 2 correct or incorrect?

- If "keep the tea jar stocked" is a **standing condition**, week 2 is correctly
  accepted — the jar is stocked — and the SOW, assignment and receipt merely
  imply work that was not required.
- If it is a **unit of work**, week 2 must refuse, and the checks need an
  execution-scoped question beside the world-fact one.

Sparring observed that `checks.py` takes the first position while every
governance record takes the second.

## Holding

**Both readings are correct, about different objects.** The records say so, and
were consulted rather than reasoned about:

| Object | Field | Shape |
| --- | --- | --- |
| `Outcome.desired_state` | "On-hand tea is at or above the reorder point…" | a state of the world — **condition** |
| `StatementOfWork.deliverables` | `["report.json"]` | a thing produced — **work** |
| `StatementOfWork.done_when` | "Evidence exists and a different actor has reviewed it." | a completion test — **work** |

1. **An outcome is a standing condition.** It names how the world should be. It
   can be true without anyone doing anything, and it can stop being true without
   anyone doing anything.
2. **A SOW is a unit of work.** It names a deliverable and the test for having
   delivered it. It is done or not done; it does not "remain true".
3. **Acceptance asserts both, separately.** To accept an outcome the system must
   establish:
   - **(a) the condition holds now** — the deterministic world-fact checks,
     re-executed at acceptance time; and
   - **(b) the bound execution contributed** — the assignment being accepted on
     actually produced an effect, read from the structured `effects` table.
4. **Neither implies the other, and the failure of each is reported
   differently.** (a) failing means *the world is wrong*. (b) failing means *this
   work did nothing*. Collapsing them is the defect this ruling exists to fix:
   week 2 satisfied (a) and failed (b), and was accepted anyway while presenting
   a SOW, an assignment, a receipt and a review as though they evidenced the work
   that produced the stocked shelf.
5. **`ACCEPTED` continues to mean the outcome is true now.** This ruling does
   not weaken that; it adds a second, independent requirement. An outcome whose
   condition holds but whose execution did nothing is not accepted — not because
   the world is wrong, but because the record would misattribute it.

## What this rules out

- Making the world-fact checks execution-scoped. That would lose the property
  Unit 6.5 exists to establish: that `ACCEPTED` means the claim is *currently*
  true, not that it was true once when a check happened to run.
- Deleting the governance records for outcomes that need no work. The right
  answer to "no work was required" is a refusal that says so, not a SOW quietly
  taking credit.

## Consequences in this repository

- `effects` carries `outcome_id` as a structured foreign key, so the effect edge
  can be followed relationally rather than inferred from world state.
- Acceptance follows that edge and refuses when the bound execution contributed
  no effect, with a message naming the real reason.
- Proof selection stops using "the newest assignment row" as an implicit rule.
  That was never a proof; it was an ordering accident, and it cannot model an
  outcome with several SOWs.

## Verification

`tests/test_causal_binding.py` reproduces the week-1/week-2 sequence and asserts
week 2 is refused while the condition still holds — proving the two requirements
are genuinely independent rather than one dressed as two.
