# Chapter 4 — Work stays inside its boundary

When Lucy hires a contractor to fix the freezer, she doesn't follow them around
the shop. But she does notice if the till is short afterward. She can't *prevent*
a stranger from wandering into the back office — but she can *tell* whether they
did.

A provider is that contractor. In Chapter 3 you saw that `--workspace` selects a
directory for it to work in; what you didn't see is that, for most providers,
nothing at the operating-system level *stops* the provider from writing outside
that directory. That sounds alarming until you internalize the move this chapter
makes: instead of promising a containment the providers cannot deliver, the
organization makes the boundary **detectable** — within a stated scope. Before
and after the provider runs, it takes a digest of the tracked files inside the
organization root, *excluding the workspace itself and the SQLite ledger*, and
compares. A change in that scope is recorded on the ledger, permanently.

Be precise about what that does and does not cover: it detects tracked changes in
`organization_root_excluding_workspace_and_ledger`. It does **not** watch the
whole filesystem — a provider that writes to `/tmp` or the home directory is
outside what this check can see. An honest "we can tell, within this scope" beats
a dishonest "we prevented it." This chapter builds the honest version and marks
its edges.

## Learning objective

Understand what "the provider only writes to its workspace" actually means in
this system: not an operating-system sandbox, but a **detectable boundary** —
checkable before a write is ever attempted (`safe_join`), checkable after a
provider has run (`snapshot_boundary`/`diff_boundary`), and a disposal policy
(`reclaim_workspace`) that decides what survives once the work is done.

Chapter 3 flagged that `--workspace` selects a directory, not a sandbox. This
chapter builds the machinery that makes that flag honest rather than alarming.

## Vocabulary this chapter adds

| Term | What it is |
| --- | --- |
| **Workspace** | The one directory an assignment's provider is allowed to write inside — `.sovereign/runs/<workspace_id>/`. |
| **Boundary snapshot** | A digest of every tracked file *outside* the workspace and the SQLite ledger, taken before and after a provider runs. |
| **Boundary violation** | A file added, removed, or changed outside the workspace between the two snapshots — **detected**, not prevented. |
| **Workspace policy** | `temporary_directory` (scratch space reclaimed after the assignment finishes) or `persistent` (nothing reclaimed, the whole run stays inspectable). |
| **Reclaim** | Removing an assignment's disposable scratch space — never the receipt or its declared output. |

## The exercise

```bash
python book/ch04_work_stays_inside_its_boundary/solution.py --root /tmp/lucy-ch04
```

Reads real output straight from the production `workspace` module: it runs one
full assignment through `Organization.run_assignment`, then exercises
`safe_join`, `snapshot_boundary`/`diff_boundary`, and `reclaim_workspace`
directly, the same functions `run_assignment` itself calls on every
invocation.

## Expected observations

```json
{
  "safe_join": {
    "legitimate_nested": "resolved to sample-workspace/nested/artifact.txt",
    "traversal": "refused: Path '../../etc/passwd' escapes its workspace root. ...",
    "absolute": "refused: Path '/etc/passwd' escapes its workspace root. ...",
    "empty": "refused: Empty path. A workspace-relative path must name something. ..."
  },
  "boundary_scope": "organization_root_excluding_workspace_and_ledger",
  "boundary_violation_detected": {
    "violated": true,
    "added": [
      "outside-the-workspace.txt"
    ]
  },
  "boundary_clean_run_not_flagged": {
    "violated": false
  },
  "reclaim": {
    "assignment_state": "COMPLETED",
    "before": [".sovereign-out", "provider-raw", "receipt.json", "receipt.json.sha256"],
    "after": [".sovereign-out", "receipt.json", "receipt.json.sha256"],
    "reclaimed_something": true,
    "receipt_preserved": true,
    "output_dir_preserved": true,
    "scratch_removed": true
  },
  "workspace_policy_default": "temporary_directory"
}
```

Four things worth reading closely:

