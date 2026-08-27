# Ruling: Unit 7 is workspace lifecycle; Pulse stays out until Unit 9

- **id:** `ruling-2026-08-27-unit7-is-workspaces-not-pulse`
- **decided:** 2026-08-27
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x, Unit 7
- **status:** ACTIVE

## The conflict

Two sources in this project's own history disagreed about what Unit 7 is.

`book/ch00_first_shift/README.md` — part of the executable textbook, gate-verified
by `scripts/verify_curriculum.py`, checkpoint-tagged, and merged as part of the
Units 0–6 acceptance record — tells the reader:

> "The organization has no heartbeat yet. It cannot notice that stock fell, or
> decide on its own that the tea needs reordering... That capacity... is called
> **Pulse**, and it does not exist yet. It arrives in Unit 9. Nothing in this book
> simulates it, and no event in the ledger you just inspected pretends otherwise.
> You can check that claim the same way you checked the others."

A Sparring handover SOW filed in the corpus
(`org/projects/sovereign-agent/sow/v1-educational-reboot/...-sparring-handover-units-0-6.md`)
instead describes Unit 7 as "the first proactive milestone: sale -> inventory
signal -> deterministic wake gate -> pulse -> replenishment."

These cannot both be true. If Unit 7 means building Pulse, the book — already
reviewed twice, accepted, and shipped to readers — teaches a false claim about
its own software, and does so while instructing the reader to independently
verify a falsehood.

## Holding

**The book governs. Unit 7 is workspace lifecycle. Pulse remains out of scope
until Unit 9.**

This is not a new decision — it is the original mission brief holding: *"do not
simulate a Pulse event before Unit 9"* was stated directly by the operator before
any Unit 6.5 work began, predates the handover SOW, and was never amended. The
handover memo describing Unit 7 as proactive-wake is superseded by that standing
instruction and by the book it was never reconciled against.

## Why the book wins over an internal handover memo

1. **The book is the accepted artifact; the handover is a working note.** The book
   was gate-checked, independently reviewed by two seats across many rounds, and
   merged into the record this project now calls ACCEPTED. The handover SOW was
   never reviewed against it and was written for a different audience —
   coordinating a review, not fixing a scope.
2. **Reviewer silence is evidence, not proof, but it counts.** Both reviewers who
   approved the book's final state had every opportunity to flag ch00's Pulse
   claim as premature or wrong. Neither did. The claim is also self-checking —
   the chapter invites the reader to verify it — which is a stronger form of
   claim than an unreviewed sentence in a handover doc.
3. **A design memo not in this repository cannot silently override one that is.**
   `docs/units-0-6-contract.md` already establishes this principle for the 1.x
   SOW itself: "The full design memo lives with the originating stream... An
   acceptance record that points at a document not in the tree is the same
   defect this project exists to remove, one level up." The same reasoning
   applies to a handover SOW that contradicts an in-tree, gate-verified claim.

## What Unit 7 is, per the grounded proposal

The only in-tree 1.x content naming what Unit 7 contains is
`book/ch03_actor_is_not_a_model/README.md:89`: "Stronger workspace lifecycle
policies arrive in Unit 7." That, plus the scope investigation's findings, is
the basis for Unit 7:

1. **Reclaim tied to assignment terminal state.** `organization.py` allocates a
   run workspace per assignment (`~line 245`) and nothing in the package ever
   reclaims it.
2. **`Actor.workspace_policy` is either enforced or removed.**
   `models.py` declares the field; nothing reads it.
3. **The workspace boundary becomes detectable, not merely declared.** Only the
   `codex` provider has real OS-level containment (`--sandbox workspace-write`);
   `cursor`'s `--workspace` is explicitly documented as "not a sandbox";
   `claude` and `scripted` have none.
4. **`_require_deliverables` gets a traversal check.** It currently joins an
   unvalidated `deliverable` string onto a path with no check.
5. **All four providers held to the same rule, with no live credential.**
   Credentialed smokes remain Unit 12's concern, not Unit 7's.

## Explicit non-scope

- **Pulse, proactive waking, any simulated Pulse event** — Unit 9. Untouched by
  this ruling in the other direction too: this ruling does not schedule Pulse
  work, only clears the conflict blocking Unit 7.
- **Multi-process fencing, supervisor, hard-kill recovery** — Unit 8.
- **Credentialed Claude/Codex/Cursor smokes** — Unit 12. Never run, not claimed
  here.

## How to check this ruling against the repository

```console
grep -n "does not exist yet. It arrives in" book/ch00_first_shift/README.md
grep -n "lifecycle policies arrive in Unit 7" book/ch03_actor_is_not_a_model/README.md
grep -rn "workspace_policy" src/sovereign_agent/models.py
python scripts/verify_curriculum.py
```

The book's Pulse claim and Unit 7's workspace citation are what this ruling
resolves between; the curriculum gate is what keeps the book itself honest going
forward.
