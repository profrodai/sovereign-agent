#!/usr/bin/env python3
"""Check that deep chapters actually carry the depth they claim.

Companion to verify_curriculum.py (structure/links/honesty) and
verify_book_snippets.py (fence execution). This one checks COVERAGE and
STRUCTURE against book/coverage_manifest.json:

- every manifest reference is real: anchor text appears in the chapter README,
  symbol text appears in the named production file, test-name fragment appears
  in the named test file, the exercise file exists;
- every chapter marked depth "full" also passes the structural depth gates:
  at least one inline python fence, at least one expected-output text fence
  directly after a python fence, an honest-limits anchor, an active-recall
  section, and the declared break-experiment evidence present verbatim;
- no reader-facing README leaks internal coordination artifacts (issue/PR
  numbers, message ids, org/repo coordination names).

Deliberately NOT here: fence formatting (ruff, via make lint) and fence
execution (verify_book_snippets.py). Three instruments, three scopes.

A chapter marked "pending" is exempt from the depth gates but NOT from the
leak scan — era-aware grading, not a free pass.

Exits 0 when sound, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK = REPO_ROOT / "book"
MANIFEST = BOOK / "coverage_manifest.json"

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


def fences(text: str) -> list[tuple[str, str]]:
    """Return (language, body) for every fenced block, in order."""
    return [
        (match.group(1) or "", match.group(2))
        for match in re.finditer(r"```(\w*)\n(.*?)```", text, re.S)
    ]


def check_reference(chapter: str, concept: dict[str, Any], readme_text: str) -> list[str]:
    problems: list[str] = []
    name = str(concept.get("concept", "<unnamed>"))
    anchor = str(concept.get("anchor", ""))
    if anchor and anchor not in readme_text:
        problems.append(f"{chapter}: anchor {anchor!r} not found in README ({name})")
    for symbol in concept.get("symbols", []):
        file = REPO_ROOT / str(symbol["file"])
        if not file.is_file():
            problems.append(f"{chapter}: symbol file {symbol['file']} missing ({name})")
        elif str(symbol["name"]) not in file.read_text(encoding="utf-8"):
            problems.append(f"{chapter}: {symbol['name']!r} not found in {symbol['file']} ({name})")
    for test in concept.get("tests", []):
        file = REPO_ROOT / str(test["file"])
        if not file.is_file():
            problems.append(f"{chapter}: test file {test['file']} missing ({name})")
        elif str(test["name"]) not in file.read_text(encoding="utf-8"):
            problems.append(
                f"{chapter}: no test matching {test['name']!r} in {test['file']} ({name})"
            )
    exercise = concept.get("exercise")
    if exercise and not (REPO_ROOT / str(exercise)).is_file():
        problems.append(f"{chapter}: exercise {exercise} missing ({name})")
    return problems


def check_depth_gates(chapter: str, entry: dict[str, Any], readme_text: str) -> list[str]:
    problems: list[str] = []
    blocks = fences(readme_text)
    python_blocks = [i for i, (lang, _) in enumerate(blocks) if lang == "python"]
    if not python_blocks:
        problems.append(f"{chapter}: depth 'full' but no inline python construction")
    paired = any(i + 1 < len(blocks) and blocks[i + 1][0] == "text" for i in python_blocks)
    if python_blocks and not paired:
        problems.append(f"{chapter}: no expected-output text fence follows any python fence")
    if not entry.get("concepts"):
        problems.append(f"{chapter}: depth 'full' but empty concept coverage")
    limits = str(entry.get("limits_anchor", ""))
    if not limits:
        problems.append(f"{chapter}: depth 'full' but no limits_anchor declared")
    elif limits not in readme_text:
        problems.append(f"{chapter}: limits anchor {limits!r} not found in README")
    if "Explain it back" not in readme_text:
        problems.append(f"{chapter}: no active-recall section ('Explain it back')")
    for evidence in entry.get("break_evidence", []):
        if str(evidence) not in readme_text:
            problems.append(f"{chapter}: break-experiment evidence {str(evidence)!r} not present")
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
    problems: list[str] = []
    full = 0
    for chapter, entry in manifest["chapters"].items():
        readme = BOOK / chapter / "README.md"
        if not readme.is_file():
            problems.append(f"{chapter}: README.md missing")
            continue
        text = readme.read_text(encoding="utf-8")
        problems.extend(check_leaks(chapter, text))
        for concept in entry.get("concepts", []):
            problems.extend(check_reference(chapter, concept, text))
        if entry.get("depth") == "full":
            full += 1
            problems.extend(check_depth_gates(chapter, entry, text))
    if problems:
        print(f"book depth NOT sound: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    pending = len(manifest["chapters"]) - full
    print(
        f"book depth sound: {full} chapter(s) at full depth verified, "
        f"{pending} pending (exempt from depth gates, leak-scanned)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
