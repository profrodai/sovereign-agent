"""Workspace lifecycle: reclaim, policy enforcement, and a detectable boundary.

A run workspace (`.sovereign/runs/<workspace_id>/`) is where a provider is
told to confine its reads and writes. Before Unit 7 that boundary was a
sentence in the assignment envelope and the directory itself lived forever.
This module makes the boundary something the organization can check after the
fact, makes `Actor.workspace_policy` change what actually happens on disk, and
makes every path taken from a governed record (a deliverable name) safe to
join without walking outside its declared root.

Three responsibilities, one module, because all three are the same shape: a
workspace is a directory whose contents are supposed to stay inside a line,
and each function here is a different way of drawing that line precisely.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from sovereign_agent.errors import Refusal

# The only two values `Actor.workspace_policy` may hold. A value outside this
# set fails closed rather than silently falling back to a default -- the same
# defect class named in the governing ruling ("workspace_policy ... nothing in
# the package reads it") would recur one layer down if an unrecognized string
# were quietly treated as "temporary_directory".
TEMPORARY_DIRECTORY = "temporary_directory"
PERSISTENT = "persistent"
WORKSPACE_POLICIES = frozenset({TEMPORARY_DIRECTORY, PERSISTENT})

# Reclaim never removes these: the receipt and its digest sidecar are the
# durable proof an execution ran, and the output directory holds the report
# and every declared deliverable, both read by code that runs long after
# `run_assignment` returns (`_require_deliverables`, `accept`, Chapter 3's own
# exercise). "Reclaim" frees the actor's disposable scratch space, not the
# organization's evidence.
_PRESERVED_ON_RECLAIM = ("receipt.json", "receipt.json.sha256")
_PRESERVED_DIR_ON_RECLAIM = ".sovereign-out"


def safe_join(root: Path, relative: str) -> Path:
    """Join `relative` onto `root`, refusing anything that would escape it.

    `Path.__truediv__` treats an absolute right-hand side as a full
    replacement of the left, and a relative path may still climb out via
    `..` segments that a string-prefix check cannot see through symlinks or
    mixed separators. This resolves both `root` and the joined candidate and
    requires the candidate to sit at or under the resolved root -- the check
    is on the resolved filesystem path, not on the string.
    """
    if not relative or relative.strip() == "":
        raise Refusal(
            "Empty path.",
            "A workspace-relative path must name something.",
            str(root),
            "Supply a non-empty relative path.",
            category="path_traversal",
        )
    resolved_root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as error:
        raise Refusal(
            f"Path {relative!r} escapes its workspace root.",
            "A workspace-relative path must resolve inside its declared root, "
            "not beside or above it.",
            str(resolved_root),
            "Use a path that stays inside the workspace.",
            category="path_traversal",
        ) from error
    return candidate


def _iter_files(root: Path, *, exclude: frozenset[Path]) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(path == excluded or excluded in path.parents for excluded in exclude):
            continue
        files.append(path)
    return files


@dataclass(frozen=True)
class BoundarySnapshot:
    """A digest of every tracked file outside one assignment's workspace.

    Not a full filesystem scan of the host -- scoped to the organization root,
    the same tree the assignment envelope calls the boundary. `.sovereign/
    organization.db*` is excluded: the SQLite ledger is legitimately written
    by this same process, in the same transaction that records the
    assignment's own progress, not by the subprocess under test. The
    workspace directory itself is excluded because the actor is *authorized*
    to write there; the boundary this snapshot protects is everything else.
    """

    digests: dict[str, str]

    @property
    def paths(self) -> frozenset[str]:
        return frozenset(self.digests)


def snapshot_boundary(org_root: Path, workspace: Path) -> BoundarySnapshot:
    org_root = org_root.resolve()
    exclude = frozenset(
        {
            workspace.resolve(),
            (org_root / ".sovereign" / "organization.db").resolve(),
            (org_root / ".sovereign" / "organization.db-wal").resolve(),
            (org_root / ".sovereign" / "organization.db-shm").resolve(),
        }
    )
    digests: dict[str, str] = {}
    for path in _iter_files(org_root, exclude=exclude):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digests[str(path.relative_to(org_root))] = digest
    return BoundarySnapshot(digests=digests)


@dataclass(frozen=True)
class BoundaryReport:
    """What changed outside the workspace between two snapshots.

    Named for what it proves: DETECTED, not prevented. A clean report means no
    tracked file outside the workspace changed during this invocation, on the
    provider whose adapter has no OS-level sandbox exactly as much as on the
    one that does -- the check does not depend on the provider having told the
    truth about its own containment.
    """

    violated: bool
    changed: tuple[str, ...]
    added: tuple[str, ...]
    removed: tuple[str, ...]


def diff_boundary(before: BoundarySnapshot, after: BoundarySnapshot) -> BoundaryReport:
    changed = tuple(
        sorted(
            path
            for path in before.paths & after.paths
            if before.digests[path] != after.digests[path]
        )
    )
    added = tuple(sorted(after.paths - before.paths))
    removed = tuple(sorted(before.paths - after.paths))
    violated = bool(changed or added or removed)
    return BoundaryReport(violated=violated, changed=changed, added=added, removed=removed)


def reclaim_workspace(workspace: Path, policy: str) -> bool:
    """Apply `policy` to a workspace that has reached a terminal state.

    Returns whether anything was reclaimed. `temporary_directory` (the
    model's own default) removes the actor's disposable scratch space --
    everything in the workspace except the receipt and the output directory,
    both preserved because later code (`_require_deliverables`, `accept`, the
    Chapter 3 exercise) reads them long after this call returns. `persistent`
    reclaims nothing: the whole point of choosing it is to leave the run
    inspectable. An unrecognized policy fails closed rather than guessing.
    """
    if policy not in WORKSPACE_POLICIES:
        raise Refusal(
            f"Unknown workspace policy {policy!r}.",
            "A policy this module does not recognize must not be silently "
            "treated as either 'reclaim' or 'keep' -- both are real, "
            "consequential choices.",
            str(workspace),
            f"Use one of: {', '.join(sorted(WORKSPACE_POLICIES))}.",
            category="unknown_workspace_policy",
        )
    if policy == PERSISTENT:
        return False
    if not workspace.exists():
        return False
    reclaimed = False
    for entry in sorted(workspace.iterdir()):
        if entry.name in _PRESERVED_ON_RECLAIM or entry.name == _PRESERVED_DIR_ON_RECLAIM:
            continue
        reclaimed = True
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()
    return reclaimed
