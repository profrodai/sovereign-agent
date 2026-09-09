"""Navigation and distribution failures must fail the active edition's own gate."""

import json
from pathlib import Path

import pytest

from scripts import package_book_assets_v1 as packaging
from scripts.verify_book_assets_v1 import verify_layout


@pytest.fixture
def book(tmp_path: Path) -> Path:
    root = tmp_path / "book"
    root.mkdir()
    (root / "README.md").write_text("# Build your always-on agent\n")
    chapters = []
    for asset in ("textbook", "exercises", "solutions", "educator"):
        folder = root / asset
        folder.mkdir()
        (folder / "README.md").write_text(
            "# " + asset + "\n[Download this complete asset](download.zip)\n"
        )
        for number in range(1, 20):
            chapter = folder / f"ch{number:02d}"
            chapter.mkdir()
            (chapter / "README.md").write_text(
                f"# Chapter {number}\n" + ("PLANNED\n" if number in {4, 7, 13} else "DRAFT\n")
            )
    (root / "textbook/checkpoints").mkdir()
    for number in range(1, 20):
        planned = number in {4, 7, 13}
        prefix = f"ch{number:02d}"
        chapters.append(
            {
                "number": number,
                "lessonId": f"lesson-{number}",
                "path": f"{prefix}/README.md",
                "status": "PLANNED" if planned else "DRAFT",
                "checkpoint": None if planned else f"checkpoints/{prefix}.py",
            }
        )
        if planned:
            continue
        (root / f"textbook/checkpoints/{prefix}.py").write_text("print('fixture')\n")
        (root / f"educator/{prefix}/TEACHING-GUIDE.md").write_text("# Teaching guide\n")
        for asset, teacher in (("exercises", "student"), ("solutions", "solutions")):
            (root / f"educator/{prefix}/{teacher}").mkdir()
            for letter in "ab":
                tags = ["embedded-runtime", "learner-owned", "transfer-owned", "course-report"]
                if asset == "solutions":
                    tags.append("instructor-check")
                notebook = {
                    "metadata": {
                        "course": {
                            "unit": f"{prefix}-{letter}",
                            "planned_minutes": 90,
                            "instructor": asset == "solutions",
                        }
                    },
                    "cells": [{"cell_type": "code", "source": [], "metadata": {"tags": tags}}],
                }
                for extension, content in (("ipynb", json.dumps(notebook)), ("md", "# Unit\n")):
                    for directory in (f"{asset}/{prefix}", f"educator/{prefix}/{teacher}"):
                        (root / directory / f"unit-{letter}.{extension}").write_text(content)
    (root / "textbook/BOOK.json").write_text(json.dumps({"schemaVersion": 3, "chapters": chapters}))
    return root


def test_four_assets_align_all_nineteen_chapters_and_preserve_planned_status(book):
    verify_layout(book)


@pytest.mark.parametrize(
    "damage",
    [
        "fifth_asset",
        "missing_chapter",
        "fake_lesson",
        "hidden_plan",
        "identity",
        "solution_leak",
        "teacher_drift",
    ],
)
def test_layout_refuses_broken_navigation_and_misleading_distribution(book, damage):
    if damage == "fifth_asset":
        (book / "classroom").mkdir()
    elif damage == "missing_chapter":
        (book / "exercises/ch04/README.md").unlink()
    elif damage == "fake_lesson":
        (book / "exercises/ch07/unit-a.ipynb").write_text("{}")
    elif damage == "hidden_plan":
        (book / "educator/ch13/README.md").write_text("# Complete chapter\n")
    elif damage == "teacher_drift":
        (book / "educator/ch01/student/unit-a.md").write_text("# Different exercise\n")
    else:
        path = book / "exercises/ch05/unit-a.ipynb"
        document = json.loads(path.read_text())
        course = document["metadata"]["course"]
        if damage == "identity":
            course["unit"] = "ch04-a"
        else:
            course["instructor"] = True
        path.write_text(json.dumps(document))
    with pytest.raises(AssertionError):
        verify_layout(book)


@pytest.mark.parametrize("target", ["../solutions/ch01/unit-a.ipynb", "ch01/missing.ipynb"])
def test_download_refuses_missing_local_dependencies(book, monkeypatch, target):
    monkeypatch.setattr(packaging, "BOOK", book)
    (book / "exercises/README.md").write_text(
        f"# Exercises\n[Download this complete asset](download.zip)\n[Start]({target})\n"
    )
    with pytest.raises(AssertionError):
        packaging.members("exercises")


def test_download_members_include_every_planned_brief_and_exclude_receipts(book, monkeypatch):
    monkeypatch.setattr(packaging, "BOOK", book)
    (book / "educator/verification-v1.json").write_text("{}")
    members = packaging.members("educator")
    assert "verification-v1.json" not in members
    assert all(f"ch{n:02d}/README.md" in members for n in (4, 7, 13))
    assert b"You have the complete asset." in members["README.md"]
    assert b"download.zip" not in members["README.md"]
