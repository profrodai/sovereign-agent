# Troubleshooting

## Python is too old

Sovereign Agent v0.7 requires Python 3.13+. Create the virtual environment with
that interpreter explicitly.

## Doctor reports a missing key

Use `sovereign-agent doctor --skip-llm` for offline verification. For a live
check, set the variable named by `SOVEREIGN_AGENT_LLM_API_KEY_ENV`.

## A model or endpoint is rejected

Confirm the endpoint is OpenAI-compatible, includes the expected `/v1/` path,
and exposes both configured model names. Run `doctor` for a small live probe.

## No session appears

`sovereign-agent run` writes to the configured `sessions_dir` (default
`./sessions`). Repository demos and examples use separate temporary or platform
data paths and print their location.

## Subprocess isolation is unavailable

Landlock needs Linux 5.13+; macOS depends on `sandbox-exec`. Choose `bare` only
when unisolated execution is an explicit risk decision.

## Docker, Podman, or SSH refuses to start

Check engine availability, digest pinning, SSH known-hosts pinning, placement
constraints, quotas, and network enforcement. The correct behavior is refusal,
not fallback.

## The agent succeeded but the answer is wrong

Inspect capability results and compare them with final claims. Add a
scenario-specific dataflow integrity audit and a deterministic regression test.

When reporting a bug, include version, OS, Python version, command, sanitized
doctor output, and a redacted report. Never attach keys or unredacted session
directories.
