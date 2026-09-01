"""Starter for Chapter 4's workspace-boundary lab."""

from __future__ import annotations

import hashlib
from pathlib import Path

STUDENT_TODO = True
BOUNDARY_SCOPE = "organization_root_excluding_workspace_and_ledger"


def safe_join(root: Path, relative: str) -> Path:
    """Return a resolved child of root, or refuse a hostile path."""
    # TODO(1): Refuse empty and absolute names, then prove the resolved
    # candidate is relative to the resolved root (including through symlinks).
    raise NotImplementedError


def snapshot(root: Path, excluded: tuple[Path, ...]) -> dict[str, str]:
    """Hash the visible regular files below root by relative path."""
    # TODO(2): Walk deterministically, omit each excluded path and its children,
    # and SHA-256 the bytes of every remaining file.
    raise NotImplementedError


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return sorted added, removed, or content-changed paths."""
    # TODO(3): Compare the union of path names, not only files present in both.
    raise NotImplementedError


def exercise(root: Path) -> dict[str, object]:
    """Build the hostile-path, receipt-digest, and scoped-snapshot experiment."""
    _ = hashlib.sha256  # The receipt digest must cover canonical JSON bytes.
    # TODO(4): Assemble the naive failure and repaired observations required by
    # check.py, and qualify the snapshot result with BOUNDARY_SCOPE.
    raise NotImplementedError("Implement the Chapter 4 boundary experiment")
