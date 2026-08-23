# Contract fixtures exchanged as files, never as Python imports between packages.

Shipped wheel fixtures live in `sovereign_agent.contracts.fixtures` and must
run from an installed environment without this checkout. Test-only provider
transcripts remain under `tests/fixtures/providers/`.
