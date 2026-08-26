# Deferral: credentialed provider smokes are Unit 12

- **id:** `ruling-2026-08-26-deferral-unit6-smokes`
- **decided:** 2026-08-26
- **authority:** principal
- **applies_to:** Unit 6 provider adapters; Unit 12 release
- **status:** ACTIVE

## The distinction this ruling exists to keep

**Installed is not authenticated.** `sovereign-agent doctor` reports Claude Code,
Codex and Cursor as available on a machine where all three are on `PATH`. That
establishes the executable exists and answers `--help`. It establishes nothing
about whether a credential works, whether a real session completes, or whether a
live provider honours the workspace boundary.

Conflating the two would be the defect this line spent Unit 6.5 removing: a
green signal standing in for a fact it does not measure.

## Holdings

1. **Unit 6 is accepted on offline evidence.** Adapters implement
   `probe` / `build_invocation` / `parse_event`; invocations are `argv` arrays
   with no shell string anywhere; capability claims come from probing the
   installed CLI and fail closed when unprovable; fixtures are deterministic and
   integration tests use fake executables.
2. **The credentialed smokes have not run.** Nine tests are collected under the
   `live` marker and deselected by default: three installed-CLI probes that
   submit no work, and six assignment smokes (read-only and workspace-write for
   each provider) gated behind `SOVEREIGN_AGENT_LIVE_ASSIGNMENTS=1`.
3. **Default CI must never need a credential** or a commercial CLI. Verified by
   running the suite with provider environment variables unset.
4. **Nothing may report these as passing.** Not the CHANGELOG, not a chapter,
   not a release note, not a PR description. They are a Unit 12 release gate.

## Why deferred rather than run

Running them requires credentials this environment does not hold, and they
consume provider credits. A smoke that cannot be run is honestly deferred; a
smoke reported as passing because the CLI is installed is a lie of exactly the
kind this project teaches learners to detect.

## How to run them when Unit 12 arrives

```bash
python -m pytest -q -m live                                   # probes only
SOVEREIGN_AGENT_LIVE_ASSIGNMENTS=1 python -m pytest -q -m live  # + assignments
```

Each assignment smoke uses a disposable fixture repository and proves its trunk
commit did not move.
