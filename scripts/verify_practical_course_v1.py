"""Verify the complete practical release; --execute records fresh-kernel behavior."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import json
import platform
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDITION = ROOT / "book/always_on/practicals/ninety-minute-v1"
RECEIPT = EDITION / "verification-v1.json"
EXPECTED = {f"ch{chapter:02d}-{letter}" for chapter in range(1, 17) for letter in "ab"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantics(notebook):
    return [
        (cell["cell_type"], "".join(cell["source"]), cell.get("metadata", {}).get("tags", []))
        for cell in notebook["cells"]
    ]


def report(notebook, prefix="COURSE_REPORT="):
    found = []
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            for line in "".join(output.get("text", "")).splitlines():
                if line.startswith(prefix):
                    found.append(json.loads(line[len(prefix) :]))
    if len(found) != 1:
        raise AssertionError(f"expected one {prefix} record, observed {len(found)}")
    return found[0]


def run_notebook(notebook, folder, *, replay=False):
    import nbformat
    from nbclient import NotebookClient

    working = copy.deepcopy(notebook)
    if replay:
        # Same kernel, same notebook cells twice: expose hidden-state and replay defects.
        working.cells = [*working.cells, *copy.deepcopy(working.cells)]
        for index, cell in enumerate(working.cells):
            cell.id = f"replay-{index:04d}"
    working.cells.append(
        nbformat.v4.new_code_cell(
            "\nfor imported_name, imported_module in list(sys.modules.it"
            'ems()):\n    if imported_name.startswith(("sovereign_agent"'
            ', "reference_organizations")):\n        imported_file = get'
            'attr(imported_module, "__file__", None)\n        if importe'
            "d_file:\n            assert Path(imported_file).resolve().i"
            "s_relative_to(COURSE_ROOT.resolve()), imported_file\n"
        )
    )
    return NotebookClient(
        working,
        timeout=120,
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(folder)}},
        record_timing=False,
    ).execute()


def execute_one(path):
    import jupytext
    import nbformat

    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    assert semantics(notebook) == semantics(jupytext.read(path.with_suffix(".md"))), path
    identity = notebook.metadata.course.unit
    instructor = notebook.metadata.course.instructor
    assert identity in EXPECTED and notebook.metadata.course.planned_minutes == 90
    with tempfile.TemporaryDirectory(prefix=f"course-fresh-{identity}-") as folder:
        executed = run_notebook(notebook, folder)
        observed = report(executed)
        assert observed["unit"] == identity
        assert observed["transfer_passed"] is instructor
        assert observed["starting_evidence"] == (
            "SUPPLIED_REFERENCE" if identity.endswith("b") else "INDEPENDENT_UNIT_A"
        )
        if instructor:
            assert report(executed, "HOLDOUT_RESULT=") == {"unit": identity, "status": "PASSED"}
        submission = Path(folder) / "practical-work" / identity / f"{identity}-submission-v1.json"
        saved = json.loads(submission.read_text())
        assert saved["unit"] == identity and len(saved["transfer"]) >= 4
        assert all(item["passed"] for item in saved["transfer"]) is instructor
    with tempfile.TemporaryDirectory(prefix=f"course-replay-{identity}-") as folder:
        run_notebook(notebook, folder, replay=True)
    result = {
        "id": identity,
        "edition": "instructor" if instructor else "student",
        "notebook": str(path.relative_to(EDITION)),
        "notebookSha256": digest(path),
        "markdown": str(path.with_suffix(".md").relative_to(EDITION)),
        "markdownSha256": digest(path.with_suffix(".md")),
        "cells": len(notebook.cells),
        "freshKernel": "PASS",
        "sameKernelReplay": "PASS",
        "markdownParity": "PASS",
        "embeddedImports": "PASS",
        "coreHoldout": "PASS" if instructor else "NOT_DISTRIBUTED",
        "transfer": "PASS" if instructor else "EXPECTED_UNFINISHED",
    }
    print("VERIFIED", identity, result["edition"], flush=True)
    return result


def execute_handoff(chapter):
    import nbformat

    folder = EDITION / f"ch{chapter:02d}/instructor"
    unit_a = nbformat.read(folder / "unit-a-v1.ipynb", as_version=4)
    unit_b = nbformat.read(folder / "unit-b-v1.ipynb", as_version=4)
    with tempfile.TemporaryDirectory(prefix=f"course-handoff-ch{chapter:02d}-") as temporary:
        run_notebook(unit_a, temporary)
        artifact = (
            Path(temporary)
            / f"practical-work/ch{chapter:02d}-a/ch{chapter:02d}-unit-a-handoff-v1.json"
        )
        assert artifact.is_file(), artifact
        replacements = 0
        for cell in unit_b.cells:
            if cell.cell_type == "code" and "LEARNER_HANDOFF = None" in cell.source:
                cell.source = cell.source.replace(
                    "LEARNER_HANDOFF = None", f"LEARNER_HANDOFF = {str(artifact)!r}"
                )
                replacements += 1
        assert replacements == 1
        executed = run_notebook(unit_b, temporary)
        assert report(executed)["starting_evidence"] == "LEARNER_SELECTED"
        assert report(executed)["transfer_passed"] is True
    print("HANDOFF VERIFIED", chapter, flush=True)
    return {"chapter": chapter, "selectedLearnerHandoff": "PASS"}


def verify(path=RECEIPT):
    receipt = json.loads(Path(path).read_text())
    assert receipt["schemaVersion"] == 1, "unsupported receipt schema"
    units = receipt["notebooks"]
    identities = [(row["id"], row["edition"]) for row in units]
    assert len(identities) == 64 and set(identities) == {
        (identity, edition) for identity in EXPECTED for edition in ("student", "instructor")
    }, "notebook coverage drift"
    assert len(receipt["handoffs"]) == 16 and {
        row["chapter"] for row in receipt["handoffs"]
    } == set(range(1, 17)), "handoff coverage drift"
    assert all(row["selectedLearnerHandoff"] == "PASS" for row in receipt["handoffs"])
    actual_paths = {str(p.relative_to(EDITION)) for p in EDITION.glob("ch*/*/*.ipynb")}
    assert actual_paths == {row["notebook"] for row in units}, "unrecorded notebook"
    for row in units:
        assert row["freshKernel"] == row["sameKernelReplay"] == row["markdownParity"] == "PASS"
        assert row["embeddedImports"] == "PASS"
        assert row["transfer"] == (
            "PASS" if row["edition"] == "instructor" else "EXPECTED_UNFINISHED"
        )
        assert row["coreHoldout"] == (
            "PASS" if row["edition"] == "instructor" else "NOT_DISTRIBUTED"
        )
        for field, hash_field in (("notebook", "notebookSha256"), ("markdown", "markdownSha256")):
            candidate = (EDITION / row[field]).resolve()
            assert candidate.is_relative_to(EDITION.resolve()), "path escapes edition"
            assert digest(candidate) == row[hash_field], "verified classroom bytes changed"
        notebook = json.loads((EDITION / row["notebook"]).read_text())
        assert notebook["metadata"]["course"]["planned_minutes"] == 90
        assert notebook["metadata"]["course"]["unit"] == row["id"]
        assert len(notebook["cells"]) == row["cells"]
        tags = {
            tag for cell in notebook["cells"] for tag in cell.get("metadata", {}).get("tags", [])
        }
        assert {"embedded-runtime", "learner-owned", "transfer-owned", "course-report"} <= tags
        assert ("instructor-check" in tags) is (row["edition"] == "instructor")
    print(
        "PRACTICAL COURSE: 32 student units, 32 worked units, 16 handoffs; verified bytes intact."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--chapters", nargs="*", type=int)
    args = parser.parse_args()
    if not args.execute:
        verify()
        return
    paths = sorted(EDITION.glob("ch*/*/*.ipynb"))
    chapters = args.chapters or list(range(1, 17))
    paths = [p for p in paths if int(p.parts[-3][2:]) in chapters]
    failures, notebooks, handoffs = [], [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(execute_one, path): str(path) for path in paths}
        for future in concurrent.futures.as_completed(futures):
            try:
                notebooks.append(future.result())
            except Exception as error:
                import traceback

                log = Path(tempfile.gettempdir()) / (
                    "course-failure-"
                    + hashlib.sha256(futures[future].encode()).hexdigest()[:10]
                    + ".log"
                )
                log.write_text(traceback.format_exc())
                failures.append(
                    {"path": futures[future], "error": str(error)[-400:], "log": str(log)}
                )
                print("FAILED", futures[future], log, flush=True)
        handoff_futures = {pool.submit(execute_handoff, chapter): chapter for chapter in chapters}
        for future in concurrent.futures.as_completed(handoff_futures):
            try:
                handoffs.append(future.result())
            except Exception:
                import traceback

                log = (
                    Path(tempfile.gettempdir())
                    / f"course-handoff-failure-{handoff_futures[future]:02d}.log"
                )
                log.write_text(traceback.format_exc())
                failures.append({"chapter": handoff_futures[future], "log": str(log)})
                print("HANDOFF FAILED", handoff_futures[future], log, flush=True)
    if failures:
        print(json.dumps(failures, indent=2))
        raise SystemExit(1)
    if args.chapters:
        print("Selected chapter checks passed; no complete-release receipt written.")
        return
    receipt = {
        "schemaVersion": 1,
        "created": "2026-09-09",
        "python": platform.python_version(),
        "plannedMinutesPerUnit": 90,
        "notebooks": sorted(notebooks, key=lambda row: (row["id"], row["edition"])),
        "handoffs": sorted(handoffs, key=lambda row: row["chapter"]),
        "limits": [
            "Classroom duration and learning outcomes remain unobserved.",
            "Local Python 3.14 kernels tested; no hosted-notebook UI claim.",
            (
                "Offline fixtures do not certify live providers, phone deli"
                "very, OS containment or host operation."
            ),
        ],
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    verify()


if __name__ == "__main__":
    main()
