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


def check_rulings_index() -> list[str]:
    """The rulings index and the rulings directory must agree, both ways.

    The index was written for a site navigation that no longer exists, was
    referenced by nothing, and was already stale at 9 of 10 the moment a new
    ruling landed. An unreferenced listing that drifts is the ghost citation
    this project keeps deleting -- so it is either checked or removed. It is
    checked.

    The first version compared raw text with `in`, which can only ever detect
    an OMISSION. A ghost row pointing at a ruling that does not exist passed
    silently, and this seat reported the check as proven after testing one
    direction. Comparing two SETS makes both failures the same failure.
    """
    directory = REPO_ROOT / "docs" / "rulings"
    index = directory / "index.md"
    if not index.is_file():
        return ["docs/rulings/index.md is missing"]

    on_disk = {r.name for r in directory.glob("*.md") if r.name != "index.md"}
    linked = set(re.findall(r"\]\(([^)#]+\.md)\)", index.read_text(encoding="utf-8")))

    problems = [f"docs/rulings/index.md does not list {n}" for n in sorted(on_disk - linked)]
    problems += [
        f"docs/rulings/index.md links {n}, which does not exist" for n in sorted(linked - on_disk)
    ]
    return problems


def main() -> int:
    problems: list[str] = []
    problems.extend(check_rulings_index())

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
