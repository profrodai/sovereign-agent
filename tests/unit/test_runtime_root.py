"""Focused tests for the versioned runtime-root slice."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sovereign_agent._internal import atomic
from sovereign_agent.config import Config
from sovereign_agent.runtime import (
    RUNTIME_DIRECTORIES,
    RUNTIME_LAYOUT_VERSION,
    RUNTIME_SCHEMA_VERSION,
    RuntimeRoot,
    RuntimeRootError,
    UnsupportedRuntimeVersionError,
)
from sovereign_agent.session.directory import SessionEscapeError, create_session, load_session


def test_directory_fsync_is_best_effort_when_host_cannot_open_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable(_path: Path, _flags: int) -> int:
        raise PermissionError("directory handles are unavailable")

    monkeypatch.setattr(atomic.os, "open", unavailable)
    assert atomic.fsync_directory(tmp_path) is False


def test_constructing_runtime_root_has_no_filesystem_side_effect(tmp_path: Path) -> None:
    path = tmp_path / "runtime"
    runtime = RuntimeRoot(path)
    assert runtime.root == path
    assert not path.exists()


def test_initialize_writes_versioned_layout(tmp_path: Path) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()

    metadata = json.loads(runtime.metadata_path.read_text(encoding="utf-8"))
    assert metadata["schema_version"] == RUNTIME_SCHEMA_VERSION
    assert metadata["layout_version"] == RUNTIME_LAYOUT_VERSION
    assert metadata["directories"] == list(RUNTIME_DIRECTORIES)
    for name in RUNTIME_DIRECTORIES:
        assert (runtime.root / name).is_dir()

    assert RuntimeRoot.open(runtime.root) == runtime


def test_initialize_rejects_unknown_on_disk_version(tmp_path: Path) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    metadata = json.loads(runtime.metadata_path.read_text(encoding="utf-8"))
    metadata["layout_version"] = 999
    runtime.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(UnsupportedRuntimeVersionError):
        runtime.initialize()


def test_runtime_path_rejects_absolute_traversal_and_symlink(
    tmp_path: Path,
) -> None:
    runtime = RuntimeRoot(tmp_path / "runtime").initialize()
    with pytest.raises(RuntimeRootError):
        runtime.path("/etc/passwd")
    with pytest.raises(RuntimeRootError):
        runtime.path("../outside")

    outside = tmp_path / "outside"
    outside.mkdir()
    (runtime.root / "escape").symlink_to(outside)
    with pytest.raises(RuntimeRootError):
        runtime.path("escape/file")


def test_config_keeps_legacy_sessions_while_exposing_runtime(tmp_path: Path) -> None:
    cfg = Config(runtime_dir=tmp_path / "new", sessions_dir=tmp_path / "old")
    runtime = cfg.make_runtime_root()
    assert runtime.root == cfg.runtime_dir
    assert runtime.legacy_sessions_dir == cfg.sessions_dir
    assert not cfg.runtime_dir.exists()


def test_runtime_dir_does_not_change_v02_positional_config_order(tmp_path: Path) -> None:
    legacy_sessions = tmp_path / "legacy"
    cfg = Config(legacy_sessions)
    assert cfg.sessions_dir == legacy_sessions
    assert cfg.runtime_dir == Path("runtime")


def test_legacy_session_is_read_without_rewrite_then_copied_on_write(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / "sessions"
    parent = create_session(
        scenario="legacy",
        sessions_dir=legacy,
        session_id="sess_legacy01",
    )
    original_json = parent.session_json_path.read_bytes()
    runtime = RuntimeRoot(tmp_path / "runtime", legacy_sessions_dir=legacy).initialize()

    loaded = load_session(parent.session_id, runtime_root=runtime)
    assert loaded.directory == parent.directory
    assert loaded.state.scenario == "legacy"
    assert parent.session_json_path.read_bytes() == original_json
    assert not (runtime.sessions_dir / parent.session_id).exists()

    loaded.update_state(state="executing")
    assert loaded.directory == runtime.sessions_dir / parent.session_id
    assert loaded.state.state == "executing"
    assert parent.session_json_path.read_bytes() == original_json
    assert json.loads(loaded.session_json_path.read_text())["state"] == "executing"


def test_current_session_wins_over_legacy_copy(tmp_path: Path) -> None:
    legacy = tmp_path / "sessions"
    old = create_session(
        scenario="old",
        sessions_dir=legacy,
        session_id="sess_duplicate",
    )
    runtime = RuntimeRoot(tmp_path / "runtime", legacy_sessions_dir=legacy).initialize()
    current = create_session(
        scenario="new",
        runtime_root=runtime,
        session_id=old.session_id,
    )

    loaded = runtime.load_session(current.session_id)
    assert loaded.state.scenario == "new"
    assert [session.session_id for session in runtime.list_sessions()] == [current.session_id]


def test_session_ids_cannot_escape_any_sessions_root(tmp_path: Path) -> None:
    with pytest.raises(SessionEscapeError):
        load_session("../outside", sessions_dir=tmp_path)
