# Add rules and human approval

Models decide what to propose. Deterministic Python decides what is allowed.
Sovereign Agent calls these the loop half and the structured half.

## Start with a rule

```python
from sovereign_agent import Rule, StructuredHalf

structured = StructuredHalf(
    rules=[
        Rule(
            name="commit_under_cap",
            condition=lambda data: data["deposit"] <= 300,
            action=commit_booking,
        ),
        Rule(
            name="escalate_over_cap",
            condition=lambda data: data["deposit"] > 300,
            escalate_if=lambda data: True,
        ),
    ]
)
```

The model cannot prompt its way around these conditions. Keep business limits,
authorization, and escalation in code.

Run the complete two-half example offline:

```bash
python -m examples.pub_booking.run
python -m examples.pub_booking.run --oversize
```

## Pause for a person

A capability can request human approval. The executor writes a durable request
and exits cleanly; a separate process can decide later:

```bash
sovereign-agent approvals list <session-id>
sovereign-agent approvals grant <session-id> <request-id> --reason "Within policy"
# or
sovereign-agent approvals deny <session-id> <request-id> --reason "Exceeds limit"
```

The decision is recorded on disk. Resume creates a new forward-only session
rather than mutating completed history.

Run both paths without a model:

```bash
python -m examples.hitl_deposit.run
```

## Production checklist

- Authenticate approvers outside the model.
- Record a useful reason and approver identity.
- Treat timeouts and missing decisions as denial unless policy says otherwise.
- Never put secret values in approval payloads.
- Test grant, deny, timeout, duplicate, and restart behavior.
