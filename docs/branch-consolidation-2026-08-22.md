# Branch consolidation — 2026-08-22

A record of how the pre-v0.3 feature branches landed on `main`, written from the
live repository state rather than from memory. Everything below was read out of
`git` and the GitHub API on 2026-08-22.

Repository: [`zeroemployeeorg/sovereign-agent`](https://github.com/zeroemployeeorg/sovereign-agent).

## Why this document exists

Seven branches accumulated in parallel while `main` sat still — six gathered into
one integration branch and merged as PR #1, plus a CI fix merged as PR #2. They
were integrated **without rewriting feature history** — no rebase, no squash, no
force-push — so the individual commits are still reachable and still say what
they said when they were written. That choice is only useful if the mapping from
branch to merge commit is written down somewhere, because "reachable" and
"findable" are not the same thing.

## What `main` was before

`main` was at `5b72183d43684da16cd565a2e6f206e750e249b4` (2026-08-07), the commit
that added `.claude/` seat configuration and `WORK-REPO.md`.

## Pull requests

Two pull requests moved everything onto `main`. Both are merged.

| PR | Title | Head | Merge commit | Merged (UTC) |
|---|---|---|---|---|
| [#1](https://github.com/zeroemployeeorg/sovereign-agent/pull/1) | Integrate pre-v0.3 execution harness without rewriting feature history | `integration/v0.3-execution-harness` | `90d1d3697c552bd7765f32033aab299336648fdb` | 2026-08-22 15:57:09 |
| [#2](https://github.com/zeroemployeeorg/sovereign-agent/pull/2) | Fix CI dev dependency installation | `fix/ci-dev-dependency-group` | `c139ad73c6937258b72e5fa073faa9181d7f1bc0` | 2026-08-22 16:16:53 |

`main` is now at `c139ad73c6937258b72e5fa073faa9181d7f1bc0`.

## Branch tips, and where they went

Every branch below is an ancestor of `origin/main` — verified with
`git merge-base --is-ancestor`. Each has a matching `archive/<branch>` tag
pointing at the same commit, so the tip survives if the branch ref is ever
deleted.

| Branch | Tip commit | Archive tag | Ancestor of `main` |
|---|---|---|---|
| `chore/src-layout` | `a90e1815166833e851d203abb5125022578aa615` | `archive/chore/src-layout` | yes |
| `feat/channels-adapter` | `0dc28571061dadc7ab8beaccba3170e199b94112` | `archive/feat/channels-adapter` | yes |
| `feat/engage-modes` | `81207aac5a0ced21a0e409fe385e0b6ad05917ff` | `archive/feat/engage-modes` | yes |
| `feat/plugin-registries` | `4a96e6fb4a1e743f44c916c55f7d353ee334acbe` | `archive/feat/plugin-registries` | yes |
| `feat/worker-backend-integration` | `97b47771fc6f7b79d34f395540aee1e9deea5d10` | `archive/feat/worker-backend-integration` | yes |
| `feat/liveness-monitor` | `b714eeae836fe25bd9290efd49e7a7ee1d4db4f1` | `archive/feat/liveness-monitor` | yes |
| `fix/ci-dev-dependency-group` | `514be77bb08914d812d233138cc0c7c3ea9688e1` | `archive/fix/ci-dev-dependency-group` | yes |

Two fixes were needed to make the integrated tree green, and they are worth
naming because they are the kind of thing that silently rots:

- `c4cd580` — restored src-layout CI lint paths, `pytest` `pythonpath`, and a
  `ruff` `I001` import-order fix after the src-layout move.
- `514be77` — installed the PEP 735 `dev` dependency *group* in CI. Dev tooling
  is a group, not a `[dev]` extra, so `pip install -e .[dev]` was quietly
  installing nothing.

## Tag correction

**`archive/pre-v0.3-runtime-stack-20260822` does not mean what its name says.**

The name reads as "the state of the runtime stack immediately before v0.3 work",
which any reader would take to mean a snapshot of `main`. It is not. It points at
`b714eeae836fe25bd9290efd49e7a7ee1d4db4f1` — the tip of `feat/liveness-monitor`,
byte-identical to `archive/feat/liveness-monitor`. It is a duplicate of one
feature-branch tip, not a snapshot of anything.

If you want the actual pre-v0.3 state of `main`, use
`5b72183d43684da16cd565a2e6f206e750e249b4` (the first parent of merge commit
`90d1d36`), **not** this tag.

The tag is left in place and is not being retargeted or deleted. Moving a
published tag is worse than a misleading name: anyone who already fetched it
would silently disagree with the remote about what the tag means. The correction
lives here instead, and this document is the thing to trust.

Summary of the correction, for anyone scanning:

| Tag | Points at | Name implies | Actually is |
|---|---|---|---|
| `archive/pre-v0.3-runtime-stack-20260822` | `b714eea` | pre-v0.3 snapshot of `main` | duplicate of `archive/feat/liveness-monitor` |

## Release tags

`v0.2.0` → `9d934cf53ff223175d01ebf07483fd608fae66a0` ("Set version to 0.2.0
(stable) in pyproject.toml", 2026-04-24). This is the only release tag and
matches the only PyPI release.

No v0.3 tag exists. `pyproject.toml` still declares `0.2.0` while `main` carries
v0.3 work, so **the version string does not identify the tree**. Use commit SHAs
when reporting against `main`.

## Verified state at `c139ad7`

- `pytest` — 370 collected, 369 passed, 1 skipped.
- `sovereign_agent.__all__` — 76 symbols (67 of which shipped in 0.2.0).
- `git merge-base --is-ancestor` — all seven branch tips are ancestors of
  `origin/main`.
