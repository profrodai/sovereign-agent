# Debug a run

1. Locate it with `sovereign-agent sessions list`.
2. Render the overview with `sovereign-agent report <session-id>`.
3. Read `session.json` for terminal state and ancestry.
4. Search `logs/trace.jsonl` for unsuccessful events.
5. Inspect the corresponding ticket and workspace files.

Common diagnoses:

- **Capability never called:** verify it was bound and exposed; improve a vague
  description only after checking the callable surface.
- **Arguments rejected:** compare model arguments with the Pydantic request.
- **Good capability output, wrong answer:** add a dataflow integrity audit.
- **Missing file:** inspect the exact workspace path in the trace.
- **Stalled approval:** list pending requests and record a grant or denial.
- **Worker refused:** requested isolation, image digest, host identity, quota,
  or network policy was not enforceable. Do not weaken it silently.

Preserve the session directory when filing a bug, but redact prompts, tool
outputs, paths, identities, and credentials before sharing.
