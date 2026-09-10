"""Shared teaching files must retain distinct identities and a route to their source."""

import json
from pathlib import Path

import pytest

from scripts import book_distribution_v1 as distribution
from scripts import package_book_assets_v2 as packaging
from scripts.verify_book_assets_v2 import verify_layout


@pytest.fixture
def book(tmp_path: Path) -> Path:
    root = tmp_path / "book"
    root.mkdir()
    (root / "README.md").write_text(distribution.brand_markdown("# Book\n"))
    chapters = []
    for asset in distribution.ASSETS:
        folder = root / asset
        folder.mkdir()
        (folder / "README.md").write_text(distribution.brand_markdown(f"# {asset}\n"))
        (folder / distribution.start_name(asset)).write_text(
            distribution.brand_markdown(
                f"# {asset}\n\n[Download this complete asset]"
                f"({distribution.download_name(asset)})\n"
            )
        )
        for number in range(1, 20):
            chapter = folder / f"ch{number:02d}"
            chapter.mkdir()
            (chapter / distribution.chapter_name(number, asset)).write_text(
                distribution.brand_markdown(
                    f"# Chapter {number}\n\n" + ("PLANNED\n" if number in {4, 7, 13} else "DRAFT\n")
                )
            )
    (root / "textbook/checkpoints").mkdir()
    for number in range(1, 20):
        planned = number in {4, 7, 13}
        prefix = f"ch{number:02d}"
        chapters.append(
            {
                "number": number,
                "lessonId": f"lesson-{number}",
                "path": f"{prefix}/{distribution.chapter_name(number, 'textbook')}",
                "status": "PLANNED" if planned else "DRAFT",
                "checkpoint": None
                if planned
                else f"checkpoints/{distribution.checkpoint_name(number)}",
            }
        )
        if planned:
            continue
        (root / "textbook/checkpoints" / distribution.checkpoint_name(number)).write_text(
            "# Join the Prof Rod learner community\n"
            + "\n".join(
                f"# {u}"
                for u in (
                    distribution.BOOK_URL,
                    distribution.COMMUNITY_URL,
                    distribution.SOURCE_URL,
                )
            )
            + "\nprint('fixture')\n"
        )
        (root / f"educator/{prefix}" / distribution.guide_name(number)).write_text(
            distribution.brand_markdown("# Teaching guide\n")
        )
        for asset, teacher in (("exercises", "student"), ("solutions", "solutions")):
            (root / f"educator/{prefix}/{teacher}").mkdir()
            for letter in "ab":
                tags = ["embedded-runtime", "learner-owned", "transfer-owned", "course-report"]
                if asset == "solutions":
                    tags.append("instructor-check")
                name = distribution.unit_name(number, letter, asset)
                document = {
                    "metadata": {
                        "course": {
                            "unit": f"{prefix}-{letter}",
                            "planned_minutes": 90,
                            "instructor": asset == "solutions",
                            "resource_id": Path(name).stem,
                            "book_url": distribution.BOOK_URL,
                            "community_url": distribution.COMMUNITY_URL,
                            "source_url": distribution.SOURCE_URL,
                            "distribution_version": distribution.EDITION,
                        }
                    },
                    "cells": [
                        {
                            "cell_type": "markdown",
                            "source": [distribution.brand_markdown("# Lesson\n")],
                            "metadata": {},
                        },
                        {"cell_type": "code", "source": [], "metadata": {"tags": tags}},
                        {
                            "cell_type": "markdown",
                            "source": [distribution.closing_block()],
                            "metadata": {},
                        },
                    ],
                }
                for suffix, content in (
                    (".ipynb", json.dumps(document)),
                    (".md", distribution.brand_markdown("# Lesson\n")),
                ):
                    (root / asset / prefix / Path(name).with_suffix(suffix)).write_text(content)
                    copy = distribution.unit_name(number, letter, asset, educator=True)
                    (
                        root / "educator" / prefix / teacher / Path(copy).with_suffix(suffix)
                    ).write_text(content)
    (root / "textbook/BOOK.json").write_text(json.dumps({"schemaVersion": 3, "chapters": chapters}))
    return root


