"""The development entry points diagnose safely and protect the real push boundary."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def command(root: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=root, input=stdin, capture_output=True, text=True, check=False
    )


@pytest.fixture
def checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    root = tmp_path / "checkout"
    (root / "scripts").mkdir(parents=True)
    for name in ("development.py", "pre-push"):
        shutil.copyfile(REPO / "scripts" / name, root / "scripts" / name)
    for name in (".python-version", "uv.lock", ".gitignore"):
        shutil.copyfile(REPO / name, root / name)
    assert command(root, "git", "init", "-b", "main").returncode == 0
    return root


def helper(root: Path, action: str) -> subprocess.CompletedProcess[str]:
    return command(root, sys.executable, "-B", "scripts/development.py", action)


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_doctor_is_read_only_and_never_prints_credentials(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = "never-print-this-private-value"
    monkeypatch.setenv("ANTHROPIC_API_KEY", sentinel)
    monkeypatch.setenv("CODEX_API_KEY", sentinel)
    before = snapshot(checkout)
    result = helper(checkout, "doctor")
    assert result.returncode == 1
    assert "FIX  development environment" in result.stdout
    assert "FIX  main-push guard installed" in result.stdout
    assert sentinel not in result.stdout + result.stderr
    assert snapshot(checkout) == before
    assert not (checkout / ".venv").exists()


def test_hooks_install_idempotently_and_enforce_actual_git_push(
    checkout: Path, tmp_path: Path
) -> None:
    assert helper(checkout, "hooks").returncode == 0
    hook = checkout / ".git/hooks/pre-push"
    before = hook.read_bytes()
    assert helper(checkout, "hooks").returncode == 0
    assert hook.read_bytes() == before
    assert os.access(hook, os.X_OK)
    assert command(checkout, "git", "add", ".").returncode == 0
    assert (
        command(
            checkout,
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "Initial fixture",
        ).returncode
        == 0
    )
    remote = tmp_path / "remote.git"
    assert command(tmp_path, "git", "init", "--bare", str(remote)).returncode == 0
    assert command(checkout, "git", "remote", "add", "origin", str(remote)).returncode == 0
    refused = command(checkout, "git", "push", "origin", "HEAD:refs/heads/main")
    assert refused.returncode != 0
    assert "Refusing a direct update to main" in refused.stderr
    assert command(checkout, "git", "push", "origin", "HEAD:refs/heads/work").returncode == 0


def test_main_deletion_and_mixed_push_are_refused(checkout: Path) -> None:
    hook = checkout / "scripts/pre-push"
    for updates in (
        "(delete) 0000 refs/heads/main 1111\n",
        "refs/heads/work 1111 refs/heads/work 0000\nrefs/heads/main 1111 refs/heads/main 0000\n",
    ):
        assert command(checkout, "sh", str(hook), stdin=updates).returncode == 1
    assert (
        command(checkout, "sh", str(hook), stdin="refs/tags/v1 1111 refs/tags/v1 0000\n").returncode
        == 0
    )


def test_hooks_preserve_custom_policy_and_existing_hooks(checkout: Path) -> None:
    hook = checkout / ".git/hooks/pre-push"
    hook.write_text("#!/bin/sh\nprintf 'existing policy'\n")
    before = hook.read_bytes()
    assert helper(checkout, "hooks").returncode == 1
    assert hook.read_bytes() == before
    hook.unlink()
    custom = checkout / "custom-hooks"
    custom.mkdir()
    assert command(checkout, "git", "config", "core.hooksPath", str(custom)).returncode == 0
    assert helper(checkout, "hooks").returncode == 1
    assert list(custom.iterdir()) == []


def test_clean_refuses_symlinks_before_removing_anything(checkout: Path, tmp_path: Path) -> None:
    (checkout / "build").mkdir()
    (checkout / "build/artifact").write_text("generated")
    outside = tmp_path / "learner-data"
    outside.mkdir()
    (outside / "receipt").write_text("preserve")
    (checkout / "dist").symlink_to(outside, target_is_directory=True)
    assert helper(checkout, "clean").returncode == 1
    assert (checkout / "build/artifact").read_text() == "generated"
    assert (outside / "receipt").read_text() == "preserve"
