"""Challenge the practical release evidence and its learner feedback contracts."""

import ast
import base64
import copy
import hashlib
import json
import runpy
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EDITION = ROOT / "book/always_on/practicals/ninety-minute-v1"
BANK = runpy.run_path(str(EDITION.parent / "authoring/transfer_bank_v1.py"))["TASKS"]


def cells(chapter=8, edition="student", letter="b"):
    return json.loads((EDITION / f"ch{chapter:02d}/{edition}/unit-{letter}-v1.ipynb").read_text())[
        "cells"
    ]


def grader():
    source = next(
        "".join(c["source"]) for c in cells() if "def run_transfer(" in "".join(c["source"])
    )
    tree = ast.parse(source)
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    namespace = {"copy": copy}
    exec(compile(tree, "<distributed-learner-grader>", "exec"), namespace)
    return namespace["run_transfer"]


@pytest.mark.parametrize("chapter", range(1, 17))
def test_transfer_reference_and_shortcuts(chapter):
    task = BANK[chapter]
    namespace = {}
    exec(task["solution"], namespace)
    checks = task["cases"] + task["holdouts"]
    evaluate = grader()
    assert all(row["passed"] for row in evaluate(namespace["transfer_check"], checks))
    for constant in (True, False, 0, None, [], {}, {"raises": "ValueError"}):
        assert not all(
            row["passed"] for row in evaluate(lambda *args, value=constant: value, checks)
        )


def test_grader_distinguishes_exception_from_returned_error_and_bool_from_integer():
    evaluate = grader()
    assert not evaluate(
        lambda: {"raises": "ValueError"}, [("error", [], {"raises": "ValueError"})]
    )[0]["passed"]
    assert not evaluate(lambda: True, [("integer", [], 1)])[0]["passed"]
    assert not evaluate(lambda: {"a": [True]}, [("nested integer", [], {"a": [1]})])[0]["passed"]


def test_grader_rejects_input_mutation_and_calls_real_candidate():
    calls = []

    def candidate(data):
        calls.append(data.copy())
        data.append("changed")
        return 4

    original = ["original"]
    observations = grader()(candidate, [("mutation", [original], 4)])
    assert calls == [["original"]]
    assert original == ["original"]
    assert observations[0]["passed"] is False


def receipt_verifier():
    return runpy.run_path(str(ROOT / "scripts/verify_practical_course_v1.py"))["verify"]


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "false_replay", "student_credit", "hash", "handoff"]
)
def test_receipt_rejects_false_evidence(tmp_path, damage):
    receipt = json.loads((EDITION / "verification-v1.json").read_text())
    if damage == "missing":
        receipt["notebooks"].pop()
    elif damage == "duplicate":
        receipt["notebooks"][-1] = receipt["notebooks"][0]
    elif damage == "false_replay":
        receipt["notebooks"][0]["sameKernelReplay"] = "NOT_RUN"
    elif damage == "student_credit":
        next(row for row in receipt["notebooks"] if row["edition"] == "student")["transfer"] = (
            "PASS"
        )
    elif damage == "hash":
        receipt["notebooks"][0]["markdownSha256"] = "0" * 64
    else:
        receipt["handoffs"][-1] = receipt["handoffs"][0]
    path = tmp_path / "false-receipt.json"
    path.write_text(json.dumps(receipt))
    with pytest.raises(AssertionError):
        receipt_verifier()(path)


def test_missing_selected_handoff_never_uses_reference(tmp_path):
    cell = next(
        "".join(c["source"])
        for c in cells()
        if c["cell_type"] == "code" and "if LEARNER_HANDOFF is not None:" in "".join(c["source"])
    )
    namespace = {"LEARNER_HANDOFF": str(tmp_path / "missing.json"), "COURSE_WORK": tmp_path}
    with pytest.raises(FileNotFoundError, match="selected learner handoff"):
        exec(cell, namespace)
    assert "HANDOFF_ORIGIN" not in namespace
    assert not (tmp_path / "ch08-unit-a-handoff-v1.json").exists()


def test_all_frozen_payloads_are_intact_and_students_exclude_instructor_holdouts():
    for path in sorted(EDITION.glob("ch*/*/*.ipynb")):
        notebook = json.loads(path.read_text())
        source = next(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if "embedded-runtime" in cell.get("metadata", {}).get("tags", [])
        )
        assignments = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {"COURSE_ARCHIVE", "COURSE_ARCHIVE_SHA256"}
        }
        assert len(assignments) == 1
        declared_digest = next(
            node.test.comparators[0].value
            for node in ast.parse(source).body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and "hashlib.sha256(course_bytes)" in ast.unparse(node.test)
        )
        raw = zlib.decompress(base64.b85decode(assignments["COURSE_ARCHIVE"].encode()))
        assert hashlib.sha256(raw).hexdigest() == declared_digest
        payload = json.loads(raw)
        assert payload
        assert not any(".egg-info/" in name for name in payload)
        for name, content in payload.items():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
            assert (ROOT / name).read_text() == content
        if not notebook["metadata"]["course"]["instructor"]:
            assert not any("holdout" in name or "/solutions/" in name for name in payload)


def test_grader_rejects_equal_value_type_mutation():
    def candidate(data):
        data[0] = True
        return "accepted"

    result = grader()(candidate, [("same numeric value is still a mutation", [[1]], "accepted")])
    assert result[0]["passed"] is False


@pytest.mark.parametrize("variant", ["valid", "site", "mixed", "unpaired", "outside"])
def test_curriculum_allows_only_paired_practical_metadata(tmp_path, variant):
    checker = runpy.run_path(str(ROOT / "scripts/verify_curriculum_v2.py"))["check_no_frontmatter"]
    checker.__globals__["BOOK"] = tmp_path / "book"
    checker.__globals__["REPO_ROOT"] = tmp_path
    relative = "always_on/practicals/ninety-minute-v1/ch01/student/unit-a-v1.md"
    if variant == "outside":
        relative = "always_on/ch01/README.md"
    path = tmp_path / "book" / relative
    path.parent.mkdir(parents=True)
    header = (
        "---\njupyter:\n  jupytext:\n    text_representation: {}\n"
        "  kernelspec:\n    name: python3\n"
    )
    if variant == "site":
        header = "---\ntitle: A website page\n"
    elif variant == "mixed":
        header += "slug: injected-site-page\n"
    path.write_text(header + "---\n# Lesson\n")
    if variant != "unpaired":
        path.with_suffix(".ipynb").write_text("{}")
    assert bool(checker()) is (variant != "valid")
