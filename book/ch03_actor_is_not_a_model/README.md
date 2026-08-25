# Chapter 3 — The actor is not a model

## Andrea's goal

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

## Isolation warning

`--workspace` selects a directory; it is not a sandbox. Cursor's CLI has file
and shell tools. Chapter 3 relies on a disposable Sovereign Agent run
workspace, not an invented provider security guarantee. Stronger workspace
lifecycle policies arrive in Unit 7.

## Reflection

1. Which fields stayed constant after rebinding the provider?
2. Why is a provider session id evidence about continuity but not actor
   identity?
3. What should happen if a CLI exits zero but omits its terminal event or
   `report.json`?
4. Why may an unknown valid event be retained while malformed JSON must fail
   the receipt?
5. In your own words: what is the difference between an actor and a provider?

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
