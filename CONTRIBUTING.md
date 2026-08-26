# Contributing to sovereign-agent

Bug reports, documentation improvements, tests, and focused code changes are
welcome. The project is alpha, but its public API and evidence contracts are
deliberate.

## Set up a development checkout

Requirements: Git, Python 3.13+, `make`, and
[`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/zeroemployeeorg/sovereign-agent.git
cd sovereign-agent
make first-run
```

No API key is needed for normal development. Verify the installed CLI with:

```bash
uv run sovereign-agent doctor --skip-llm
```

## Development loop

```bash
make lint
make test
make test-examples
make docs-strict
```

Before opening a pull request, run `make ci`. If your change touches packaging
or the public API, also run `make release-verify`.

Live model tests are opt-in because they use network access and tokens. Run
`make ci-real-estimate` before any `*-real` target. Never include credentials
in issues, commits, fixtures, or session artifacts.

## Change the right surface

- Library code: `src/sovereign_agent/`
- Deterministic tests: `tests/`
- Runnable scenarios: `examples/`
- The executable textbook: `book/` — the source of truth for chapters. It is
  published by the profrod.ai site, which consumes this directory; this
  repository builds no site of its own.
- Reference and historical notes: `docs/`

New reusable actions should use ZeoCore `@capability`. Do not add new uses of
the deprecated `@register_tool` path.

Anything in `sovereign_agent.__all__` is part of the public contract. Update
tests, `docs/API.md`, the versioned public API manifest, migration guidance, and
release notes when intentionally changing that surface.

## Documentation standard

- Start with a user goal and state prerequisites.
- Prefer runnable examples from `examples/` over untested snippets.
- Label network, token cost, platform, and destructive steps before the command.
- Use current v0.7 behavior; mark historical pages clearly.
- Run `make docs-strict`.

## Pull requests

Keep changes focused and explain:

1. the user-visible problem;
2. why the chosen behavior is correct;
3. deterministic tests or commands run;
4. compatibility, security, cost, or migration impact.

Do not commit generated `site/`, virtual environments, keys, session data, or
provider transcripts containing private content.

## Reporting security issues

Do not open a public issue for a suspected vulnerability. Follow
[SECURITY.md](SECURITY.md).
