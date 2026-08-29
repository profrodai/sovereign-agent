# Chapter 3 — The actor is not a model

## Learning objective

Understand why swapping the intelligence behind an actor does not change who is
accountable — and why a provider therefore cannot approve its own work.

An **actor** is a governed identity with a role and authority. A **provider**
is an external intelligence CLI: `scripted`, `claude`, `codex`, or `cursor`.
Changing intelligence must not silently change who may act.

## Exercise

1. Inspect `operator-course` in `sovereign.toml`. Record its id, role,
   authority, and provider.
2. Run the exercise with a provider you have installed:

   ```bash
   python book/ch03_actor_is_not_a_model/solution.py \
     --root /tmp/andrea-ch03 --provider claude
   ```

3. Inspect the first scripted receipt under
   `/tmp/andrea-ch03/.sovereign/runs/*/receipt.json`.
4. Observe the governed `actor.provider_rebound` event. The Principal changes
   the provider binding; the actor id, role, and authority remain unchanged.
5. If the live CLI is absent or cannot prove required print/stream flags, read
   the refusal. Installing a model does not bypass the gate.
6. If it runs, inspect `provider_session_ref`, `provider_usage`, normalized
   events, and the validated `.sovereign-out/report.json`.
7. Replace `--provider claude` with `codex` or `cursor`. Cursor is an equal
   adapter, not a documentation bridge.

The provider receives one production-built assignment envelope containing the
actor, authority, SOW, disposable workspace boundary, output paths, and exact
`ActorReport` schema. The adapter only translates that envelope into its CLI.

## Expected observations

Running the exercise prints a JSON summary. The line that matters:

```text
"identity_unchanged": true
```

Before and after the rebind, `operator-course` keeps the same id, the same
role, and the same authority list. Only `provider` changes — from `scripted`
to `claude`, `codex`, or `cursor`.

Confirm the governed record of the change:

```bash
sqlite3 /tmp/andrea-ch03/.sovereign/organization.db \
  "SELECT kind FROM events WHERE kind = 'actor.provider_rebound';"
```

Expected: one row. Rebinding is an act the organization records, performed by an
actor with ruling authority — not a config edit that happens quietly.

If a live CLI is missing or cannot prove its required flags, you will see a
refusal instead of a run. That is the correct outcome: capability claims come
from probing the installed CLI, and an unprovable capability fails closed.

## Why a provider cannot approve its own work

The provider that proposed the restock in Chapter 0 runs *behind*
`operator-course`. Acceptance is refused for every actor that performed work,
and performers are derived from the assignments in the ledger — not supplied by
the caller. So the intelligence that did the work cannot become the authority
that blesses it, no matter which model is bound to the actor.

Swap `claude` for `codex` and the governance does not move. That is the point.

## Learner verification command

```bash
python -m pytest tests/test_actors_and_mailbox.py tests/test_providers.py -q
```

Expected: all pass. These prove actor identity survives a provider rebind, that
authority cannot be self-granted, and that adapters build argument arrays rather
than shell strings.

## Isolation warning

`--workspace` selects a directory; it is not a sandbox. Cursor's CLI has file
and shell tools. Chapter 3 relies on a disposable Sovereign Agent run
workspace, not an invented provider security guarantee. Stronger workspace
lifecycle policies arrive in Unit 7.

Codex receives `--sandbox workspace-write` when the actor has
`write_workspace` authority because even a domain-read-only assignment must
write its mandatory report. The live read-only smoke verifies that tracked
domain files remain unchanged; it does not make the report directory
unwritable.

The same authority becomes Claude `--permission-mode acceptEdits` and Cursor
`--force`, but only when those exact controls are present in the installed
CLI's help output. These flags authorize writes inside the disposable run
workspace; they do not expand the actor's organizational authority.

## Explain it back

1. Which fields stayed constant after rebinding the provider?
2. Why is a provider session id evidence about continuity but not actor
   identity?
3. What should happen if a CLI exits zero but omits its terminal event or
   `report.json`?
4. Why may an unknown valid event be retained while malformed JSON must fail
   the receipt?
5. In your own words: what is the difference between an actor and a provider?
6. `operator-course` is rebound from `scripted` to `claude`. Who is accountable
   for the work afterwards, and how would you show that from the ledger?
7. Why does deriving the performer from assignments — rather than accepting it
   as an argument — matter for keeping a provider from approving itself?

## Production correspondence

| Textbook concept | Production responsibility |
| --- | --- |
| Actor id, role, authority | Governed organizational identity and policy |
| Provider binding | Replaceable intelligence runtime |
| Assignment envelope | Bounded work contract and output schema |
| Disposable run directory | Isolation boundary owned by Sovereign Agent |
| Provider session reference | Runtime continuity evidence, never identity |
| Terminal event + report | Protocol completion plus validated work claim |
| Receipt and SHA-256 sidecar | Canonical durable execution evidence |

## Live smoke tests

Default tests use faithful, redacted fixtures and fake executables. Probes are
opt-in and submit no work:

```bash
python -m pytest -q -m live
```

Credentialed assignment smokes require a second explicit gate. They run one
read-only and one workspace-write assignment per installed provider and may
consume provider credits (typically a short prompt each):

```bash
SOVEREIGN_AGENT_LIVE_ASSIGNMENTS=1 python -m pytest -q -m live
```

The fixture repository is disposable, and each test proves its trunk commit
did not move.

Next: [Chapter 4 — Work stays inside its boundary](../ch04_work_stays_inside_its_boundary/README.md)
