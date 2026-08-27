# Contributing to sovereign-agent

Bug reports, documentation improvements, tests, and focused code changes are
welcome. The project is alpha, and its governance and evidence contracts are
deliberate.

## Set up a development checkout

Requirements: Git, Python 3.14+, `make`, and
[`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/zeroemployeeorg/sovereign-agent.git
cd sovereign-agent
make install
```

No API key is needed for anything in this repository, including the full test
suite. Verify the installed CLI with:

```bash
uv run sovereign-agent doctor
```

## Development loop

The Makefile has five targets and no others:

```bash
make install   # uv sync --all-groups
make lint      # ruff format --check, ruff check, mypy
make test      # pytest
make verify    # lint + test
make doctor    # the CLI's own environment check
```

Before opening a pull request, run `make verify`, plus the checks CI runs that
the Makefile does not wrap:

```bash
uv lock --check
uv run python scripts/verify_runtime_dependencies.py
uv run python scripts/verify_source_budget.py
uv run python scripts/verify_curriculum.py
```

Provider smoke tests that need credentials are opt-in, deselected by default,
and gated behind `SOVEREIGN_AGENT_LIVE_ASSIGNMENTS=1`. Default CI needs no
credential and no commercial CLI. Never include credentials in issues, commits,
fixtures, or session artifacts.

## Change the right surface

- Library code: `src/sovereign_agent/`
- The reference organization: `src/reference_organizations/store/`
- Deterministic tests: `tests/`
- The executable textbook: `book/` — the source of truth for chapters. It is
  rendered and published by `zeroemployeeorg/zeo-site`; this repository builds
  no site of its own. See [`book/CONTENT-SOURCE.md`](book/CONTENT-SOURCE.md)
  for the contract a renderer inherits, and
  [the publication ruling](docs/rulings/2026-08-27-book-publication-destination.md)
  for why the destination lives there rather than here.
- Verification scripts: `scripts/`
- Rulings and reference notes: `docs/` — much of it documents the 0.x line and
  is labelled as historical.

Anything in `sovereign_agent.__all__` is part of the public contract, and
`scripts/verify_source_budget.py` enforces a cap on it. Changing that surface
deliberately means updating the tests and the relevant rulings in the same
change.

## Rulings

Binding decisions live in `docs/rulings/`. A ruling that contradicts the code is
worse than no ruling, because it teaches a reader that the governance records
are decoration. If you find one that no longer describes the repository, file an
amendment rather than editing the original, and say how to check it against the
code.

## Documentation standard

- Start with a user goal and state prerequisites, including any tool the reader
  must already have installed.
- Every command shown must actually run. Execute it before committing it — the
  curriculum gate executes chapter *solutions*, not the commands in prose.
- Label network, token cost, platform, and destructive steps before the command.
- Say which line is 1.x and which is historical.

## Pull requests

Keep changes focused and explain:

1. the user-visible problem;
2. why the chosen behavior is correct;
3. what evidence proves it — ideally a test that fails without the change.