1. **`safe_join` refuses by shape, not by luck.** An absolute path is refused
   *even when it would resolve inside root* — the function's own contract is
   "name something inside root using a relative path," so acceptance never
   depends on where the caller's filesystem happens to put things.
2. **`boundary_scope` is a value you can check, not a docstring you have to
   trust.** It literally says what the check does and does not cover:
   `organization_root_excluding_workspace_and_ledger`. The workspace itself is
   excluded because the actor is *authorized* to write there. The SQLite
   ledger is excluded because this same process legitimately writes it in its
   own transaction. A `violated: False` report means "nothing changed in what
   this check can see" — not an unqualified claim that execution stayed
   inside the workspace everywhere.
3. **A real write outside the workspace is caught.** `outside-the-workspace.txt`
   shows up in `added`, because nothing in this system relies on a provider's
   own good behavior to prove the boundary held — it is checked from outside,
   after the fact.
4. **Reclaim is a policy decision, not an automatic cleanup.** `provider-raw`
   (the disposable scratch space) is gone after reclaim; `receipt.json`,
   `receipt.json.sha256`, and `.sovereign-out` (the durable proof of what ran,
   and its declared output) are not touched. `_require_deliverables` and
   `accept()` both read from `.sovereign-out` long after `run_assignment`
   returns — a reclaim policy that deleted it would silently break
   re-verification.

## Why detection, not prevention

Only Codex's adapter gives real OS-level containment (`--sandbox
workspace-write`). `claude`, `cursor`, and `scripted` have none — Chapter 3
already told you `--workspace` is a selected directory, not a sandbox. This
chapter does not invent containment those providers don't have. It makes the
*absence* of containment checkable: a clean boundary report is evidence that,
for this one invocation, nothing outside the workspace changed — not a claim
that anything was stopped from changing. A dirty report does not block the
assignment from completing either; it puts the fact on the ledger as a durable
event (`assignment.workspace_boundary_checked`) either way, exactly as the
governing ruling asks: "you can determine after the fact whether execution
stayed inside it."

## Learner verification command

```bash
python -m pytest tests/test_workspace_lifecycle.py -k \
  "reclaimed_after_terminal_state or persistent_policy or temporary_directory_policy or detects_write_outside or do_not_trip_the_boundary or traversal or absolute_deliverable or legitimate_nested"
```

Expected: all pass. Together they prove reclaim runs on every terminal path,
`workspace_policy` actually branches behavior, a real escape outside the
workspace is detected, and a legitimate in-workspace write is not
misreported as one.

## Explain it back

1. `safe_join` refuses an absolute path outright, even one that would resolve
   inside the workspace root. Why does "would resolve inside root" not make
   an absolute input safe to accept?
2. `boundary_scope` names two things the boundary check structurally cannot
   see. Name them, and explain why excluding each one is a deliberate
   decision rather than a gap nobody noticed.
3. A dirty boundary report does not block the assignment from completing.
   Why record the violation anyway, rather than refusing the run outright?
4. `reclaim_workspace("persistent")` reclaims nothing. What would you lose if
   `temporary_directory` were the *only* policy this system offered?
5. This chapter's boundary check is a **ledger** guarantee, not a filesystem
   one. If a provider's subprocess already wrote real bytes outside the
   workspace before the after-snapshot ran, what exactly does the recorded
   violation change about those bytes?

## Where to look next

- `src/sovereign_agent/workspace.py` — `safe_join`, `snapshot_boundary`,
  `diff_boundary`, `reclaim_workspace`
- `src/sovereign_agent/workspace.py` — read the boundary check and the reclaim
  policy end to end; they are short, and the exercise above calls exactly them
- `.sovereign/runs/<workspace_id>/` — inspect one directly after running the
  exercise above

`solution.py` imports the production package rather than copying it.

Next: [Chapter 5 — Authority needs a fence](../ch05_authority_needs_a_fence/README.md)
