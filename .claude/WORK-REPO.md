# A WORK REPO IS NOT THE CORPUS

`org/` is TRUNK-ONLY for filings: a SOW on a branch is invisible to every other seat's
`--inbox`. **THIS repo is the opposite** - it holds CODE that genuinely collides, so
s10's worktree ritual applies: one worktree per stream, on `<seat>/<topic>`, cut from
`origin/main`, ONE STEP PER BLOCK.

**`make verify` is the gate** (s6a). Apply -> verify -> THEN commit. A gate whose output
you discard is not a gate: run it visibly and branch on its exit status.

**A seat pushes its OWN branch** (RULING-007 standing clearance). Pushing `main`,
merging, rebasing and force-pushing are MASTER's - denied here mechanically, not by
convention.

**Your SOW lives in the corpus repo, not here.** `sow_repo` is where you REPORT,
`work_repo` is where you CHANGE CODE, and they are different fields for a reason (s15).
