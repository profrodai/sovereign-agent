# Troubleshooting

## Python is too old

Sovereign Agent v0.7 requires Python 3.13+. Create the virtual environment with
that interpreter explicitly.

## Doctor reports a missing key

Use `sovereign-agent doctor` for offline verification (it never calls the
network). For a live check, set `SOVEREIGN_AGENT_LLM_API_KEY` if your endpoint
needs one; a local Ollama needs no key.

## A model or endpoint is rejected

Confirm the endpoint is OpenAI-compatible, includes the expected `/v1` path, and
serves the model named by `SOVEREIGN_AGENT_LLM_MODEL`. An unreachable endpoint
does not crash a run: the `ollama` provider records an honest `failed`
ActorReport, which you can read in the run's `report.json`.

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
