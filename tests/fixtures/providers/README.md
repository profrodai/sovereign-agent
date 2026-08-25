# Provider fixture provenance

These redacted JSONL fixtures reproduce the documented non-interactive stream
shapes used by Unit 6. They contain no prompts, credentials, repository data,
or provider-generated proprietary content.

- `codex.exec-json.jsonl` follows OpenAI's Codex non-interactive JSONL example,
  retrieved 2026-08-25. No Codex executable was installed on the capture host.
  It includes `thread.started`, `turn.started`, `item.completed`, an unknown
  valid event, and `turn.completed` with usage.
- `claude.stream-json.jsonl` follows Claude Code 2.1.220 print-mode
  `stream-json` output. Provenance: a redacted local protocol capture plus the
  documented success terminal shape; volatile model, paths, ids, and message
  text are replaced.
- `cursor.stream-json.jsonl` follows Cursor Agent CLI `stream-json` output.
  Provenance: Cursor's official output-format schema retrieved 2026-08-25; no
  Cursor executable was installed on the capture host. Volatile model, paths,
  ids, and message text are replaced.
- `protocol-cases.json` records provider-neutral error cases used by the fake
  executable integration suite: provider error, non-zero exit, malformed
  stream, truncated stream, unknown valid event, and resume.

Probe tests record the installed executable's version, command, exit status,
stdout, stderr, and error. Golden fixtures intentionally do not claim that a
future CLI version has the same protocol; opt-in live assignment smokes detect
that drift.
