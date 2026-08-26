#!/usr/bin/env python3
"""Check that the book is a real, runnable learning path.

Catches the ways a curriculum rots:

- a chapter that lost a required section
- a `solution.py` that no longer imports
- a solution that copies implementation instead of importing the package
- a chapter promising behaviour the code does not have (e.g. Pulse before Unit 9)
- a referenced script or chapter that does not exist

Exits 0 when the curriculum is sound, 1 otherwise.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK = REPO_ROOT / "book"
sys.path.insert(0, str(REPO_ROOT / "src"))

REQUIRED_CHAPTERS = (
    "ch00_first_shift",
    "ch01_organization_remembers",
    "ch02_work_needs_governance",
    "ch03_actor_is_not_a_model",
)

# Chapter solutions that take a root path and run the exercise end to end.
# EVERY required chapter's exercise must EXECUTE, not merely import. ch03 was
# required but absent here, so the gate reported "3 exercises executed" across
# four required chapters -- a gate overstating its own coverage, which is the
# defect this project exists to remove. It runs offline on the scripted
# provider; no credential is needed, so nothing justified the exclusion.
RUNNABLE = {
    "ch00_first_shift": "run_simulated",
    "ch01_organization_remembers": "observe_memory",
    "ch02_work_needs_governance": "explore_governance",
    "ch03_actor_is_not_a_model": "run_exercise",
}

# Exercises whose entry point needs an argument beyond the root path.
RUNNABLE_ARGS: dict[str, tuple[object, ...]] = {
    # Offline by default: the chapter teaches provider REBINDING, and the
    # scripted provider proves identity survives it without any credential.
    "ch03_actor_is_not_a_model": ("scripted",),
}

REQUIRED_SECTIONS = (
    ("learning objective", ("## Learning objective",)),
    ("runnable exercise", ("## The exercise", "## Exercise 1", "## Exercise")),
    ("expected observations", ("Expected", "## Expected observations")),
    ("learner verification command", ("## Learner verification command",)),
    ("explain it back", ("## Explain it back",)),
)

# Pulse arrives in Unit 9. A chapter must not claim the organization wakes itself.
FORBIDDEN_CLAIMS = (
    re.compile(r"\bpulse\b\s+(?:event\s+)?(?:fires|fired|wakes|woke)", re.IGNORECASE),
    re.compile(r"organization wakes itself (?:up )?(?:now|today)", re.IGNORECASE),
)


def check_chapter(name: str) -> list[str]:
    problems: list[str] = []
    directory = BOOK / name
    if not directory.is_dir():
        return [f"{name}: chapter directory is missing"]

    readme = directory / "README.md"
    if not readme.is_file():
        problems.append(f"{name}: README.md is missing")
        return problems
    text = readme.read_text(encoding="utf-8")

    for label, markers in REQUIRED_SECTIONS:
        if not any(marker in text for marker in markers):
            problems.append(f"{name}: no {label} section")

    for pattern in FORBIDDEN_CLAIMS:
        if pattern.search(text):
            problems.append(f"{name}: claims Pulse behaviour that does not exist until Unit 9")

    solution = directory / "solution.py"
    if not solution.is_file():
        problems.append(f"{name}: solution.py is missing")
        return problems

    source = solution.read_text(encoding="utf-8")
    if not re.search(r"^from (sovereign_agent|reference_organizations)", source, re.MULTILINE):
        problems.append(f"{name}: solution.py does not import the production package")
    if "class Database" in source or "CREATE TABLE" in source:
        problems.append(f"{name}: solution.py appears to copy implementation code")

    spec = importlib.util.spec_from_file_location(f"book_{name}_solution", solution)
    if spec is None or spec.loader is None:
        problems.append(f"{name}: solution.py could not be loaded")
    else:
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as error:  # noqa: BLE001 - any import failure is a curriculum failure
            problems.append(
                f"{name}: solution.py failed to import: {type(error).__name__}: {error}"
            )
            return problems

        # Importing proves the file parses. RUNNING it proves the chapter still
        # works: an exercise rots when the API moves underneath it, and an
        # import-only check never notices. Each runs against a fresh root.
        entry_point = RUNNABLE.get(name)
        if entry_point is not None:
            function = getattr(module, entry_point, None)
            if function is None:
                problems.append(f"{name}: solution.py has no {entry_point}()")
            else:
                with tempfile.TemporaryDirectory() as scratch:
                    try:
                        function(Path(scratch) / "root", *RUNNABLE_ARGS.get(name, ()))
                    except Exception as error:  # noqa: BLE001 - broken exercise, broken chapter
                        problems.append(
                            f"{name}: {entry_point}() failed to run: "
                            f"{type(error).__name__}: {error}"
                        )

    # Every local link and referenced script must exist.
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#")):
            continue
        if not (directory / target).resolve().exists():
            problems.append(f"{name}: broken link to {target}")
    for script in re.findall(r"(scripts/[\w_]+\.py)", text):
        if not (REPO_ROOT / script).is_file():
            problems.append(f"{name}: references missing script {script}")
    return problems


PUBLISHED = {
    "README.md": "index.md",
    "ch00_first_shift/README.md": "ch00_first_shift.md",
    "ch01_organization_remembers/README.md": "ch01_organization_remembers.md",
    "ch02_work_needs_governance/README.md": "ch02_work_needs_governance.md",
    "ch03_actor_is_not_a_model/README.md": "ch03_actor_is_not_a_model.md",
}


def check_published_copies() -> list[str]:
    """The site copy of a chapter must not drift from the source of truth.

    Publishing book/ into docs/ creates two copies, and two copies of anything
    is the shape of every defect this project has spent its life removing. The
    published page is a PROJECTION of book/, so it is regenerated and compared,
    never hand-edited -- the same rule the governance projections follow.
    """
    problems: list[str] = []
    for source_rel, published_rel in PUBLISHED.items():
        source = BOOK / source_rel
        published = REPO_ROOT / "docs" / "book" / published_rel
        if not published.is_file():
            problems.append(f"docs/book/{published_rel} is missing; run scripts/publish_book.py")
            continue
        expected = render_published(source.read_text(encoding="utf-8"))
        if published.read_text(encoding="utf-8") != expected:
            problems.append(
                f"docs/book/{published_rel} has drifted from book/{source_rel}; "
                "regenerate with scripts/publish_book.py"
            )
    return problems


def render_published(text: str) -> str:
    """Source chapter -> published page. Pure; used to publish AND to verify."""
    text = re.sub(r"\]\(\.\./ch(\d\d)_([a-z_]+)/README\.md\)", r"](ch\1_\2.md)", text)
    text = re.sub(r"\]\(ch(\d\d)_([a-z_]+)/README\.md\)", r"](ch\1_\2.md)", text)
    text = text.replace("](../../docs/", "](../")
    text = text.replace("](../README.md)", "](index.md)")
    return text


def main() -> int:
    problems: list[str] = []
    problems.extend(check_published_copies())

    index = BOOK / "README.md"
    if not index.is_file():
        problems.append("book/README.md is missing")
    else:
        index_text = index.read_text(encoding="utf-8")
        for name in REQUIRED_CHAPTERS:
            if name not in index_text:
                problems.append(f"book/README.md does not link {name}")

    for name in REQUIRED_CHAPTERS:
        problems.extend(check_chapter(name))

    for problem in problems:
        print(f"CURRICULUM: {problem}")
    if problems:
        print(f"\n{len(problems)} curriculum problem(s).")
        return 1
    print(
        f"curriculum sound: {len(REQUIRED_CHAPTERS)} chapters, "
        f"{len(RUNNABLE)} exercises executed, all links resolve"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
