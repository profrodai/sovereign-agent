"""Mutation regression tests for the book verifiers.

Each test here is a failure class the Principal demonstrated (msg_aa4e52b8
B3/B4) or listed as required mutation coverage: the instrument is run against
a deliberately corrupted manifest and must fail loudly. A verifier nobody has
tried to break is an instrument of unknown strength -- these keep every
previously-demonstrated false-green path permanently closed.

Scope: scripts/verify_book_depth.py (the depth/coverage instrument). The
snippet verifier's own mutation coverage (SystemExit containment, timeout,
unterminated fences, later-chapter survival) lives alongside these once its
hardening lands -- same file, so the failure classes stay in one place.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify_book_depth.py"
REAL_MANIFEST = REPO_ROOT / "book" / "coverage_manifest.json"


def _load_depth_module():
    spec = importlib.util.spec_from_file_location("verify_book_depth", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_with_manifest(tmp_path: Path, manifest: dict, capsys) -> tuple[int, str]:
    """Run the depth verifier's main() against a mutated manifest copy."""
    mutated = tmp_path / "coverage_manifest.json"
    mutated.write_text(json.dumps(manifest), encoding="utf-8")
    module = _load_depth_module()
    module.MANIFEST = mutated
    code = module.main()
    output = capsys.readouterr().out
    return code, output


def real_manifest() -> dict:
    return json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))


def first_full_chapter(manifest: dict) -> str:
    for slug, entry in manifest["chapters"].items():
        if entry.get("depth") == "full":
            return slug
    raise AssertionError("no full-depth chapter in the real manifest")


def test_the_real_manifest_passes(capsys) -> None:
    module = _load_depth_module()
    code = module.main()
    output = capsys.readouterr().out
    assert code == 0
    assert "BOOK-DEPTH-COMPLETE chapters=13" in output


def test_an_empty_manifest_is_refused(tmp_path, capsys) -> None:
    code, output = run_with_manifest(tmp_path, {"chapters": {}}, capsys)
    assert code == 1
    assert "empty denominator" in output


def test_a_missing_chapter_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    removed = first_full_chapter(manifest)
    del manifest["chapters"][removed]
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert f"missing canonical chapter {removed}" in output


def test_an_extra_chapter_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    manifest["chapters"]["ch99_invented"] = {"depth": "pending", "concepts": []}
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "unknown chapter ch99_invented" in output


def test_an_invalid_depth_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["depth"] = "heroic"
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "'heroic'" in output


def test_an_empty_symbol_name_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["symbols"][0]["name"] = ""
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "empty symbol name" in output


def test_an_absolute_symbol_path_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["symbols"][0] = {
        "file": "/etc/hosts",
        "name": "localhost",
    }
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "not a file under src/ or scripts/" in output


def test_a_traversing_symbol_path_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["symbols"][0] = {
        "file": "src/../../etc/hosts",
        "name": "localhost",
    }
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "not a file under src/ or scripts/" in output


def test_a_nonexistent_ast_symbol_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["symbols"][0]["name"] = "definitely_not_defined"
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "not a function/class/module-level assignment" in output


def test_a_docstring_word_is_not_an_ast_symbol(tmp_path, capsys) -> None:
    """Substring matching used to accept any word that appeared in the file."""
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    # "append-only" appears as prose in database.py but is no AST node.
    manifest["chapters"][chapter]["concepts"][0]["symbols"][0] = {
        "file": "src/sovereign_agent/database.py",
        "name": "append-only",
    }
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "not a function/class/module-level assignment" in output


def test_an_imprecise_test_reference_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["tests"] = ["def test_"]
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "not file::function" in output


def test_a_missing_test_function_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["tests"] = [
        "tests/test_persistence.py::test_this_test_does_not_exist"
    ]
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "no test function" in output


def test_no_tests_and_no_known_gap_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    concept = manifest["chapters"][chapter]["concepts"][0]
    concept["tests"] = []
    concept.pop("known_gap", None)
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "neither precise tests nor an explicit known_gap" in output


def test_an_exercise_outside_the_chapter_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["exercise"] = "scripts/verify_curriculum.py"
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "not a file under book/" in output


def test_a_short_source_text_fragment_is_refused(tmp_path, capsys) -> None:
    manifest = real_manifest()
    chapter = first_full_chapter(manifest)
    manifest["chapters"][chapter]["concepts"][0]["source_text"] = [
        {"file": "src/sovereign_agent/database.py", "text": "reserv"}
    ]
    code, output = run_with_manifest(tmp_path, manifest, capsys)
    assert code == 1
    assert "shorter than" in output


def test_known_gaps_are_counted_in_the_summary(capsys) -> None:
    module = _load_depth_module()
    code = module.main()
    output = capsys.readouterr().out
    assert code == 0
    assert "explicit known gap(s) on record" in output


def test_canonical_chapter_sets_agree_across_verifiers() -> None:
    """The three book instruments must never disagree on the denominator."""
    depth = _load_depth_module()
    curriculum_spec = importlib.util.spec_from_file_location(
        "verify_curriculum", REPO_ROOT / "scripts" / "verify_curriculum.py"
    )
    assert curriculum_spec is not None and curriculum_spec.loader is not None
    curriculum = importlib.util.module_from_spec(curriculum_spec)
    curriculum_spec.loader.exec_module(curriculum)
    assert set(depth.CANONICAL_CHAPTERS) == set(curriculum.REQUIRED_CHAPTERS)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