def test_reader_can_identify_chapter_topic_and_role_without_a_folder():
    assert (
        distribution.unit_name(2, "a", "exercises")
        == "profrod-sovereign-agent-ch02-a-pydantic-shop-tools-exercise.ipynb"
    )
    assert (
        distribution.unit_name(2, "b", "solutions")
        == "profrod-sovereign-agent-ch02-b-pydantic-validation-repair-solution.ipynb"
    )
    assert (
        distribution.unit_name(2, "a", "exercises", educator=True)
        == "profrod-sovereign-agent-ch02-a-pydantic-shop-tools-educator-exercise.ipynb"
    )
    assert (
        distribution.download_name("exercises")
        == "profrod-sovereign-agent-exercises-2026-09-10.zip"
    )


def test_all_nineteen_chapters_keep_navigation_and_visible_origin(book):
    verify_layout(book)


@pytest.mark.parametrize(
    "damage",
    [
        "generic_name",
        "collision",
        "hidden_origin",
        "hidden_cta",
        "no_footer",
        "wrong_resource",
        "solution_leak",
        "missing_chapter",
        "hidden_plan",
        "fake_lesson",
        "teacher_drift",
    ],
)
def test_distribution_refuses_ambiguous_or_unattributed_material(book, damage):
    path = distribution.unit_path(book, 2, "a", "exercises")
    if damage == "generic_name":
        path.rename(path.with_name("unit-a.ipynb"))
    elif damage == "collision":
        (book / "solutions" / path.name.upper()).write_bytes(path.read_bytes())
    elif damage == "missing_chapter":
        (book / "exercises/ch04" / distribution.chapter_name(4, "exercises")).unlink()
    elif damage == "hidden_plan":
        p = book / "educator/ch13" / distribution.chapter_name(13, "educator")
        p.write_text(p.read_text().replace("PLANNED", "Complete"))
    elif damage == "fake_lesson":
        (book / "exercises/ch07/profrod-sovereign-agent-fake.ipynb").write_text("{}")
    elif damage == "teacher_drift":
        p = (
            book
            / "educator/ch02/student"
            / Path(distribution.unit_name(2, "a", "exercises", educator=True)).with_suffix(".md")
        )
        p.write_text(distribution.brand_markdown("# A different exercise\n"))
    else:
        doc = json.loads(path.read_text())
        if damage == "hidden_origin":
            doc["cells"][0]["source"] = ["# Lesson\n"]
        elif damage == "hidden_cta":
            doc["cells"][0]["source"][0] = doc["cells"][0]["source"][0].replace(
                "**Join the Prof Rod learner community:**", "Community"
            )
        elif damage == "no_footer":
            doc["cells"].pop()
        elif damage == "wrong_resource":
            doc["metadata"]["course"]["resource_id"] = "chapter-three"
        else:
            doc["metadata"]["course"]["instructor"] = True
        path.write_text(json.dumps(doc))
    with pytest.raises(AssertionError):
        verify_layout(book)


def test_downloads_have_named_starts_and_can_be_combined_without_overwriting(book, monkeypatch):
    monkeypatch.setattr(packaging, "BOOK", book)
    shared_names = set()
    for asset in packaging.ASSETS:
        content = packaging.members(asset)
        assert not any(Path(p).name == "README.md" for p in content)
        assert b"You have the complete asset." in content[distribution.start_name(asset)]
        names = {Path(p).name.casefold() for p in content}
        assert shared_names.isdisjoint(names)
        shared_names.update(names)
        assert all(
            f"ch{n:02d}/{distribution.chapter_name(n, asset)}" in content for n in (4, 7, 13)
        )


@pytest.mark.parametrize("target", ["../solutions/private.ipynb", "ch02/missing.ipynb"])
def test_download_refuses_navigation_outside_the_asset_or_to_missing_files(
    book, monkeypatch, target
):
    monkeypatch.setattr(packaging, "BOOK", book)
    p = book / "exercises" / distribution.start_name("exercises")
    p.write_text(p.read_text() + f"\n[Continue]({target})\n")
    with pytest.raises(AssertionError):
        packaging.members("exercises")


def test_code_examples_do_not_become_spurious_download_links():
    source = (
        "[Real](lesson.md)\n````markdown\n```python\n"
        "[Example](not-a-file)\n```\n````\n[Next](next.md)"
    )
    assert packaging.markdown_destinations(source) == ["lesson.md", "next.md"]
