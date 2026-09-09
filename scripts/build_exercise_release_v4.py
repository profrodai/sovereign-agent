#!/usr/bin/env python3
"""Build all sixteen chapters using the pilot's locked conversion and execution path."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from build_exercise_release_v3 import (
    EXERCISES,
    ROOT,
    Unit,
    convert,
    execute,
    marker,
    outputs_bytes,
    relative,
    semantic_digest,
    sha256,
    verify_solution,
)
from build_exercise_release_v3 import (
    UNITS as PILOT_UNITS,
)

CHAPTERS = (2, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16)
UNITS = tuple(
    sorted(
        (
            *PILOT_UNITS,
            *(
                Unit(
                    f"ch{chapter:02d}-{letter}",
                    EXERCISES / f"ch{chapter:02d}/unit-{letter}-{slug}-v1.md",
                    EXERCISES / f"ch{chapter:02d}/unit-{letter}-{slug}-v1.ipynb",
                    EXERCISES / f"ch{chapter:02d}/solutions/unit-{letter}-solution-v1.py",
                    EXERCISES / f"ch{chapter:02d}/holdouts/unit-{letter}-holdout-v1.py",
                )
                for chapter in CHAPTERS
                for letter, slug in (("a", "build-connect"), ("b", "repair-transfer"))
            ),
        ),
        key=lambda unit: unit.identity,
    )
)


def main() -> int:
    jupytext = shutil.which("jupytext")
    if not jupytext:
        raise RuntimeError("run with the locked authoring dependency group")
    started = time.monotonic()
    rows = []
    measurements = []
    with tempfile.TemporaryDirectory(prefix="lucy-full-book-exercises-") as temporary:
        for unit in UNITS:
            unit_started = time.monotonic()
            notebook = convert(unit, jupytext)
            work = Path(temporary) / unit.identity.split("-")[0]
            work.mkdir(exist_ok=True)
            executed = execute(notebook, work)
            report = marker(executed, "EXERCISE_REPORT=")
            evidence = verify_solution(unit, notebook, work)
            if evidence != {"unit": unit.identity, "status": "PASSED"}:
                raise ValueError(f"wrong instructor holdout identity: {unit.identity}")
            rows.append(
                {
                    "id": unit.identity,
                    "canonicalSource": relative(unit.source),
                    "canonicalSha256": sha256(unit.source),
                    "notebook": relative(unit.notebook),
                    "notebookSha256": sha256(unit.notebook),
                    "semanticDigestVersion": 1,
                    "semanticSha256": semantic_digest(notebook),
                    "freshKernel": True,
                    "execution": {
                        "attempted": sum(c["cell_type"] == "code" for c in executed["cells"]),
                        "completed": sum(c["cell_type"] == "code" for c in executed["cells"]),
                        "failed": 0,
                        "skipped": 0,
                        "capturedOutputBytes": outputs_bytes(executed),
                        "exerciseReport": report,
                    },
                    "instructorEvidence": {
                        "solution": relative(unit.solution),
                        "solutionSha256": sha256(unit.solution),
                        "holdout": relative(unit.holdout),
                        "holdoutSha256": sha256(unit.holdout),
                        "holdoutResult": evidence,
                    },
                }
            )
            measurements.append(
                {
                    "unit": unit.identity,
                    "automatedSeconds": round(time.monotonic() - unit_started, 3),
                }
            )
            print(f"VERIFIED {unit.identity}", flush=True)
    students = {relative(p) for u in UNITS for p in (u.source, u.notebook)}
    students.update(
        {
            "book/always_on/exercises/companion-index-v2.md",
            "book/always_on/exercises/source_tasks_v1.py",
            "book/always_on/exercises/source-tasks-v1.json",
        }
    )
    instructor = {relative(p) for u in UNITS for p in (u.solution, u.holdout)}
    instructor.update(
        f"book/always_on/exercises/ch{n:02d}/holdouts/runtime-transfer-v1.py" for n in CHAPTERS
    )
    support = {
        "book/always_on/educator/runtime_labs_v1.py",
        "book/always_on/educator/runtime-experiments-v1.json",
        "scripts/build_exercise_release_v3.py",
        "scripts/build_exercise_release_v4.py",
        "scripts/verify_exercise_release_v4.py",
        "tests/test_wave2_source_tasks_v1.py",
    }
    # Bind runtime dependencies as well as notebooks to the reviewed source revision.
    support.update(relative(p) for p in (ROOT / "src").rglob("*.py"))
    for folder in ("checkpoints", "learner", "skills"):
        support.update(
            relative(p)
            for p in (ROOT / "book/always_on" / folder).rglob("*")
            if p.is_file() and p.suffix in {".py", ".toml"}
        )
    release = {
        "schemaVersion": 3,
        "status": "DRAFT",
        "pedagogy": "UNREVIEWED",
        "sourceCommit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "environmentLock": "uv.lock",
        "environmentLockSha256": sha256(ROOT / "uv.lock"),
        "studentFiles": [{"path": p, "sha256": sha256(ROOT / p)} for p in sorted(students)],
        "instructorFiles": [{"path": p, "sha256": sha256(ROOT / p)} for p in sorted(instructor)],
        "runtimeFiles": [{"path": p, "sha256": sha256(ROOT / p)} for p in sorted(support)],
        "units": rows,
        "executionLimitations": [
            "trusted local course code; requires the pinned full repository checkout",
            "per-cell timeout is not a whole-run deadline",
            "captured output limit is checked after execution",
            "process, network, and descendant isolation unavailable",
            "starter execution and instructor holdouts do not establish learner mastery",
            "Unit B instructor execution consumes the reference Unit A handoff",
        ],
    }
    (EXERCISES / "release-v4.json").write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"automatedReleaseSeconds": round(time.monotonic() - started, 3), "units": measurements}
        )
    )
    print("Author active minutes and classroom outcomes were not measured by this command.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
