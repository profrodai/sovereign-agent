# Lab 03 — Change the provider, not the actor

## Challenge

Use the real production `Actor`, `ROLE_AUTHORITY`, and provider capability contract. Rebind an actor's mutable `provider` field while proving that its id, role, and descriptive authority list remain unchanged. Then prove that editing that list cannot self-grant role authority and that an adapter must refuse an unproven capability.

## Production map

Production stores `provider` directly on `Actor`; there is no separate frozen binding object. `Organization.rebind_actor` changes that field under ruling authority. Authorization is decided by `ROLE_AUTHORITY`, while `require_proven` gates provider invocation using live probe evidence.

## Run it

Copy the starter before editing, then run this lab's checker against your copy:

```bash
cp starter.py work.py
python -c 'from pathlib import Path; import check, work; print(check.check(work, Path(".lab-run")))'
```

Implement `exercise(root)` in `work.py` using the installed `sovereign_agent` package. No provider executable or credential is needed: construct `ProviderCapabilities` values as offline probe results and call the same fail-closed contract used by adapters.

## Break it

Append `accept` to the actor's own authority list and verify the operator still cannot accept. Next request streaming from a capability record that cannot prove streaming. Finally flip only that proven bit and observe the request pass without changing actor identity.

## Explain it back

Separate four nouns precisely: actor id, role, provider, and capability. Which can change during a rebind? Which grants organizational authority? Which describes what a particular CLI invocation can safely do?
