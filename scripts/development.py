#!/usr/bin/env python3
"""Read-only checkout diagnosis and explicit local hook installation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )


def hook_path() -> Path | None:
    if shutil.which("git") is None:
        return None
    result = git("rev-parse", "--git-path", "hooks/pre-push")
    if result.returncode:
        return None
    path = Path(result.stdout.strip())
    return path if path.is_absolute() else ROOT / path


def hook_installed(path: Path | None) -> bool:
    return bool(
        path
        and not path.is_symlink()
        and path.is_file()
        and os.access(path, os.X_OK)
        and path.read_bytes() == (ROOT / "scripts/pre-push").read_bytes()
    )


def doctor() -> int:
    failures = 0

    def report(ok: bool, label: str, fix: str) -> None:
        nonlocal failures
        print(f"PASS {label}" if ok else f"FIX  {label}: {fix}")
        failures += int(not ok)

    print("Sovereign Agent development prerequisites (read-only, offline)")
    for tool in ("git", "make", "uv"):
        executable = shutil.which(tool)
        version = ""
        if executable:
            try:
                result = subprocess.run(
                    [executable, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0:
                    version = result.stdout.splitlines()[0]
            except (OSError, subprocess.TimeoutExpired, IndexError):
                pass
        report(bool(version), f"{tool} {version}".strip(), f"install {tool} on PATH")
    pinned = (ROOT / ".python-version").read_text().strip()
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    report(python.is_file(), "development environment", "run make setup on a build host")
    if python.is_file():
        # Isolated interpreter: no user site/PYTHONPATH, bytecode writes, uv sync, or downloads.
        probe = """
import importlib.metadata, json, sys
names = ('pydantic', 'ruff', 'mypy', 'pytest', 'build')
versions = {}
for name in names:
    try:
        versions[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        versions[name] = None
print(json.dumps({'python': '.'.join(map(str, sys.version_info[:3])), 'packages': versions}))
"""
        try:
            result = subprocess.run(
                [str(python), "-I", "-B", "-c", probe],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            data = json.loads(result.stdout) if result.returncode == 0 else {}
        except (OSError, ValueError, subprocess.TimeoutExpired):
            data = {}
        version = data.get("python", "unavailable")
        report(
            version.startswith(pinned + "."),
            f"Python {version} (pinned {pinned} in .python-version)",
            "run make setup",
        )
        # Read the committed lock with the pinned development interpreter, not an installer.
        try:
            result = subprocess.run(
                [
                    str(python),
                    "-I",
                    "-B",
                    "-c",
                    "import json,sys,tomllib; "
                    "d=tomllib.load(open(sys.argv[1],'rb')); "
                    "print(json.dumps({p['name']:p.get('version') for p in d['package']}))",
                    str(ROOT / "uv.lock"),
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            locked = json.loads(result.stdout) if result.returncode == 0 else {}
        except (OSError, ValueError, subprocess.TimeoutExpired):
            locked = {}
        report(bool(locked), "committed dependency lock", "restore uv.lock and run make setup")
        for name in ("pydantic", "ruff", "mypy", "pytest", "build"):
            actual = data.get("packages", {}).get(name)
            report(
                bool(actual) and actual == locked.get(name),
                f"{name} matches uv.lock",
                "run make setup with the committed lock",
            )
    report(hook_installed(hook_path()), "main-push guard installed", "run make hooks")
    print("PASS no required credential environment variables (optional live providers only)")
    print("INFO optional live-only names: SOVEREIGN_AGENT_LIVE_ASSIGNMENTS, ANTHROPIC_API_KEY,")
    print("     ANTHROPIC_AUTH_TOKEN, CLAUDE_CODE_OAUTH_TOKEN, CODEX_API_KEY, CURSOR_API_KEY")
    print("PASS no required external volumes, services, or network for the default workflow")
    print("INFO make setup needs package-index access; doctor performs no network requests")
    print(
        "INFO git, make, and uv versions are reported; this repo pins Python and uv.lock packages"
    )
    return int(failures != 0)


def hooks() -> int:
    path = hook_path()
    if path is None:
        print("FIX run make hooks inside a Git checkout", file=sys.stderr)
        return 1
    if hook_installed(path):
        print("PASS main-push guard already installed")
        return 0
    if git("config", "--get", "core.hooksPath").returncode == 0:
        print(
            "FIX existing core.hooksPath requires owner integration; nothing replaced",
            file=sys.stderr,
        )
        return 1
    if path.is_symlink() or path.exists() or path.parent.is_symlink():
        print(
            "FIX existing hook or symlink requires owner integration; nothing replaced",
            file=sys.stderr,
        )
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write((ROOT / "scripts/pre-push").read_bytes())
        path.chmod(0o755)
    except FileExistsError:
        print("FIX hook appeared during installation; nothing replaced", file=sys.stderr)
        return 1
    print("PASS installed lightweight main-push guard; no build or test is run by this hook")
    return 0


def clean() -> int:
    paths = [
        ROOT / name for name in ("build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache")
    ]
    for path in paths:
        if path.is_symlink():
            print("FIX refusing a symlink in generated output; nothing removed", file=sys.stderr)
            return 1
        if path.exists() and (
            not path.is_dir()
            or git("check-ignore", "-q", "--", path.name).returncode != 0
            or git("ls-files", "--", path.name).stdout
        ):
            print(
                "FIX output is not an ignored, untracked directory; nothing removed",
                file=sys.stderr,
            )
            return 1
    for path in paths:
        if path.exists():
            shutil.rmtree(path)
            print(f"Removed generated {path.name}/")
    print("PASS generated outputs cleaned; virtual environment and learner data preserved")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("doctor", "hooks", "clean"):
        print("Usage: development.py doctor|hooks|clean", file=sys.stderr)
        sys.exit(2)
    sys.exit({"doctor": doctor, "hooks": hooks, "clean": clean}[sys.argv[1]]())
