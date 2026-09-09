"""Run preserved edition contracts in an isolated, explicit historical topology.

The archive is copied unchanged; no compatibility directory is created in book/.
Current source and tests are copied, so this also catches runtime regressions that
would break readers of the historical editions. Active edition checks are separate.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/archive/book-20260909"
HISTORICAL_TESTS = (
    "test_always_on_book.py",
    "test_book_snippets_verifier.py",
    "test_book_advanced_exercises.py",
    "test_book_verifiers.py",
    "test_educator_v2_safety.py",
    "test_phone_checkpoint.py",
    "test_ch01_exercise_holdouts_v1.py",
    "test_exercise_solution_scan_v1.py",
    "test_ch09_exercise_holdouts_v1.py",
    "test_zeocore_interop.py",
    "test_curriculum_jupytext_frontmatter_v1.py",
    "test_ch12_request_eval_v1.py",
    "test_exercise_release_v5.py",
    "test_educator_curriculum.py",
    "test_educator_v2_runtime.py",
    "test_practical_course_v1.py",
    "test_telegram_identity_setup.py",
    "test_reader_construction.py",
    "test_ch03_exercise_holdouts_v1.py",
    "test_educator_ch01.py",
    "test_publication_contract.py",
    "test_providers.py",
    "test_wave2_source_tasks_v1.py",
    "test_educator_ch01_harness.py",
)
HISTORICAL_GATES = (
    "verify_curriculum_v2.py",
    "verify_book_snippets.py",
    "verify_book_depth.py",
    "verify_book_structure_v1.py",
    "verify_always_on_v1.py",
    "verify_publication_v2.py",
    "verify_exercise_release_v5.py",
    "verify_practical_course_v1.py",
    "package_practical_course_v1.py",
    "verify_book_labs.py",
)


def verify_archive() -> None:
    inventory = json.loads((ROOT / "docs/archive/book-20260909-inventory.json").read_text())
    assert inventory["schemaVersion"] == 1
    rows = inventory["files"]
    assert len(rows) == inventory["fileCount"] == 686, "historical archive inventory changed"
    actual = {
        str(path.relative_to(ROOT))
        for path in ARCHIVE.rglob("*")
        if path.is_file()
        and not {"__pycache__", ".ruff_cache", ".pytest_cache"}.intersection(path.parts)
        and path.suffix != ".pyc"
    }
    assert actual == {row["archivedPath"] for row in rows}, "historical archive membership changed"
    blobs = {}
    if (ROOT / ".git").exists():
        tree = subprocess.run(
            ["git", "ls-tree", "-rz", "--full-tree", inventory["sourceCommit"], "--", "book"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        for record in tree.split(b"\0"):
            if record:
                metadata, path = record.split(b"\t", 1)
                blobs[path.decode()] = metadata.split()[2].decode()
        assert set(blobs) == {row["sourcePath"] for row in rows}, "source snapshot membership drift"
    for row in rows:
        path = ROOT / row["archivedPath"]
        assert path.resolve().is_relative_to(ARCHIVE.resolve()) and not path.is_symlink()
        relative = path.relative_to(ARCHIVE)
        assert row["sourcePath"] == "book/" + relative.as_posix()
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == row["sha256"], (
            f"archived bytes changed: {relative}"
        )
        assert len(data.splitlines()) == row["lines"], f"archived line count changed: {relative}"
        if blobs:
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            assert hashlib.sha1(blob).hexdigest() == blobs[row["sourcePath"]], (
                "archive does not match its original Git object",
                relative,
            )
    print(
        "HISTORICAL ARCHIVE: all 686 files match inventory"
        + (" and pinned Git objects." if blobs else "."),
        flush=True,
    )


@contextlib.contextmanager
def projection():
    if not ARCHIVE.is_dir():
        raise FileNotFoundError(f"historical book archive is missing: {ARCHIVE}")
    verify_archive()
    with tempfile.TemporaryDirectory(prefix="sovereign-historical-book-") as temporary:
        root = Path(temporary)
        ignore = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")
        shutil.copytree(ARCHIVE, root / "book", ignore=ignore)
        for name in ("src", "scripts", "tests"):
            shutil.copytree(ROOT / name, root / name, ignore=ignore)
        shutil.copytree(
            ROOT / "docs",
            root / "docs",
            ignore=shutil.ignore_patterns("archive", "__pycache__", "*.pyc"),
        )
        for name in ("pyproject.toml", "uv.lock", "README.md"):
            shutil.copy2(ROOT / name, root / name)
        if (ROOT / ".git").exists():
            git_dir = subprocess.run(
                ["git", "rev-parse", "--absolute-git-dir"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            # Historical receipt gates only read pinned Git objects. They do not
            # stage, commit or mutate this checkout's repository metadata.
            (root / ".git").write_text(f"gitdir: {git_dir}\n")
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
        yield root, env


def run(mode: str) -> None:
    with projection() as (root, env):
        if mode == "tests":
            commands = [
                [sys.executable, "-m", "pytest", "-q", *[f"tests/{p}" for p in HISTORICAL_TESTS]]
            ]
        elif mode == "labs":
            commands = [[sys.executable, "scripts/verify_book_labs.py"]]
        elif mode == "gates":
            commands = [
                [
                    sys.executable,
                    f"scripts/{name}",
                    *(["--verify"] if name.startswith("package_") else []),
                ]
                for name in HISTORICAL_GATES
            ]
        else:
            raise ValueError(f"unknown historical verification mode: {mode}")
        for command in commands:
            print("HISTORICAL ARCHIVE:", " ".join(command), flush=True)
            subprocess.run(command, cwd=root, env=env, check=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("tests", "gates", "labs"))
    run(parser.parse_args().mode)
