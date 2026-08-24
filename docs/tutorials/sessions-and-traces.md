# Inspect sessions and traces

Every task becomes a session directory. This is the main debugging interface,
not an implementation detail.

## Create something to inspect

From a repository checkout:

```bash
python -m examples.research_assistant.run
```

The command prints its artifact location. Offline examples normally use a
temporary directory and may clean it up; real runs persist under the platform
data directory. `sovereign-agent run` writes to `./sessions/`.

## Read from the outside in

1. `session.json` — current state, timestamps, scenario, and ancestry.
2. `SESSION.md` — task context given to the run.
3. `workspace/` — files the agent produced.
4. `tickets/` — operation records and verified output manifests.
5. `logs/trace.jsonl` — ordered planner, executor, and capability events.
6. `ipc/` — durable handoff, approval, and completion messages.

Use the CLI when you want a summary:

```bash
sovereign-agent sessions list
sovereign-agent sessions show <session-id>
sovereign-agent report <session-id>
```

Use ordinary file tools when you need exact evidence:

```bash
cat sessions/<session-id>/logs/trace.jsonl
find sessions/<session-id>/tickets -type f
```

## Debug a failed run

Work backward:

1. Read the final result and terminal state.
2. Find the last unsuccessful event in `trace.jsonl`.
3. Inspect that event's arguments and result.
4. Confirm the capability existed in the callable surface.
5. Check whether the model used successful outputs in its final answer.

A structurally successful run can still be wrong. Add a domain-specific
dataflow audit, as the research and code-review examples do.

## Resume without rewriting history

```bash
sovereign-agent sessions resume <parent-id> --task "Continue with the missing section"
```

Resume creates a child session. The parent remains immutable and the child
records its ancestry. See the offline
[`session_resume_chain`](https://github.com/zeroemployeeorg/sovereign-agent/tree/main/examples/session_resume_chain)
example.
