#!/usr/bin/env python3
"""Independently verify the complete book release against committed source bytes."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / "book/always_on/exercises/release-v4.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(release_path: Path = RELEASE) -> None:
    release = json.loads(release_path.read_text())
    require(
        set(release)
        == {
            "schemaVersion",
            "status",
            "pedagogy",
            "sourceCommit",
            "environmentLock",
            "environmentLockSha256",
            "studentFiles",
            "instructorFiles",
            "runtimeFiles",
            "units",
            "executionLimitations",
        },
        "unknown or missing release field",
    )
    require(release["schemaVersion"] == 3, "unknown release schema")
    require(release["status"] == "DRAFT", "release overstates acceptance")
    require(release["pedagogy"] == "UNREVIEWED", "human review receipt required")
    commit = release["sourceCommit"]
    require(
        isinstance(commit, str) and re.fullmatch(r"[a-f0-9]{40}", commit) is not None, "bad commit"
    )
    require(release["environmentLock"] == "uv.lock", "unexpected environment lock")
    seen = set()
    inventories = {}
    for group in ("studentFiles", "instructorFiles", "runtimeFiles"):
        inventory = {}
        require(isinstance(release[group], list) and bool(release[group]), "empty file inventory")
        for row in release[group]:
            require(set(row) == {"path", "sha256"}, "unknown inventory field")
            path = row["path"]
            require(isinstance(path, str) and path not in seen, "duplicate file")
            target = ROOT / path
            require(not Path(path).is_absolute() and ".." not in Path(path).parts, "unsafe path")
            require(target.is_file() and target.resolve().is_relative_to(ROOT), "missing file")
            require(digest(target.read_bytes()) == row["sha256"], f"working file drift: {path}")
            saved = subprocess.run(
                ["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, check=False
            )
            require(
                saved.returncode == 0 and digest(saved.stdout) == row["sha256"],
                f"commit drift: {path}",
            )
            if group == "studentFiles":
                require(
                    not any(p in {"solutions", "holdouts"} for p in Path(path).parts), "answer leak"
                )
                if path.endswith((".ipynb", ".md")):
                    require(
                        not re.search(
                            r"(?:runpy\.run_path|exec|import).*solutions", target.read_text()
                        ),
                        "solution import",
                    )
            seen.add(path)
            inventory[path] = row["sha256"]
        inventories[group] = inventory
    lock_bytes = (ROOT / "uv.lock").read_bytes()
    require(digest(lock_bytes) == release["environmentLockSha256"], "lock drift")
    saved_lock = subprocess.run(["git", "show", f"{commit}:uv.lock"], cwd=ROOT, capture_output=True)
    require(saved_lock.returncode == 0 and saved_lock.stdout == lock_bytes, "committed lock drift")
    expected_units = {f"ch{chapter:02d}-{letter}" for chapter in range(1, 17) for letter in "ab"}
    require(len(release["units"]) == 32, "wrong unit count")
    require({row["id"] for row in release["units"]} == expected_units, "unit set drift")
    declared_student_paths = set()
    for row in release["units"]:
        require(
            set(row)
            == {
                "id",
                "canonicalSource",
                "canonicalSha256",
                "notebook",
                "notebookSha256",
                "semanticDigestVersion",
                "semanticSha256",
                "freshKernel",
                "execution",
                "instructorEvidence",
            },
            "unknown unit field",
        )
        for key, hash_key in (
            ("canonicalSource", "canonicalSha256"),
            ("notebook", "notebookSha256"),
        ):
            require(
                inventories["studentFiles"].get(row[key]) == row[hash_key],
                "unit outside student inventory",
            )
            declared_student_paths.add(row[key])
        notebook = json.loads((ROOT / row["notebook"]).read_text())
        stable = []
        code_count = 0
        for cell in notebook["cells"]:
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            tags = cell.get("metadata", {}).get("tags", [])
            require(not any("solution" in tag.casefold() for tag in tags), "solution cell")
            if cell["cell_type"] == "code":
                code_count += 1
                require(
                    cell.get("outputs", []) == [] and cell.get("execution_count") is None,
                    "student output leak",
                )
            stable.append({"cell_type": cell["cell_type"], "source": source, "tags": tags})
        require(row["semanticDigestVersion"] == 1, "unknown semantic contract")
        require(
            digest(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode())
            == row["semanticSha256"],
            "semantic drift",
        )
        execution = row["execution"]
        require(
            set(execution)
            == {
                "attempted",
                "completed",
                "failed",
                "skipped",
                "capturedOutputBytes",
                "exerciseReport",
            },
            "unknown execution field",
        )
        require(row["freshKernel"] is True and code_count > 0, "missing kernel evidence")
        require(
            all(
                type(execution[key]) is int and execution[key] >= 0
                for key in ("attempted", "completed", "failed", "skipped")
            ),
            "invalid execution counter type",
        )
        require(execution["attempted"] == execution["completed"] == code_count, "cell count drift")
        require(execution["failed"] == execution["skipped"] == 0, "incomplete notebook execution")
        require(
            type(execution["capturedOutputBytes"]) is int
            and 0 <= execution["capturedOutputBytes"] <= 1_000_000,
            "invalid output observation",
        )
        require(execution["exerciseReport"]["unit"] == row["id"], "wrong student report")
        evidence = row["instructorEvidence"]
        require(
            set(evidence)
            == {"solution", "solutionSha256", "holdout", "holdoutSha256", "holdoutResult"},
            "unknown instructor field",
        )
        for key in ("solution", "holdout"):
            require(
                inventories["instructorFiles"].get(evidence[key]) == evidence[key + "Sha256"],
                "instructor inventory drift",
            )
        require(
            evidence["holdoutResult"] == {"unit": row["id"], "status": "PASSED"},
            "holdout result drift",
        )
    for path in inventories["studentFiles"]:
        if path.endswith(".ipynb"):
            require(path in declared_student_paths, "undeclared student notebook")
    require(len(declared_student_paths) == 64, "units reuse another unit's artifacts")
    require(
        set(inventories["studentFiles"])
        == declared_student_paths
        | {
            "book/always_on/exercises/companion-index-v2.md",
            "book/always_on/exercises/source_tasks_v1.py",
            "book/always_on/exercises/source-tasks-v1.json",
        },
        "student support inventory drift",
    )
    required_runtime = {
        "book/always_on/educator/runtime_labs_v1.py",
        "book/always_on/educator/runtime-experiments-v1.json",
        "scripts/build_exercise_release_v3.py",
        "scripts/build_exercise_release_v4.py",
        "scripts/verify_exercise_release_v4.py",
        "tests/test_wave2_source_tasks_v1.py",
    }
    required_runtime.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*.py"))
    for folder in ("checkpoints", "learner", "skills"):
        required_runtime.update(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "book/always_on" / folder).rglob("*")
            if p.is_file() and p.suffix in {".py", ".toml"}
        )
    require(set(inventories["runtimeFiles"]) == required_runtime, "runtime inventory drift")
    expected_instructor = {
        row["instructorEvidence"][key]
        for row in release["units"]
        for key in ("solution", "holdout")
    }
    expected_instructor.update(
        f"book/always_on/exercises/ch{chapter:02d}/holdouts/runtime-transfer-v1.py"
        for chapter in range(1, 17)
        if chapter not in {1, 3, 9}
    )
    require(
        set(inventories["instructorFiles"]) == expected_instructor, "hidden case inventory drift"
    )


if __name__ == "__main__":
    verify()
    print(
        "EXERCISE RELEASE: 32 units, committed bytes, execution and instructor holdouts verified."
    )
    print("Classroom outcomes and pedagogical acceptance remain separate human evidence.")
