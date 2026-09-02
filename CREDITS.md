# Credits

Sovereign Agent combines established software-systems patterns with a runnable
teaching approach. This file names the principal influences on the current 1.x
line; it is not a dependency manifest or a claim that those projects endorse
this one.

## Pedagogical influences

- **Sebastian Raschka, _Build a Large Language Model from Scratch_** — the
  build-it-yourself progression, worked mechanisms, and adversarial exercises.
- **Andrej Karpathy, nanoGPT** — a compact implementation that readers can hold
  in their heads and run locally.
- **Sasha Rush and the MiniTorch project** — executable lessons in which the
  teaching implementation and tested implementation stay connected.

## Systems influences

- **SQLite** — transactions, constraints, and a locally inspectable canonical
  ledger.
- **Capability security and reference monitors** — authority is checked by
  deterministic host policy rather than granted by model confidence.
- **Lease fencing and idempotent consumers** — stale-worker exclusion and
  replay-safe effects under retries and recovery.
- **Event sourcing and derived projections** — append-only facts beside
  reproducible human-readable views.

## Runtime and development dependencies

The current package intentionally has one direct runtime dependency:

- [Pydantic](https://github.com/pydantic/pydantic), MIT — strict boundary
  models and validation.

The development toolchain uses
[build](https://github.com/pypa/build),
[mypy](https://github.com/python/mypy),
[pytest](https://github.com/pytest-dev/pytest), and
[Ruff](https://github.com/astral-sh/ruff). Their authoritative versions and
transitive dependencies are recorded in `pyproject.toml` and `uv.lock`; this
file deliberately does not duplicate the lockfile.

## Contributors

Copyright is held by Rod Rivera and Sovereign Agent contributors. Git history
is the authoritative attribution record for individual contributions. See
[LICENSE](LICENSE) and [NOTICE](NOTICE) for redistribution terms.
