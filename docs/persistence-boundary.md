# The persistence boundary: what is canonical, what is derived

The 1.x educational-reset ruling states the doctrine in one line:

> JSON/TOML is canonical for committed governance; SQLite is canonical for
> operational state; Markdown is generated.

That line is nearly right, and reading it literally would teach you something
false about this codebase. This note records the refined boundary and the
experiment that forced the refinement, as an amendment to the doctrine rather
than a quiet re-reading of it.

## What the code actually does

Two claims, each checkable in under a minute.

**Claim 1 — deleting `governance/` does not harm the organization.**

```console
sovereign-agent demo store --mode simulated --root /tmp/store
rm -rf /tmp/store/governance
python -c "from sovereign_agent.organization import Organization; \
o=Organization('/tmp/store'); \
print(o.status_text(o.db.connection.execute('select id from outcomes').fetchone()['id']))"
```

The status still prints. Outcomes and SOWs are read from SQLite
(`Organization._outcome`, `Organization.sows_for`). Nothing in the codebase ever
reads `governance/outcomes/**/outcome.json` back. It is written and never
consulted.

**Claim 2 — editing `sovereign.toml` does change behaviour.**

Change a `provider = ` line and reopen the organization; the actor comes back
with the new provider. `load_actors` parses that file on every open.

## The refined boundary

| Data | Canonical home | Why |
| --- | --- | --- |
| Actor definitions, roles, providers | `sovereign.toml` | Read on every open. Editing it changes behaviour. Committed, reviewable, diffable. |
| Repository product rulings | `docs/rulings/*.md` | Human decisions, committed and reviewed. Canonical in files. |
| Runtime organization rulings | **SQLite** (`rulings`), projected to `governance/rulings/` | `Organization.rule()` records a decision made by an actor inside a running organization. Operational state; the files are a projection. |
| Outcomes, SOWs, assignments, evidence, acceptance | **SQLite** | Read on every operation. These carry mutable execution state. |
| Inventory, cash, events, signals, leases | **SQLite** | Operational state by definition. |
| `governance/**/*.json` | **derived projection** | Written for inspection and diffing. Never read back. |
| `governance/**/*.md`, chapter output | **generated** | Never authoritative. Regenerate freely. |

So the doctrine is refined, not overturned:

- *Committed governance definitions* — the actors and rulings a human writes and
  reviews — are canonical in TOML/Markdown, and they are genuinely read back.
- *Governance execution records* — the state of a particular outcome as work
  moves through it — are canonical in SQLite, because they change while the
  organization runs.
- The JSON under `governance/outcomes/` is the **inspectable projection** of
  those records, not their source.

The original line collapsed those two senses of "governance". Splitting them is
the amendment.

## The limit you must not lie about

SQLite gives you one transaction across many tables. It does **not** give you a
transaction across SQLite *and* the filesystem.

`Organization.accept` commits the ledger, and only then calls `project_outcome`
to write files. If the process dies in between — or the disk fills — the ledger
says `ACCEPTED` and the files on disk do not. That is a real, reachable state,
and it is why the code carries this comment:

```python
# NOT part of the transaction above: see docs/persistence-boundary.md.
project_outcome(self.root, outcome, sows)
```

`atomic_write` (in `files.py`) makes each individual file appear atomically, via
write-temp-then-rename. That is per-file atomicity, and it is worth having. It
is not cross-resource atomicity, and calling it that would be the same species
of lie as an `ACCEPTED` outcome with an empty shelf.

**The rule that follows:** SQLite is the authority. Files are rebuildable from
it. When they disagree, the database wins and the projection is regenerated —
never the reverse. Drift detection therefore reconciles *toward* the database.

A stronger property (an outbox, replayed on next open) is buildable, and is
deliberately out of scope for Unit 6.5. The honest half-door is labelled rather
than disguised.


## A second limit: the ledger is inside the trust boundary

Append-only protection covers `events`. It does not cover every table, and it
cannot. `outcomes` has no triggers, and `outcome.subject` — the field that says
which SKU the acceptance checks are about — is a value inside that row's JSON.

Sparring demonstrated the consequence. Rewriting that single field to point at a
different, well-stocked product makes all three checks pass **coherently**, and
the outcome accepts while the real shelf is empty:

```text
UPDATE outcomes SET record = <subject: "SKU-TEA" -> "SKU-DECOY"> WHERE id = ...
-> all three checks PASS, ACCEPTED, while SKU-TEA on_hand=2 < reorder_point=3
```

This is worth naming precisely, because it is the *exception* to how the check
registry normally protects you. Tamper with inventory directly and you are
caught: `cash_reconciles` and `replenishment_event_exists` cross-check inventory
against the event log, so a single edit puts the checks in contradiction with
each other. Subject tampering is the one single-field write that moves all three
checks together onto a world where they are genuinely true — so the mutual
cross-checking that provides the real guarantee is bypassed rather than tripped.

It requires raw write access to the database, and doctrine already places SQLite
inside the trust boundary: anyone who can write arbitrary rows can rewrite the
organization's memory. But "ACCEPTED means the outcome is true now" is exactly
the claim this falsifies, so it is recorded here rather than left for a reader
to discover.

A related property, verified rather than assumed: `DROP TRIGGER` succeeds from
an outside connection, and reopening does not restore the trigger, because the
migration that created it is already stamped as applied. This is true of the
migration-2 guards as much as the migration-3 one, so it is a pre-existing
property of the trust boundary rather than something the append-only work
introduced. It is the same statement as above in a different key: everything
here protects the ledger from *mistakes and ordinary tools*, not from an actor
with arbitrary write access to the database file.

**What the digest does and does not cover.** Each check now digests its own
observation, and every store check's observation includes the `sku` it was run
against — so evidence written about one SKU cannot be read as evidence about
another. What the digest cannot see is a change to `outcome.subject` itself:
retargeting the outcome makes verification *re-run* against the new subject and
produce fresh, internally consistent evidence. The gap is not a missing field in
the digest; it is that `outcomes` rows are mutable by anyone with database write
access, and no digest of a check's own reads can detect the question changing
underneath it.

Closing it needs the outcome record itself to be tamper-evident — signing or
hash-chaining governance rows — which is a larger change than Unit 6.5 should
carry. Named here as the honest next step rather than implied to be taken.

## How to see the drift for yourself

```console
sovereign-agent demo store --mode simulated --root /tmp/store
echo "hand-edited nonsense" >> /tmp/store/governance/outcomes/*/README.md
python scripts/verify_projections.py /tmp/store
```

The verifier reports the stale projection and exits non-zero. Regenerating from
the ledger fixes it.
