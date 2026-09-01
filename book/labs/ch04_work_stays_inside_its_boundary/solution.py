"""Reference solution for Chapter 4: constrain paths and qualify proof."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

STUDENT_TODO = False

BOUNDARY_SCOPE = "organization_root_excluding_workspace_and_ledger"


def _fresh(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
    path.mkdir(parents=True)


def _safe_join(root: Path, relative: str) -> Path:
    if not relative.strip() or Path(relative).is_absolute():
        raise ValueError("path must be a non-empty relative name")
    resolved_root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError("path escapes workspace") from error
    return candidate


def _snapshot(org: Path, workspace: Path, ledger: Path) -> dict[str, str]:
    org = org.resolve()
    workspace = workspace.resolve()
    ledger = ledger.resolve()
    result: dict[str, str] = {}
    for path in sorted(org.rglob("*")):
        if not path.is_file():
            continue
        if path == ledger or path == workspace or workspace in path.parents:
            continue
        result[str(path.relative_to(org))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _diff(before: dict[str, str], after: dict[str, str]) -> list[str]:
    names = set(before) | set(after)
    return sorted(name for name in names if before.get(name) != after.get(name))


def exercise(root: Path) -> dict[str, object]:
    lab = root / "ch04"
    _fresh(lab)
    org = lab / "organization"
    workspace = org / ".sovereign" / "runs" / "run-1"
    ledger = org / ".sovereign" / "organization.db"
    workspace.mkdir(parents=True)
    ledger.write_text("ledger-v1", encoding="utf-8")
    policy = org / "policy.txt"
    policy.write_text("approved", encoding="utf-8")
    outside = org / "private.txt"
    outside.write_text("do not touch", encoding="utf-8")

    # The naive guard reasons about spelling, not the filesystem object reached.
    naive_candidate = workspace / ".." / ".." / ".." / "private.txt"
    naive_accepts_traversal = str(naive_candidate).startswith(str(workspace))

    link = workspace / "shortcut"
    link.symlink_to(outside)
    refused: list[str] = []
    for label, name in (
        ("traversal", "../../../private.txt"),
        ("absolute", str(outside.resolve())),
        ("symlink", "shortcut"),
    ):
        try:
            _safe_join(workspace, name)
        except ValueError:
            refused.append(label)
    nested = _safe_join(workspace, "output/report.json")
    nested.parent.mkdir(parents=True)
    nested.write_text('{"status":"completed"}', encoding="utf-8")

    receipt = {"assignment_id": "asg_demo", "status": "completed", "units": 3}
    receipt_bytes = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt_path = workspace / "receipt.json"
    receipt_path.write_bytes(receipt_bytes)
    digest = hashlib.sha256(receipt_bytes).hexdigest()
    (workspace / "receipt.json.sha256").write_text(digest + "\n", encoding="utf-8")

    before = _snapshot(org, workspace, ledger)
    policy.write_text("tampered", encoding="utf-8")
    ledger.write_text("ledger-v2", encoding="utf-8")
    changed = _diff(before, _snapshot(org, workspace, ledger))

    return {
        "naive_accepts_traversal": naive_accepts_traversal,
        "repaired_refusals": sorted(refused),
        "nested_output": str(nested.relative_to(workspace.resolve())),
        "receipt_digest_matches": hashlib.sha256(receipt_path.read_bytes()).hexdigest() == digest,
        "boundary_changed": changed,
        "boundary_scope": BOUNDARY_SCOPE,
        "ledger_change_visible": ".sovereign/organization.db" in changed,
    }
