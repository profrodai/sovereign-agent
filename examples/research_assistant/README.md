# Research assistant example

A small sovereign-agent scenario: take a research question, use a `web_lookup` tool to fetch mock evidence, and write a short markdown report to `workspace/report.md`.

The scenario is deliberately offline. The `web_lookup` tool returns scripted results from a fixture file, and the demo runs against `FakeLLMClient`. Swap either half for the real thing — an `OpenAICompatibleClient` for the LLM, or replace `web_lookup` with a real HTTP-backed tool — and you have the live version.

## Why this example

It exercises the parts of sovereign-agent a new user is most likely to reach for:

- Authoring a reusable action as a ZeoCore `@capability` (canonical capability
  ID, effects, typed request). The in-tree runner still uses a scripted
  lookup for determinism; new work should follow the capability path, not
  `@register_tool`.
- Running the full loop half: planner produces subgoals, executor makes tool
  calls, eventually calls `write_file` and `complete_task`.
- Producing an auditable session directory with verified manifests on every ticket.

## Run

```bash
python -m examples.research_assistant.run
```

For the live version:

```bash
NEBIUS_KEY=... python -m examples.research_assistant.run --real
```

## Output

```
sessions/sess_<id>/
├── session.json
├── SESSION.md                         <-- task description
├── workspace/
│   └── report.md                      <-- the final report
├── logs/
│   ├── trace.jsonl                    <-- every event
│   └── tickets/
│       ├── tk_<planner>/              <-- 1 subgoal, verified manifest
│       └── tk_<executor>/             <-- 2 tool calls, verified manifest
└── ipc/
    └── session_complete.json
```

After running, print the report:

```bash
cat sessions/sess_*/workspace/report.md
```
