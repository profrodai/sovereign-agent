"""Status snapshots, backup/restore, retention, and v0.3 copy-on-write migration."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent.runtime import (
    RUNTIME_LAYOUT_VERSION,
    RuntimeRoot,
    directories_for_layout,
)
from sovereign_agent.service import CoordinatorConflict


def snapshot(runtime_root: RuntimeRoot, **sections: Any) -> dict[str, Any]:
    payload = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "runtime_root": str(runtime_root.root),
        "layout_version": runtime_root.layout_version,
        **sections,
    }
    return payload


def backup(runtime_root: RuntimeRoot, destination: Path) -> Path:
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(
        runtime_root.root,
        destination,
        ignore=shutil.ignore_patterns("*.lock", ".rename-probe", ".rename-probe.renamed"),
        symlinks=False,
    )
    manifest = {
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": str(runtime_root.root),
        "layout_version": runtime_root.layout_version,
    }
    atomic_write_json(destination / "backup-manifest.json", manifest)
    return destination


def restore(
    archive: Path, destination: Path, *, verify_only: bool = False, live_root: Path | None = None
) -> Path:
    archive = Path(archive)
    destination = Path(destination)
    if live_root is not None and destination.resolve() == Path(live_root).resolve():
        raise CoordinatorConflict("restore refuses to overwrite a live coordinator root")
    if (destination / "service" / "coordinator.json").exists():
        raise CoordinatorConflict("restore refuses to overwrite a live coordinator root")
    manifest = archive / "backup-manifest.json"
    if not manifest.exists():
        raise ValueError("backup manifest missing")
    if verify_only:
        return archive
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(archive, destination)
    return destination


def compact(runtime_root: RuntimeRoot, *, retain_receipts: bool = True) -> dict[str, Any]:
    removed: list[str] = []
    attempts = runtime_root.relay_dir / "attempts"
    if attempts.exists():
        for path in attempts.glob("*.jsonl"):
            # keep attempt logs unless tiny/empty; retention is conservative
            if path.stat().st_size == 0:
                path.unlink()
                removed.append(str(path))
    manifest = {
        "compacted_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "removed": removed,
        "retain_receipts": retain_receipts,
    }
    runtime_root.ensure_directory("operations")
    atomic_write_json(runtime_root.operations_dir / "compaction-manifest.json", manifest)
    return manifest


def migrate_v03_copy_on_write(source: Path, destination: Path) -> RuntimeRoot:
    source = Path(source)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(source, destination)
    for name in directories_for_layout(RUNTIME_LAYOUT_VERSION):
        (destination / name).mkdir(mode=0o700, exist_ok=True)
    metadata = {
        "schema_version": 1,
        "layout_version": RUNTIME_LAYOUT_VERSION,
        "directories": list(directories_for_layout(RUNTIME_LAYOUT_VERSION)),
        "migrated_from": str(source),
        "migrated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    atomic_write_json(destination / "runtime.json", metadata)
    return RuntimeRoot.open(destination)
