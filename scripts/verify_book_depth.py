#!/usr/bin/env python3
"""Check that deep chapters actually carry the depth they claim.

Companion to verify_curriculum.py (structure/links/honesty) and
verify_book_snippets.py (fence execution). This one checks COVERAGE and
STRUCTURE against book/coverage_manifest.json.

Hardened after the Principal's B3/B4 findings (msg_aa4e52b8), which
demonstrated four false-green paths in the first version by direct mutation:
an empty manifest passed with a zero denominator; substring symbol matching
accepted empty names (which match every file); reference paths accepted
absolute paths escaping the repository; and generic test fragments like
"def test_" counted as precise evidence. Every one of those is now a hard
failure, and tests/test_book_verifiers.py holds a regression test per class.

The contract:

- the manifest's chapter set must equal the canonical 13 chapter slugs
  exactly -- no missing, no extra, never empty. The claimant does not choose
  the denominator;
- every reference path must resolve inside its required repository root
  (symbols/source under src/ or scripts/, tests under tests/, exercises
  under the chapter's own book/ directory) -- absolute paths and `..`
  traversal are rejected before resolution is even attempted;
- a `symbols` entry names an exact AST node -- a function, class, or
  module-level assignment target -- in the referenced Python file;
- a `tests` entry is a precise node id `tests/<file>.py::<test_function>`,
  and the named test function must exist as an AST node in that file;
- prose-level evidence (docstring sentences, SQL trigger names, comments)
  goes in `source_text`, exact-substring checked with a minimum length so a
  fragment cannot accidentally match;
- a full-depth concept needs at least one symbol AND (at least one test OR
  an explicit `known_gap` string). A known gap is machine-readable honesty:
  it is counted and reported in the summary, so a chapter carrying one can
  never be mistaken for fully test-backed;
- every finished chapter (full or tour) declares its companion lab, and the
  binding is checked as IDENTITY (directory under book/labs/, lab.json
  naming this exact chapter) -- lab BEHAVIOR is the disjoint
  scripts/verify_book_labs.py gate's job, deliberately not duplicated here.

Chapters marked "tour" are finished guided-tour chapters (bash transcripts,
no inline python): exempt from the python-construction gate ONLY — concepts,
limits, recall, break evidence, and the leak scan all still apply. Chapters
marked "pending" are unfinished: exempt from the depth gates but NOT from
the leak scan. Exits 0 when sound, 1 otherwise, printing every problem found.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK = REPO_ROOT / "book"
MANIFEST = BOOK / "coverage_manifest.json"

CANONICAL_CHAPTERS = frozenset(
    {
        "ch00_first_shift",
        "ch01_organization_remembers",
        "ch02_work_needs_governance",
        "ch03_actor_is_not_a_model",
        "ch04_work_stays_inside_its_boundary",
        "ch05_authority_needs_a_fence",
        "ch06_the_organization_recovers",
        "ch07_the_organization_wakes_itself",
        "ch08_the_store_becomes_a_catalog",
        "ch09_each_product_has_its_own_threshold",
        "ch10_one_signal_wakes_one_need",
        "ch11_replenishment_scales_without_losing_governance",
        "ch12_the_pilot_begins_with_a_receipt",
    }
)

ALLOWED_DEPTHS = frozenset({"full", "tour", "pending"})
MIN_SOURCE_TEXT_LENGTH = 12

# Internal coordination artifacts that must never reach a reader. Domain words
# the PRODUCT itself uses (SOW, ruling, sparring-as-role) are NOT leaks.
LEAK_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\borg #\d+", "org-repo issue reference"),
    (r"\bPR #\d+", "pull-request reference"),
    (r"\bmsg_[0-9a-f]{8}", "coordination message id"),
    (r"\bCLAUDE\.md\b", "fleet doctrine file"),
    (r"\bzeroemployeeorg/org\b", "org coordination repo"),
    (r"\bRULING-\d{3}\b", "fleet ruling id"),
)


def contained_path(raw: str, required_root: Path) -> Path | None:
    """Resolve `raw` against REPO_ROOT and require it strictly inside
    `required_root`.

    Absolute paths and `..` segments are rejected on the STRING, before any
    filesystem resolution, so acceptance never depends on where the host
    filesystem happens to put things. Resolution (which also follows
    symlinks) then enforces real containment.
    """
    if not raw or raw.startswith("/") or ".." in Path(raw).parts:
        return None
    candidate = (REPO_ROOT / raw).resolve()
    root = required_root.resolve()
    if candidate == root or root not in candidate.parents:
        return None
    return candidate


def source_path(raw: str) -> Path | None:
    """A path allowed to hold production symbols/source text."""
    return contained_path(raw, REPO_ROOT / "src") or contained_path(raw, REPO_ROOT / "scripts")


def ast_defined_names(source: str) -> set[str]:
    """Function/class names (at any nesting) plus module-level assignment
    targets -- the exact nodes a `symbols` entry may name."""
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def check_symbol(chapter: str, concept_name: str, entry: dict[str, Any]) -> list[str]:
    file_raw = str(entry.get("file", ""))
    name = str(entry.get("name", ""))
    if not name:
        return [f"{chapter}: empty symbol name ({concept_name})"]
    path = source_path(file_raw)
    if path is None or not path.is_file():
        return [
            f"{chapter}: symbol file {file_raw!r} is not a file under src/ or scripts/ "
            f"({concept_name})"
        ]
    if path.suffix != ".py":
        return [f"{chapter}: symbol file {file_raw!r} is not a Python file ({concept_name})"]
    if name not in ast_defined_names(path.read_text(encoding="utf-8")):
        return [
            f"{chapter}: {name!r} is not a function/class/module-level assignment "
            f"in {file_raw} ({concept_name})"
        ]
    return []


def check_source_text(chapter: str, concept_name: str, entry: dict[str, Any]) -> list[str]:
    file_raw = str(entry.get("file", ""))
    text = str(entry.get("text", ""))
    if len(text) < MIN_SOURCE_TEXT_LENGTH:
        return [
            f"{chapter}: source_text {text!r} shorter than {MIN_SOURCE_TEXT_LENGTH} chars "
            f"({concept_name})"
        ]
    path = source_path(file_raw)
    if path is None or not path.is_file():
        return [
            f"{chapter}: source_text file {file_raw!r} is not a file under src/ or scripts/ "
            f"({concept_name})"
        ]
    if text not in path.read_text(encoding="utf-8"):
        return [f"{chapter}: source_text {text!r} not found in {file_raw} ({concept_name})"]
    return []


def check_test_node(chapter: str, concept_name: str, node_id: str) -> list[str]:
    if "::" not in node_id:
        return [f"{chapter}: test reference {node_id!r} is not file::function ({concept_name})"]
    file_raw, _, function = node_id.partition("::")
    if not function.startswith("test_") or function == "test_":
        return [
            f"{chapter}: test function {function!r} is not a precise test name ({concept_name})"
        ]
    path = contained_path(file_raw, REPO_ROOT / "tests")
    if path is None or not path.is_file():
        return [f"{chapter}: test file {file_raw!r} is not a file under tests/ ({concept_name})"]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if function not in functions:
        return [f"{chapter}: no test function {function!r} in {file_raw} ({concept_name})"]
    return []


def check_concept(chapter: str, concept: dict[str, Any], readme_text: str) -> tuple[list[str], int]:
    """Validate one concept's references. Returns (problems, known_gap_count)."""
    problems: list[str] = []
    name = str(concept.get("concept", "")) or "<unnamed>"
    if name == "<unnamed>":
        problems.append(f"{chapter}: concept with no name")
    anchor = str(concept.get("anchor", ""))
    if not anchor:
        problems.append(f"{chapter}: concept {name} has no anchor")
    elif anchor not in readme_text:
        problems.append(f"{chapter}: anchor {anchor!r} not found in README ({name})")

    symbols = concept.get("symbols", [])
    if not symbols:
        problems.append(f"{chapter}: concept {name} declares no symbols")
    for entry in symbols:
        problems.extend(check_symbol(chapter, name, entry))

    for entry in concept.get("source_text", []):
        problems.extend(check_source_text(chapter, name, entry))

    tests = concept.get("tests", [])
    known_gap = str(concept.get("known_gap", ""))
    gap_count = 1 if known_gap else 0
    if not tests and not known_gap:
        problems.append(
            f"{chapter}: concept {name} has neither precise tests nor an explicit known_gap"
        )
    for node_id in tests:
        problems.extend(check_test_node(chapter, name, str(node_id)))

    exercise = str(concept.get("exercise", ""))
    if not exercise:
        problems.append(f"{chapter}: concept {name} has no exercise")
    else:
        path = contained_path(exercise, BOOK / chapter)
        if path is None or not path.is_file():
            problems.append(
                f"{chapter}: exercise {exercise!r} is not a file under book/{chapter}/ ({name})"
            )
    return problems, gap_count


