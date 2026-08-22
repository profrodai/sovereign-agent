"""Versioned, durable filesystem root for sovereign-agent runtime state."""

from __future__ import annotations

import json
import re
import secrets
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_json, fsync_directory

RUNTIME_SCHEMA_VERSION = 1
RUNTIME_LAYOUT_VERSION = 1
RUNTIME_METADATA_FILENAME = "runtime.json"
RUNTIME_DIRECTORIES = ("seats", "sessions", "executions", "relay", "receipts", "locks")

_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class RuntimeRootError(ValueError):
    """The runtime root or one of its paths violates the filesystem contract."""


class UnsupportedRuntimeVersionError(RuntimeRootError):
    """The on-disk root uses a version this package cannot safely operate on."""


@dataclass(frozen=True)
class RuntimeRoot:
    """A handle to a versioned runtime filesystem tree.

    Constructing a handle is side-effect free. Call :meth:`initialize` before
    writing. ``legacy_sessions_dir`` makes an existing v0.2 session tree
    readable; a legacy session is copied into this root only on its first
    write, leaving the original tree and its ``session.json`` untouched.
    """

    root: Path
    legacy_sessions_dir: Path | None = None
    schema_version: int = RUNTIME_SCHEMA_VERSION
    layout_version: int = RUNTIME_LAYOUT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))
        if self.legacy_sessions_dir is not None:
            object.__setattr__(self, "legacy_sessions_dir", Path(self.legacy_sessions_dir))
        if self.schema_version <= 0 or self.layout_version <= 0:
            raise RuntimeRootError("runtime versions must be positive integers")

    @property
    def metadata_path(self) -> Path:
        return self.root / RUNTIME_METADATA_FILENAME

    @property
    def seats_dir(self) -> Path:
        return self.root / "seats"

    @property
    def sessions_dir(self) -> Path:
        return self.root / "sessions"

    @property
    def executions_dir(self) -> Path:
        return self.root / "executions"

    @property
    def relay_dir(self) -> Path:
        return self.root / "relay"

    @property
    def receipts_dir(self) -> Path:
        return self.root / "receipts"

    @property
    def locks_dir(self) -> Path:
        return self.root / "locks"

    def initialize(self) -> RuntimeRoot:
        """Create and validate the durable layout and atomic root metadata."""
        if self.root.is_symlink():
            raise RuntimeRootError(f"runtime root must not be a symlink: {self.root}")
        if self.root.exists() and not self.root.is_dir():
            raise RuntimeRootError(f"runtime root is not a directory: {self.root}")

        self.root.mkdir(parents=True, exist_ok=True)
        existing = self._read_metadata()
        if existing is not None:
            self._validate_metadata(existing)

        for name in RUNTIME_DIRECTORIES:
            directory = self.root / name
            if directory.is_symlink():
                raise RuntimeRootError(f"runtime directory must not be a symlink: {directory}")
            directory.mkdir(mode=0o700, parents=False, exist_ok=True)
            if not directory.is_dir():
                raise RuntimeRootError(f"runtime path is not a directory: {directory}")

        if existing is None:
            atomic_write_json(self.metadata_path, self._metadata())
            fsync_directory(self.root)
        return self

    @classmethod
    def open(
        cls,
        root: Path,
        *,
        legacy_sessions_dir: Path | None = None,
    ) -> RuntimeRoot:
        """Open and validate an initialized runtime root without modifying it."""
        runtime = cls(root, legacy_sessions_dir=legacy_sessions_dir)
        metadata = runtime._read_metadata()
        if metadata is None:
            raise RuntimeRootError(f"runtime metadata not found: {runtime.metadata_path}")
        runtime._validate_metadata(metadata)
        for name in RUNTIME_DIRECTORIES:
            directory = runtime.root / name
            if directory.is_symlink() or not directory.is_dir():
                raise RuntimeRootError(f"runtime directory missing or unsafe: {directory}")
        return runtime

    def path(self, relative: str | Path) -> Path:
        """Resolve a relative path inside this root, rejecting every escape."""
        rel = Path(relative)
        if rel.is_absolute():
            raise RuntimeRootError(f"absolute runtime path is not allowed: {relative!r}")
        base = self.root.resolve()
        candidate = (base / rel).resolve()
        try:
            candidate.relative_to(base)
        except ValueError as exc:
            raise RuntimeRootError(f"path escapes runtime root: {relative!r}") from exc
        return candidate

    def session_directory(self, session_id: str, *, for_write: bool = False) -> Path:
        """Return a current or legacy session path, migrating on first write."""
        _validate_component(session_id, "session_id")
        current = self.sessions_dir / session_id
        if current.exists():
            return current

        legacy = self._legacy_session_directory(session_id)
        if legacy is None or not legacy.exists():
            return current
        if not for_write:
            return legacy
        self.initialize()
        return self._copy_legacy_session(legacy, current)

    def create_session(self, *args: Any, **kwargs: Any) -> Any:
        """Create a session in this root (lazy import avoids import cycles)."""
        from sovereign_agent.session.directory import create_session

        kwargs["runtime_root"] = self
        return create_session(*args, **kwargs)

    def load_session(self, session_id: str) -> Any:
        """Load a current or legacy session through this root."""
        from sovereign_agent.session.directory import load_session

        return load_session(session_id, runtime_root=self)

    def list_sessions(self, **kwargs: Any) -> list[Any]:
        """List current and legacy sessions, preferring current copies."""
        from sovereign_agent.session.directory import list_sessions

        return list_sessions(runtime_root=self, **kwargs)

    def _metadata(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "layout_version": self.layout_version,
            "directories": list(RUNTIME_DIRECTORIES),
        }

    def _read_metadata(self) -> dict[str, Any] | None:
        if not self.metadata_path.exists():
            return None
        if self.metadata_path.is_symlink():
            raise RuntimeRootError(f"runtime metadata must not be a symlink: {self.metadata_path}")
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeRootError(f"invalid runtime metadata: {self.metadata_path}") from exc
        if not isinstance(data, dict):
            raise RuntimeRootError("runtime metadata must be a JSON object")
        return data

    def _validate_metadata(self, metadata: dict[str, Any]) -> None:
        schema = metadata.get("schema_version")
        layout = metadata.get("layout_version")
        if schema != self.schema_version or layout != self.layout_version:
            raise UnsupportedRuntimeVersionError(
                "unsupported runtime version: "
                f"schema={schema!r}, layout={layout!r}; "
                f"expected schema={self.schema_version}, layout={self.layout_version}"
            )
        if metadata.get("directories") != list(RUNTIME_DIRECTORIES):
            raise RuntimeRootError("runtime metadata directory layout does not match this version")

    def _legacy_session_directory(self, session_id: str) -> Path | None:
        if self.legacy_sessions_dir is None:
            return None
        legacy_root = self.legacy_sessions_dir.resolve()
        candidate = (legacy_root / session_id).resolve()
        try:
            candidate.relative_to(legacy_root)
        except ValueError as exc:
            raise RuntimeRootError(f"legacy session path escapes its root: {session_id!r}") from exc
        return candidate

    def _copy_legacy_session(self, source: Path, destination: Path) -> Path:
        staging = self.sessions_dir / f".{destination.name}.migrate-{secrets.token_hex(6)}"
        try:
            shutil.copytree(source, staging, symlinks=True)
            try:
                staging.replace(destination)
            except FileExistsError:
                shutil.rmtree(staging)
            fsync_directory(self.sessions_dir)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise
        return destination


def _validate_component(value: str, label: str) -> None:
    if not _SAFE_COMPONENT.fullmatch(value) or value in {".", ".."}:
        raise RuntimeRootError(f"unsafe {label}: {value!r}")


__all__ = [
    "RUNTIME_DIRECTORIES",
    "RUNTIME_LAYOUT_VERSION",
    "RUNTIME_METADATA_FILENAME",
    "RUNTIME_SCHEMA_VERSION",
    "RuntimeRoot",
    "RuntimeRootError",
    "UnsupportedRuntimeVersionError",
]
