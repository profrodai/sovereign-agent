#!/usr/bin/env python3
"""Verify the thirteen runnable companion labs.

This gate uses only the Python standard library. It validates metadata against
the live source and test trees, imports the learner and reference modules, and
runs each behavioral checker twice against independent temporary roots.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import io
import json
import re
import sys
import tempfile
import tokenize
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LABS_ROOT = REPO_ROOT / "book" / "labs"
SRC_ROOT = (REPO_ROOT / "src").resolve()
TESTS_ROOT = (REPO_ROOT / "tests").resolve()

CHAPTERS = (
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
)

REQUIRED_FILES = (
    "README.md",
    "lab.json",
    "starter.py",
    "solution.py",
    "check.py",
    "expected.json",
)

REQUIRED_HEADINGS = (
    "## Challenge",
    "## Production map",
    "## Run it",
    "## Break it",
    "## Explain it back",
)

LAB_JSON_KEYS = {
    "schema_version",
    "chapter",
    "title",
    "production_sources",
    "production_tests",
    "entrypoint",
    "expected",
}

NUMBERED_TODO = re.compile(r"^# TODO\((\d+)\):")


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _safe_repo_file(value: object, *, prefix: str, root: Path) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "must be a nonempty string"
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None, f"path escapes the repository: {value!r}"
    if not value.startswith(f"{prefix}/"):
        return None, f"must be below {prefix}/: {value!r}"
    candidate = (REPO_ROOT / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, f"path escapes {prefix}/ after resolution: {value!r}"
    if not candidate.is_file():
        return None, f"file does not exist: {value!r}"
    return candidate, None


def _test_node_exists(node: object) -> str | None:
    if not isinstance(node, str):
        return "test node must be a string"
    parts = node.split("::")
    if len(parts) not in (2, 3) or any(not part for part in parts):
        return f"test node must be file::test or file::Class::test: {node!r}"

    test_file, error = _safe_repo_file(parts[0], prefix="tests", root=TESTS_ROOT)
    if error is not None:
        return error
    assert test_file is not None

    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
    except (OSError, SyntaxError) as exc:
        return f"cannot inspect test node {node!r}: {type(exc).__name__}: {exc}"

    if len(parts) == 2:
        name = parts[1]
        exists = any(
            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
            for item in tree.body
        )
    else:
        class_name, method_name = parts[1:]
        matching_classes = (
            item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == class_name
        )
        exists = any(
            isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            and member.name == method_name
            for class_node in matching_classes
            for member in class_node.body
        )
    if not exists:
        return f"test node does not exist: {node!r}"
    return None


def _assignment_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for item in target.elts for name in _assignment_names(item)}
    return set()


def _production_source_exists(reference: object) -> str | None:
    if not isinstance(reference, str):
        return "production source must be a string"
    try:
        file_name, symbol = reference.rsplit(":", 1)
    except ValueError:
        return f"production source must be file.py:Symbol: {reference!r}"
    symbol_parts = symbol.split(".")
    if not symbol_parts or any(not part.isidentifier() for part in symbol_parts):
        return f"production source has invalid symbol: {reference!r}"
    source_file, error = _safe_repo_file(file_name, prefix="src", root=SRC_ROOT)
    if error is not None:
        return error
    assert source_file is not None
    try:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    except (OSError, SyntaxError) as exc:
        return f"cannot inspect production source {reference!r}: {type(exc).__name__}: {exc}"

    def named_children(nodes: list[ast.stmt]) -> dict[str, ast.AST]:
        found: dict[str, ast.AST] = {}
        for item in nodes:
            if isinstance(item, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                found[item.name] = item
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    for name in _assignment_names(target):
                        found[name] = item
            elif isinstance(item, ast.AnnAssign):
                for name in _assignment_names(item.target):
                    found[name] = item
        return found

    current: ast.AST | None = named_children(tree.body).get(symbol_parts[0])
    for part in symbol_parts[1:]:
        if not isinstance(current, ast.ClassDef):
            current = None
            break
        current = named_children(current.body).get(part)
    if current is None:
        return f"production symbol does not exist: {reference!r}"
    return None


def _import_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create an import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_positional_contract(function: object, names: tuple[str, ...]) -> bool:
    if not callable(function):
        return False
    try:
        signature = inspect.signature(function)
    except TypeError:
        return False
    except ValueError:
        return False
    parameters = tuple(signature.parameters.values())
    return len(parameters) == len(names) and all(
        parameter.name == name
        and parameter.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for parameter, name in zip(parameters, names, strict=True)
    )


def _json_round_trip(value: object) -> object:
    encoded = json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return json.loads(encoded)


def _check_starter_shape(path: Path) -> list[str]:
    problems: list[str] = []
    source = path.read_text(encoding="utf-8")
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (IndentationError, tokenize.TokenError) as exc:
        problems.append(f"starter.py cannot be tokenized: {type(exc).__name__}: {exc}")
        tokens = []
    todo_numbers = {
        int(match.group(1))
        for token in tokens
        if token.type == tokenize.COMMENT
        for match in [NUMBERED_TODO.match(token.string)]
        if match is not None
    }
    if len(todo_numbers) < 3:
        problems.append(
            "starter.py must contain at least three distinct numbered markers such as '# TODO(1):'"
        )
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        problems.append(f"starter.py cannot be parsed: {type(exc).__name__}: {exc}")
        return problems
    helpers = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name != "exercise"
    ]
    if not helpers:
        problems.append(
            "starter.py must contain a top-level helper function or class besides exercise"
        )
    return problems


def _check_metadata(chapter: str, lab_dir: Path) -> tuple[dict[str, Any] | None, list[str]]:
    problems: list[str] = []
    path = lab_dir / "lab.json"
    try:
        metadata = _load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"lab.json cannot be read: {type(exc).__name__}: {exc}"]
    if not isinstance(metadata, dict):
        return None, ["lab.json must contain one JSON object"]

    keys = set(metadata)
    if keys != LAB_JSON_KEYS:
        missing = sorted(LAB_JSON_KEYS - keys)
        extra = sorted(keys - LAB_JSON_KEYS)
        if missing:
            problems.append(f"lab.json missing keys: {', '.join(missing)}")
        if extra:
            problems.append(f"lab.json unknown keys: {', '.join(extra)}")
    if metadata.get("schema_version") != 1:
        problems.append("lab.json schema_version must be 1")
    if metadata.get("chapter") != chapter:
        problems.append(f"lab.json chapter must be {chapter!r}")
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        problems.append("lab.json title must be a nonempty string")
    if metadata.get("entrypoint") != "exercise":
        problems.append("lab.json entrypoint must be 'exercise'")
    if metadata.get("expected") != "expected.json":
        problems.append("lab.json expected must be 'expected.json'")

    sources = metadata.get("production_sources")
    if not isinstance(sources, list) or not sources:
        problems.append("lab.json production_sources must be a nonempty list")
    else:
        if len(sources) != len(set(item for item in sources if isinstance(item, str))):
            problems.append("lab.json production_sources contains duplicates")
        for source in sources:
            error = _production_source_exists(source)
            if error is not None:
                problems.append(f"production_sources: {error}")

    nodes = metadata.get("production_tests")
    if not isinstance(nodes, list) or not nodes:
        problems.append("lab.json production_tests must be a nonempty list")
    else:
        if len(nodes) != len(set(item for item in nodes if isinstance(item, str))):
            problems.append("lab.json production_tests contains duplicates")
        for node in nodes:
            error = _test_node_exists(node)
            if error is not None:
                problems.append(f"production_tests: {error}")
    return metadata, problems


def check_lab(chapter: str) -> list[str]:
    problems: list[str] = []
    lab_dir = LABS_ROOT / chapter
    if not lab_dir.is_dir():
        return ["lab directory is missing"]

    for filename in REQUIRED_FILES:
        if not (lab_dir / filename).is_file():
            problems.append(f"required file is missing: {filename}")
    if problems:
        return problems

    readme = (lab_dir / "README.md").read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        if heading not in readme.splitlines():
            problems.append(f"README.md is missing exact heading {heading!r}")

    problems.extend(_check_starter_shape(lab_dir / "starter.py"))

    metadata, metadata_problems = _check_metadata(chapter, lab_dir)
    problems.extend(metadata_problems)

    try:
        expected = _load_json(lab_dir / "expected.json")
        if not isinstance(expected, dict):
            problems.append("expected.json must contain one JSON object")
        expected = _json_round_trip(expected)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        problems.append(f"expected.json is not strict JSON: {type(exc).__name__}: {exc}")
        expected = None

    old_path = list(sys.path)
    sys.path[:0] = [str(lab_dir), str(REPO_ROOT / "src"), str(REPO_ROOT)]
    try:
        starter = _import_module(lab_dir / "starter.py", f"book_lab_{chapter}_starter")
        solution = _import_module(lab_dir / "solution.py", f"book_lab_{chapter}_solution")
        checker = _import_module(lab_dir / "check.py", f"book_lab_{chapter}_check")
    except Exception as exc:  # noqa: BLE001 - every import defect is reported by the gate
        problems.append(f"module import failed: {type(exc).__name__}: {exc}")
        return problems
    finally:
        sys.path[:] = old_path

    starter_exercise = getattr(starter, "exercise", None)
    solution_exercise = getattr(solution, "exercise", None)
    check = getattr(checker, "check", None)
    if getattr(starter, "STUDENT_TODO", None) is not True:
        problems.append("starter.py must set STUDENT_TODO = True")
    if getattr(solution, "STUDENT_TODO", None) is not False:
        problems.append("solution.py must set STUDENT_TODO = False")
    if not _has_positional_contract(starter_exercise, ("root",)):
        problems.append("starter.py must expose exercise(root) with exactly that parameter")
    if not _has_positional_contract(solution_exercise, ("root",)):
        problems.append("solution.py must expose exercise(root) with exactly that parameter")
    if not _has_positional_contract(check, ("target_module", "root")):
        problems.append("check.py must expose check(target_module, root)")

    if callable(starter_exercise):
        with tempfile.TemporaryDirectory(prefix=f"book-lab-{chapter}-starter-") as scratch:
            root = Path(scratch) / "root"
            try:
                starter_exercise(root)
            except NotImplementedError:
                pass
            except Exception as exc:  # noqa: BLE001 - report wrong pedagogical failure
                problems.append(
                    f"starter exercise raised the wrong exception: {type(exc).__name__}: {exc}"
                )
            else:
                problems.append("starter exercise must raise NotImplementedError")

    if _has_positional_contract(solution_exercise, ("root",)) and _has_positional_contract(
        check, ("target_module", "root")
    ):
        observations: list[object] = []
        for run_number in (1, 2):
            with tempfile.TemporaryDirectory(
                prefix=f"book-lab-{chapter}-solution-{run_number}-"
            ) as scratch:
                root = Path(scratch) / "root"
                exercise_calls = 0

                def observed_exercise(exercise_root: Path) -> dict[str, object]:
                    nonlocal exercise_calls
                    exercise_calls += 1
                    return solution_exercise(exercise_root)

                solution.exercise = observed_exercise
                try:
                    result = check(solution, root)
                    if not isinstance(result, dict):
                        raise TypeError("check() must return a dictionary")
                    observations.append(_json_round_trip(result))
                except Exception as exc:  # noqa: BLE001 - behavioral failures are gate failures
                    problems.append(
                        f"solution check run {run_number} failed: {type(exc).__name__}: {exc}"
                    )
                finally:
                    solution.exercise = solution_exercise
                if exercise_calls == 0:
                    problems.append(f"solution check run {run_number} did not call exercise(root)")
        if len(observations) == 2:
            if observations[0] != observations[1]:
                problems.append("solution observations differ across two fresh roots")
            if expected is not None:
                for index, observation in enumerate(observations, start=1):
                    if observation != expected:
                        problems.append(
                            f"solution check run {index} does not match expected.json: "
                            f"observed={json.dumps(observation, sort_keys=True)}"
                        )
    return problems


def main() -> int:
    failures: list[str] = []
    if not LABS_ROOT.is_dir():
        print("FAIL book/labs directory is missing")
        return 1

    actual_directories = {
        path.name
        for path in LABS_ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__" and not path.name.startswith(".")
    }
    expected_directories = set(CHAPTERS)
    for extra in sorted(actual_directories - expected_directories):
        failures.append(f"{extra}: unexpected lab directory")

    for chapter in CHAPTERS:
        chapter_problems = check_lab(chapter)
        if chapter_problems:
            for problem in chapter_problems:
                failures.append(f"{chapter}: {problem}")
            print(f"FAIL {chapter} ({len(chapter_problems)} defects)")
        else:
            print(f"PASS {chapter}")

    if failures:
        print(f"\nbook labs: FAIL ({len(failures)} defects)")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"\nbook labs: PASS ({len(CHAPTERS)} labs, solutions deterministic twice)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
