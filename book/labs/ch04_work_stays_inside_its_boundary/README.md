## Challenge

An actor may write inside its assigned workspace, but a filename is not a boundary. Build a resolved-path guard that refuses absolute paths, `..` escapes, and a symlink whose target is outside the workspace. Then write a canonical receipt plus its SHA-256 sidecar and compare before/after snapshots of the organization tree.

Your result must distinguish prevention from detection. The path guard prevents a named output from escaping. The snapshot only detects changes in its declared scope; it deliberately excludes the run workspace and the SQLite ledger.

## Production map

- `src/sovereign_agent/workspace.py:safe_join` resolves the root and candidate before checking containment.
- `src/sovereign_agent/workspace.py:snapshot_boundary` and `diff_boundary` report detected changes and carry their limited scope.
- `src/sovereign_agent/execution.py:write_receipt` writes canonical evidence and a digest sidecar.
- The tests named in `lab.json` exercise traversal, symlink, boundary-detection, and ledger-blind-spot cases.

## Run it

From this directory, run:

```console
cp starter.py work.py
python check.py work.py /tmp/sa-ch04-lab
```

Fill the numbered TODO seams in `work.py` and rerun the checker. Use `python check.py solution.py /tmp/sa-ch04-lab` only after attempting the repair. The checker creates no network traffic and may be rerun against the same root.

## Break it

First replace the resolved-path comparison with `str(candidate).startswith(str(root))`. Observe that a sibling such as `workspace-evil` or a symlink can pass a textual prefix check. Next hash `str(receipt)` instead of canonical JSON bytes; vary key insertion order and observe that logically equal receipts acquire different digests. Finally, remove the snapshot scope from the result and explain how a clean report becomes an overclaim.

## Explain it back

Why must containment be checked after symlink resolution? What fact does the digest prove, and what does it not authenticate? Why is `boundary_clean: true` weaker than “the actor touched nothing outside its workspace”? Name the two deliberately invisible locations in this lab.
