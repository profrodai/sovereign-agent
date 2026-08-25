# Chapter 0 — Andrea's first shift

## Status: runnable (manual replenishment, no Pulse)

Complete the first shift without provider tokens:

```bash
sovereign-agent doctor
sovereign-agent demo store --mode simulated --root /tmp/andrea-shift
```

You should see `outcome ACCEPTED`.

The path is:

```text
sale → inventory signal persisted → manually dispatched replenishment SOW
→ Scripted Operator → evidence → Sparring → acceptance
```

Pulse is not part of this chapter. The organization does not wake itself yet;
the demo dispatches the replenishment SOW explicitly. Proactive wake behavior
arrives in Chapter 7 / Unit 9.

Inspect:

- `governance/outcomes/*/outcome.json` and `README.md`
- `.sovereign/organization.db`
- `.sovereign/runs/*/.sovereign-out/report.json`

`solution.py` imports the production demo rather than copying it.
