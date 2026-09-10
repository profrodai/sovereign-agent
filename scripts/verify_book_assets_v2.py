"""Verify the active four-asset edition independently from historical archives.

--execute runs every active exercise and solution in fresh kernels, repeats each
in the same kernel, and checks every selected A-to-B handoff. The saved receipt
binds those observations to exact notebook and Markdown bytes. Planned chapters
remain explicitly unwritten; a green layout gate is not publication acceptance.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import platform
import re
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__:
    from . import book_distribution_v1 as distribution
else:
    import book_distribution_v1 as distribution


ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
ASSETS = ("textbook", "exercises", "solutions", "educator")
PLANNED = {4, 7, 13}
AVAILABLE = set(range(1, 20)) - PLANNED
EXPECTED = {f"ch{chapter:02d}-{letter}" for chapter in AVAILABLE for letter in "ab"}
RECEIPT = ROOT / "docs/evidence/book-four-assets/verification-v2.json"
LEGACY = runpy.run_path(str(ROOT / "scripts/verify_practical_course_v1.py"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(book: Path, relative: str) -> Path:
    candidate = book / relative
    assert not Path(relative).is_absolute() and ".." not in Path(relative).parts, relative
    assert candidate.is_file() and not candidate.is_symlink(), relative
    assert candidate.resolve().is_relative_to(book.resolve()), relative
    return candidate


def notebook_paths(book: Path = BOOK) -> list[Path]:
    return sorted(
        path for asset in ("exercises", "solutions") for path in (book / asset).glob("ch*/*.ipynb")
    )


def verify_layout(book: Path = BOOK) -> dict:
    assert {p.name for p in book.iterdir() if p.is_dir()} == set(ASSETS), (
        "book must have exactly four audience directories"
    )
    local_file(book, "README.md")
    distribution.verify_unique_names(book)
    manifest = json.loads(local_file(book, "textbook/BOOK.json").read_text())
    assert manifest["schemaVersion"] == 3
    chapters = manifest["chapters"]
    assert [row["number"] for row in chapters] == list(range(1, 20)), "chapter coverage drift"
    assert len({row["lessonId"] for row in chapters}) == 19, "duplicate stable lesson identity"
    assert {row["number"] for row in chapters if row["status"] == "PLANNED"} == PLANNED
    for asset in ASSETS:
        local_file(book, f"{asset}/README.md")
        local_file(book, f"{asset}/{distribution.start_name(asset)}")
        actual = {p.name for p in (book / asset).glob("ch[0-9]*") if p.is_dir()}
        assert actual == {f"ch{n:02d}" for n in range(1, 20)}, f"{asset}: chapter coverage drift"
    for row in chapters:
        chapter = row["number"]
        prefix = f"ch{chapter:02d}"
        assert row["path"] == f"{prefix}/{distribution.chapter_name(chapter, 'textbook')}"
        assert row["status"] in {"DRAFT", "PLANNED"}, "publication acceptance is not established"
        for asset in ASSETS:
            readme = local_file(
                book, f"{asset}/{prefix}/{distribution.chapter_name(chapter, asset)}"
            )
            assert re.search(r"^# .+", readme.read_text(), re.M), readme
            if chapter in PLANNED:
                assert "PLANNED" in readme.read_text(), f"{readme}: planned status is hidden"
                assert not any(
                    p.suffix in {".ipynb", ".py", ".zip"} for p in readme.parent.rglob("*")
                ), f"{readme}: planned chapter ships fake executable material"
        if chapter in PLANNED:
            assert row["checkpoint"] is None
            continue
        assert row["checkpoint"] == f"checkpoints/{distribution.checkpoint_name(chapter)}"
        local_file(book, f"textbook/{row['checkpoint']}")
        local_file(book, f"educator/{prefix}/{distribution.guide_name(chapter)}")
        for asset in ("exercises", "solutions"):
            expected_names = {distribution.unit_name(chapter, letter, asset) for letter in "ab"}
            assert {p.name for p in (book / asset / prefix).glob("*.ipynb")} == expected_names
            for letter in "ab":
                path = distribution.unit_path(book, chapter, letter, asset)
                local_file(book, str(path.relative_to(book)))
                local_file(book, str(path.with_suffix(".md").relative_to(book)))
                notebook = json.loads(path.read_text())
                course = notebook["metadata"]["course"]
                assert course["unit"] == f"{prefix}-{letter}", "notebook chapter identity drift"
                assert course["resource_id"] == path.stem, "resource name drift"
                assert course["book_url"] == distribution.BOOK_URL
                assert course["community_url"] == distribution.COMMUNITY_URL
                assert course["source_url"] == distribution.SOURCE_URL
                assert course["distribution_version"] == distribution.EDITION
                header = "".join(notebook["cells"][0]["source"])
                footer = "".join(notebook["cells"][-1]["source"])
                distribution.verify_attribution(header)
                assert "Keep building with Prof Rod" in footer, "missing closing invitation"
                assert distribution.COMMUNITY_URL in footer and distribution.BOOK_URL in footer
                assert course["planned_minutes"] == 90
                assert course["instructor"] is (asset == "solutions"), "solution distribution leak"
                tags = {
                    tag
                    for cell in notebook["cells"]
                    for tag in cell.get("metadata", {}).get("tags", [])
                }
                assert {
                    "embedded-runtime",
                    "learner-owned",
                    "transfer-owned",
                    "course-report",
                } <= tags
                assert ("instructor-check" in tags) is (asset == "solutions")
                educator_kind = "solutions" if asset == "solutions" else "student"
                for suffix in (".ipynb", ".md"):
                    educator_copy = local_file(
                        book,
                        f"educator/{prefix}/{educator_kind}/"
                        + str(
                            Path(
                                distribution.unit_name(chapter, letter, asset, educator=True)
                            ).with_suffix(suffix)
                        ),
                    )
                    assert educator_copy.read_bytes() == path.with_suffix(suffix).read_bytes(), (
                        "educator teaching copy diverged from its companion",
                        educator_copy,
                    )
    for path in book.rglob("*.md"):
        distribution.verify_attribution(path.read_text())
    for pattern in ("*.py", "*.toml"):
        for path in book.rglob(pattern):
            source = path.read_text()
            assert "Join the Prof Rod learner community" in source, path
            for url in (distribution.BOOK_URL, distribution.COMMUNITY_URL, distribution.SOURCE_URL):
                assert url in source, path
    assert len(notebook_paths(book)) == 64
    return manifest


def verify_textbook() -> None:
    manifest = verify_layout()
    checker = runpy.run_path(str(ROOT / "scripts/verify_book_snippets.py"))["check_chapter"]
    examples = pairs = 0
    for row in manifest["chapters"]:
        if row["status"] == "PLANNED":
            continue
        count, matched, errors = checker(BOOK / "textbook" / row["path"])
        assert not errors, "\n".join(errors)
        assert count >= 2 and matched >= 2, row["lessonId"]
        examples += count
        pairs += matched
        subprocess.run(
            [sys.executable, str(BOOK / "textbook" / row["checkpoint"])],
            cwd=ROOT,
            check=True,
            timeout=60,
        )
    print(f"ACTIVE TEXTBOOK: 16 draft checkpoints; {examples} examples and {pairs} output pairs.")
    print("Chapters 4, 7 and 13 remain PLANNED. No publication or classroom-quality acceptance.")


def execute_one(path: Path) -> dict:
    import jupytext
    import nbformat

    notebook_hash = digest(path)
    markdown_hash = digest(path.with_suffix(".md"))
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    assert LEGACY["semantics"](notebook) == LEGACY["semantics"](
        jupytext.read(path.with_suffix(".md"))
    )
    identity = notebook.metadata.course.unit
    instructor = notebook.metadata.course.instructor
    assert identity in EXPECTED
    with tempfile.TemporaryDirectory(prefix=f"active-book-{identity}-") as folder:
        executed = LEGACY["run_notebook"](notebook, folder)
        observed = LEGACY["report"](executed)
        assert observed["unit"] == identity
        assert observed["transfer_passed"] is instructor
        assert observed["starting_evidence"] == (
            "SUPPLIED_REFERENCE" if identity.endswith("b") else "INDEPENDENT_UNIT_A"
        )
        if instructor:
            assert LEGACY["report"](executed, "HOLDOUT_RESULT=") == {
                "unit": identity,
                "status": "PASSED",
            }
        saved = json.loads(
            (
                Path(folder) / "practical-work" / identity / f"{identity}-submission-v1.json"
            ).read_text()
        )
        assert saved["unit"] == identity and len(saved["transfer"]) >= 4
        assert all(item["passed"] for item in saved["transfer"]) is instructor
    with tempfile.TemporaryDirectory(prefix=f"active-replay-{identity}-") as folder:
        LEGACY["run_notebook"](notebook, folder, replay=True)
    assert digest(path) == notebook_hash and digest(path.with_suffix(".md")) == markdown_hash, (
        "notebook sources changed during execution",
        path,
    )
    print("ACTIVE VERIFIED", identity, "solution" if instructor else "exercise", flush=True)
    return {
        "id": identity,
        "asset": "solutions" if instructor else "exercises",
        "notebook": str(path.relative_to(BOOK)),
        "notebookSha256": notebook_hash,
        "markdown": str(path.with_suffix(".md").relative_to(BOOK)),
        "markdownSha256": markdown_hash,
        "freshKernel": "PASS",
        "sameKernelReplay": "PASS",
        "markdownParity": "PASS",
        "embeddedImports": "PASS",
        "transfer": "PASS" if instructor else "EXPECTED_UNFINISHED",
        "coreHoldout": "PASS" if instructor else "NOT_DISTRIBUTED",
    }


def execute_handoff(chapter: int) -> dict:
    import nbformat

    unit_a = nbformat.read(distribution.unit_path(BOOK, chapter, "a", "solutions"), as_version=4)
    unit_b = nbformat.read(distribution.unit_path(BOOK, chapter, "b", "solutions"), as_version=4)
    with tempfile.TemporaryDirectory(prefix=f"active-handoff-{chapter}-") as temporary:
        LEGACY["run_notebook"](unit_a, temporary)
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
        executed = LEGACY["run_notebook"](unit_b, temporary)
        observed = LEGACY["report"](executed)
        assert observed["starting_evidence"] == "LEARNER_SELECTED"
        assert observed["transfer_passed"] is True
    print("ACTIVE HANDOFF VERIFIED", chapter, flush=True)
    return {"chapter": chapter, "selectedLearnerHandoff": "PASS"}


def verify_receipt(path: Path = RECEIPT, book: Path = BOOK) -> None:
    verify_layout(book)
    receipt = json.loads(path.read_text())
    assert receipt["schemaVersion"] == 1 and receipt["edition"] == "four-assets-19-chapters"
    rows = receipt["notebooks"]
    assert len(rows) == 64 and {(row["id"], row["asset"]) for row in rows} == {
        (identity, asset) for identity in EXPECTED for asset in ("exercises", "solutions")
    }, "active notebook coverage drift"
    assert {str(p.relative_to(book)) for p in notebook_paths(book)} == {
        row["notebook"] for row in rows
    }
    assert len(receipt["handoffs"]) == 16
    assert {row["chapter"] for row in receipt["handoffs"]} == AVAILABLE
    assert all(row["selectedLearnerHandoff"] == "PASS" for row in receipt["handoffs"])
    for row in rows:
        assert row["notebook"] == str(
            distribution.unit_path(
                book, int(row["id"][2:4]), row["id"][-1], row["asset"]
            ).relative_to(book)
        )
        assert row["markdown"] == str(Path(row["notebook"]).with_suffix(".md"))
        for proof in ("freshKernel", "sameKernelReplay", "markdownParity", "embeddedImports"):
            assert row[proof] == "PASS", f"active notebook {proof} missing"
        assert row["transfer"] == ("PASS" if row["asset"] == "solutions" else "EXPECTED_UNFINISHED")
        assert row["coreHoldout"] == ("PASS" if row["asset"] == "solutions" else "NOT_DISTRIBUTED")
        for field in ("notebook", "markdown"):
            assert digest(local_file(book, row[field])) == row[field + "Sha256"], (
                "active verified bytes changed"
            )
    print(
        "ACTIVE COURSE: 32 exercise units, 32 solutions, 16 selected handoffs; "
        "exact executed bytes intact."
    )


def execute(workers: int, *, record: bool = True) -> None:
    verify_layout()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        notebooks = list(pool.map(execute_one, notebook_paths()))
        handoffs = list(pool.map(execute_handoff, sorted(AVAILABLE)))
    receipt = {
        "schemaVersion": 1,
        "edition": "four-assets-19-chapters",
        "created": "2026-09-10",
        "python": platform.python_version(),
        "notebooks": notebooks,
        "handoffs": handoffs,
        "limits": [
            "Three planned chapters contain no executable notebooks.",
            "Ninety minutes is a teaching plan, not measured classroom duration.",
            "Offline execution does not certify real phone delivery or host operation.",
        ],
    }
    if not record:
        verify_receipt()
        print("ACTIVE COURSE: all notebooks and handoffs freshly re-executed; receipt unchanged.")
        return
    # A release receipt is append-only; explicitly remove an unpublished failed
    # draft before rerunning, or create a successor verifier for a later release.
    with RECEIPT.open("x") as output:
        output.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    verify_receipt()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--check-execution", action="store_true")
    parser.add_argument("--textbook", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if args.execute:
        execute(args.workers)
    elif args.check_execution:
        execute(args.workers, record=False)
    elif args.textbook:
        verify_textbook()
    else:
        verify_receipt()
