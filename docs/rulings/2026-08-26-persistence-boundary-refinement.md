# Ruling: the persistence boundary, refined

- **id:** `ruling-2026-08-26-persistence-boundary-refinement`
- **decided:** 2026-08-26
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x persistence and the governance/operational split
- **status:** ACTIVE
- **amends:** [`ruling-2026-08-25-educational-reset`](2026-08-25-educational-reset.md)

## Why this is its own ruling

This refinement was first recorded inside the amendment that moved `main` to the
1.x line. Those are two unrelated decisions — a branch policy and a data
doctrine — and folding them into one authority record makes it impossible to
cite, supersede, or argue with either separately. Raised in review of PR #24 and
corrected here.

## The holding being refined

The educational-reset ruling states:

> JSON/TOML is canonical for committed governance; SQLite is canonical for
> operational state; Markdown is generated.

Read literally, that is false of this codebase. Deleting the entire
`governance/` directory leaves the organization fully working, because outcomes
and SOWs are read from SQLite and the JSON is never read back.

## Holdings

1. **"Governance" names two different things**, and the original line collapsed
   them:
   - *Committed governance definitions* — actors in `sovereign.toml`, rulings in
     `docs/rulings/` — are canonical in files and are genuinely read back.
     Editing `sovereign.toml` changes behaviour on the next open.
   - *Governance execution records* — the state of an outcome as work moves
     through it — are canonical in **SQLite**, because they change while the
     organization runs.
2. **`governance/**/*.json` is a derived projection**, not a source. It is
   written for inspection and diffing and never read back.
3. **Markdown is generated** and never authoritative.
4. **Runtime rulings are operational records.** `Organization.rule()` stores a
   ruling in SQLite and projects files from it. That is a *runtime organization
   ruling* — a governed decision made by an actor inside a running
   organization — and it is distinct from the *repository product rulings* in
   `docs/rulings/`, which humans write, review, and commit. Both are called
   "ruling"; only the second is canonical in files. The teaching text must keep
   these apart.
5. **No cross-resource atomicity is claimed.** SQLite and the filesystem cannot
   be written in one transaction. The ledger is the authority; projections are
   rebuildable from it and reconcile *toward* it.
6. **Verification of projections must be pure.** Detecting drift and repairing
   it are separate acts. A verifier that repairs while checking reports success
   about a state it created.

## Consequences

- `docs/persistence-boundary.md` is the explanatory text for this ruling.
- `scripts/verify_projections.py` checks by default and repairs only under
  `--reconcile`.
- Trust boundary, stated plainly: everything here protects the ledger from
  mistakes and ordinary tools, not from an actor with arbitrary write access to
  the database file.
