# Ruling amendment: `main` is the 1.x educational integration line

- **id:** `ruling-2026-08-25-main-is-the-1x-line`
- **decided:** 2026-08-25
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x branch policy and release expectations
- **status:** ACTIVE
- **amends:** [`ruling-2026-08-25-educational-reset`](2026-08-25-educational-reset.md)

## Why this amendment exists

The educational-reset ruling recorded, under *Consequences in this repository*:

> Implementation proceeds on `v1-educational`. `main` remains the 0.7 line
> until the 1.0 definition of done is met.

That holding no longer describes reality. Units 0 through 6 were reviewed,
approved, and merged into `main` (PRs #20, #21, #22, #23). `main` today
contains the Python 3.14 educational skeleton, not the 0.7 framework.

A ruling that contradicts the repository is worse than no ruling: it teaches a
learner to distrust the governance records. The correction is an amendment on
the record, **not** a rewrite of Git history and **not** a quiet edit of the
original file.

## Holdings

1. **`v0.7.0` remains immutable.** The tag stays at commit
   `be2a41bbee202c52a40b2e87c00215827be302a0`. It is not moved, retagged, or
   deleted. The 0.x line remains installable exactly as released.
2. **`main` is the 1.x educational integration line.** As of the Unit 0 merge,
   `main` carries the 1.x executable textbook. The earlier holding that "`main`
   remains the 0.7 line until the 1.0 definition of done is met" is
   **superseded** in full.
3. **Users who need the 0.x framework pin `sovereign-agent<1`.** This is
   unchanged by this amendment and is the supported migration answer.
4. **No release-gate claim is made.** Nothing in this amendment asserts that
   1.0 has met its definition of done. `main` carries `1.0.0.dev1`, a
   pre-release. Outstanding gates include the credentialed provider smokes
   (Unit 12), which have **not** been run.
5. **History is not rewritten.** The merges that produced this state stand as
   the durable record of how the line moved.

## What did not change

- The persistence doctrine of the original ruling is refined **separately**, by
  [its own ruling](2026-08-26-persistence-boundary-refinement.md). This
  amendment decides branch policy and nothing else: two unrelated decisions
  should not share one authority record.
- Holdings 1 through 7 of the educational-reset ruling remain in force.
- The production destination remains Zero Employee in Go. This package is the
  didactic reference.

## How to verify this amendment against the repository

```console
git log --oneline --first-parent main | head
git tag --list 'v0.7.0' --format='%(objectname) %(refname:short)'
python -c "import sovereign_agent; print(sovereign_agent.__version__)"
```

The first command shows the merged 1.x units on `main`. The second shows the
`v0.7.0` tag still present. The third prints a `.dev` version, which is the
package stating plainly that it is not a finished 1.0.