def fences(text: str) -> list[tuple[str, str]]:
    """Return (language, body) for every fenced block, in order."""
    return [
        (match.group(1) or "", match.group(2))
        for match in re.finditer(r"```(\w*)\n(.*?)```", text, re.S)
    ]


def check_depth_gates(
    chapter: str, entry: dict[str, Any], readme_text: str, depth: str
) -> list[str]:
    """Gates for finished chapters.

    Depth 'full' requires inline python construction with paired expected-output
    fences. Depth 'tour' is a finished guided-tour chapter (bash transcripts, no
    inline python) — it is exempt from the python-construction gate ONLY; every
    other finished-chapter gate (concepts, limits, recall, break evidence, leak
    scan) applies identically. 'tour' is not a loophole for an unfinished
    chapter: it must still declare and pass real coverage.
    """
    problems: list[str] = []
    if depth == "full":
        blocks = fences(readme_text)
        python_blocks = [i for i, (lang, _) in enumerate(blocks) if lang == "python"]
        if not python_blocks:
            problems.append(f"{chapter}: depth 'full' but no inline python construction")
        paired = any(i + 1 < len(blocks) and blocks[i + 1][0] == "text" for i in python_blocks)
        if python_blocks and not paired:
            problems.append(f"{chapter}: no expected-output text fence follows any python fence")
    if not entry.get("concepts"):
        problems.append(f"{chapter}: depth {depth!r} but empty concept coverage")
    limits = str(entry.get("limits_anchor", ""))
    if not limits:
        problems.append(f"{chapter}: depth {depth!r} but no limits_anchor declared")
    elif limits not in readme_text:
        problems.append(f"{chapter}: limits anchor {limits!r} not found in README")
    if "Explain it back" not in readme_text:
        problems.append(f"{chapter}: no active-recall section ('Explain it back')")
    evidence_list = entry.get("break_evidence", [])
    if not evidence_list:
        problems.append(f"{chapter}: depth {depth!r} but no break_evidence declared")
    for evidence in evidence_list:
        if str(evidence) not in readme_text:
            problems.append(f"{chapter}: break-experiment evidence {str(evidence)!r} not present")
    problems.extend(check_lab_binding(chapter, entry))
    return problems


