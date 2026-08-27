# Ruling: Unit 7 is workspace lifecycle; Unit 9 owns the pulse pipeline

- **id:** `ruling-2026-08-27-unit7-is-workspaces-not-pulse`
- **decided:** 2026-08-27
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x, Unit 7
- **status:** ACTIVE

## There was no conflict of authorities. There was a transcription error.

This ruling's first draft framed this as two sources disagreeing and weighed
which should win. That framing was wrong, and the corrected version says so
rather than quietly fixing the wording: the deciding fact was already ratified
and in-tree the whole time, and the first draft never grepped for it.

`docs/sows/sovereign-agent-v1-educational-control-plane.md`, sequencing
amendment 5, ratified by the principal and committed to `main` at `43d1dff`:

> "**Unit 9 is the first fully proactive milestone:** sale -> inventory signal
> -> deterministic wake gate -> pulse -> replenishment work created without a
> human prompt -> Scripted Operator -> evidence -> Sparring -> acceptance."

That is the sentence the book's ch00 was written against.

This ruling's first draft cited the handover as
`org/projects/sovereign-agent/sow/v1-educational-reboot/...-sparring-handover-units-0-6.md`
— a corpus-relative path that does not resolve inside this repository. That was
a ghost citation inside a ruling written to resolve a citation dispute. The
correct reference: the source is **external to this repository**, held in the
corpus at `rodriveracom/org-zeroemployeeorg`, path
`projects/sovereign-agent/sow/v1-educational-reboot/v1-educational-reboot-SOW-01-sparring-handover-units-0-6.md`,
committed there at `07ec2081`. It transcribed the pipeline from amendment 5
under the wrong unit number, as Unit 7 rather than Unit 9 — a copying error in
a working handover note, not a second ratified position. The corpus-side
correction is filed at
[org PR #62](https://github.com/rodriveracom/org-zeroemployeeorg/pull/62),
"SOW-01 correction: Unit 7 is workspace lifecycle; proactive pipeline is Unit 9."

## Holding

**Unit 7 is workspace lifecycle. Unit 9 owns the proactive pipeline — sale,
signal, wake gate, pulse, replenishment — exactly as amendment 5 states.**

This was never open. The book's ch00 (`book/ch00_first_shift/README.md:116-118`)
and `docs/sows/sovereign-agent-v1-educational-control-plane.md:59-61` already
agreed; only the handover transcription disagreed with both. This ruling exists
to put the correction on the record and to stop implementation until the
transcription error is fixed at its source, not to choose between two rulings
that were never in tension.

## What Unit 7 is, per the grounded proposal

The only in-tree 1.x content naming what Unit 7 contains is
`book/ch03_actor_is_not_a_model/README.md:89`: "Stronger workspace lifecycle
policies arrive in Unit 7." That, plus the scope investigation's findings, is
the basis for Unit 7:

1. **Reclaim tied to assignment terminal state.** `organization.py` allocates a
   run workspace per assignment (`~line 245`) and nothing in the package ever
   reclaims it.
2. **`Actor.workspace_policy` is enforced.** `models.py` declares the field and
   nothing in the package reads it. The operator ruling here is enforcement, not a
   choice between enforcing and deleting it: Unit 7 must make it read and honored.
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
grep -n "Unit 9 is the first fully proactive milestone" docs/sows/sovereign-agent-v1-educational-control-plane.md
grep -rn "workspace_policy" src/sovereign_agent/models.py
python scripts/verify_curriculum.py
```

The first three confirm the book, the ratified sequencing amendment, and Unit
7's workspace citation all already agreed. The fourth shows the field this
ruling requires Unit 7 to enforce. The curriculum gate is what keeps the book
itself honest going forward.
