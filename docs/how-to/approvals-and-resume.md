# Handle approvals and resume work

List requests:

```bash
sovereign-agent approvals list <session-id>
```

Record a decision:

```bash
sovereign-agent approvals grant <session-id> <request-id> \
  --approver "operator@example.com" --reason "Within approved limit"

sovereign-agent approvals deny <session-id> <request-id> \
  --approver "operator@example.com" --reason "Exceeds approved limit"
```

Approval records are durable files. A grant does not erase the request, and a
denial can be supplied to the next plan as evidence.

Resume completed work as a child:

```bash
sovereign-agent sessions resume <session-id> \
  --task "Continue after the recorded approval decision"
```

By default, unfinished parents cannot be resumed. Use
`--allow-unfinished-parent` only when your recovery procedure explicitly
permits it.

For an offline demonstration, run:

```bash
python -m examples.hitl_deposit.run
python -m examples.session_resume_chain.run
```