def check_lab_binding(chapter: str, entry: dict[str, Any]) -> list[str]:
    """Bind the chapter to its companion lab as declared evidence.

    This is an IDENTITY binding, not a behavioral claim: it checks the declared
    lab directory exists under book/labs/, carries a lab.json, and that
    lab.json's own "chapter" field names this chapter. Whether the lab actually
    RUNS and its checks hold is the disjoint scripts/verify_book_labs.py gate's
    job — this check deliberately does not duplicate it, and passing here says
    nothing about lab behavior.
    """
    problems: list[str] = []
    lab_raw = str(entry.get("lab", ""))
    if not lab_raw:
        problems.append(f"{chapter}: finished chapter declares no companion lab")
        return problems
    lab_dir = contained_path(lab_raw, REPO_ROOT / "book" / "labs")
    if lab_dir is None or not lab_dir.is_dir():
        problems.append(f"{chapter}: lab {lab_raw!r} is not a directory under book/labs/")
        return problems
    lab_json = lab_dir / "lab.json"
    if not lab_json.is_file():
        problems.append(f"{chapter}: lab {lab_raw!r} has no lab.json")
        return problems
    try:
        declared = json.loads(lab_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        problems.append(f"{chapter}: lab.json unreadable ({error})")
        return problems
    lab_chapter = str(declared.get("chapter", ""))
    if lab_chapter != chapter:
        problems.append(f"{chapter}: lab.json declares chapter {lab_chapter!r} — identity mismatch")
    return problems


def check_leaks(chapter: str, readme_text: str) -> list[str]:
    problems = []
    for pattern, label in LEAK_PATTERNS:
        match = re.search(pattern, readme_text)
        if match:
            problems.append(f"{chapter}: internal {label} leaks to readers: {match.group(0)!r}")
    return problems


def main() -> int:
    if not MANIFEST.is_file():
        print("book/coverage_manifest.json is missing")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    chapters = manifest.get("chapters")
    if not isinstance(chapters, dict) or not chapters:
        print(
            "book depth NOT sound: manifest declares no chapters (an empty denominator is refused)"
        )
        return 1

    problems: list[str] = []
    declared = set(chapters)
    for slug in sorted(CANONICAL_CHAPTERS - declared):
        problems.append(f"manifest missing canonical chapter {slug}")
    for slug in sorted(declared - CANONICAL_CHAPTERS):
        problems.append(f"manifest declares unknown chapter {slug}")

    full = 0
    tours = 0
    gaps = 0
    for chapter in sorted(declared & CANONICAL_CHAPTERS):
        entry = chapters[chapter]
        depth = str(entry.get("depth", ""))
        if depth not in ALLOWED_DEPTHS:
            problems.append(f"{chapter}: depth {depth!r} is not one of {sorted(ALLOWED_DEPTHS)}")
            continue
        readme = BOOK / chapter / "README.md"
        if not readme.is_file():
            problems.append(f"{chapter}: README.md missing")
            continue
        text = readme.read_text(encoding="utf-8")
        problems.extend(check_leaks(chapter, text))
        for concept in entry.get("concepts", []):
            concept_problems, gap_count = check_concept(chapter, concept, text)
            problems.extend(concept_problems)
            gaps += gap_count
        if depth == "full":
            full += 1
            problems.extend(check_depth_gates(chapter, entry, text, depth))
        elif depth == "tour":
            tours += 1
            problems.extend(check_depth_gates(chapter, entry, text, depth))

    if problems:
        print(f"book depth NOT sound: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    pending = len(CANONICAL_CHAPTERS) - full - tours
    print(
        f"book depth sound: {full} chapter(s) at full depth verified, "
        f"{tours} tour chapter(s) verified, {pending} pending "
        f"(exempt from depth gates, leak-scanned), {gaps} explicit known gap(s) on record"
    )
    print(f"BOOK-DEPTH-COMPLETE chapters={len(CANONICAL_CHAPTERS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
