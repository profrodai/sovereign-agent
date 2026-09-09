"""Build the complete self-contained practical course from canonical Markdown sources.

--author assembles a new edition from chapter teaching fragments and preserved exercises.
Ordinary builds only convert the resulting canonical student Markdown and instructor editions.
"""

from __future__ import annotations

import argparse
import ast
import base64
import copy
import hashlib
import json
import re
import runpy
import subprocess
import textwrap
import zlib
from pathlib import Path

import jupytext
import nbformat
from build_exercise_release_v5 import UNITS

ROOT = Path(__file__).resolve().parent.parent
COURSE = ROOT / "book/always_on/practicals"
AUTHORING = COURSE / "authoring"
EDITION = COURSE / "ninety-minute-v1"
PIN = "444c5f6"
BANK = runpy.run_path(str(AUTHORING / "transfer_bank_v1.py"))["TASKS"]
SQL_CHAPTERS = {4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16}
WAVE_CHAPTERS = {2, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16}


def markdown(source):
    return nbformat.v4.new_markdown_cell(textwrap.dedent(source).strip() + "\n")


def code(source, *tags):
    return nbformat.v4.new_code_cell(
        textwrap.dedent(source).strip() + "\n", metadata={"tags": list(tags)}
    )


def fragment(name):
    return jupytext.read(AUTHORING / name).cells


def support_payload(instructor):
    tracked = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", PIN], cwd=ROOT, text=True
        ).splitlines()
    )
    paths = set()
    for folder in (
        "src",
        "book/always_on/checkpoints",
        "book/always_on/learner",
        "book/always_on/skills",
    ):
        paths.update(
            path
            for path in (ROOT / folder).rglob("*")
            if path.is_file()
            and path.suffix in {".py", ".json", ".toml", ".txt"}
            and "__pycache__" not in path.parts
            and path.relative_to(ROOT).as_posix() in tracked
        )
    paths.update(
        ROOT / name
        for name in (
            "book/always_on/exercises/source_tasks_v1.py",
            "book/always_on/exercises/source-tasks-v1.json",
            "book/always_on/educator/runtime_labs_v1.py",
            "book/always_on/educator/runtime-experiments-v1.json",
        )
    )
    if instructor:
        paths.update(
            (ROOT / "book/always_on/exercises").glob("ch*/holdouts/runtime-transfer-v1.py")
        )
    files = {str(p.relative_to(ROOT)): p.read_text() for p in sorted(paths)}
    raw = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return (
        base64.b85encode(zlib.compress(raw, 9)).decode(),
        hashlib.sha256(raw).hexdigest(),
        len(files),
    )


def bootstrap(identity, instructor):
    payload, digest, count = support_payload(instructor)
    encoded_lines = "\n".join(f'    "{payload[i : i + 84]}"' for i in range(0, len(payload), 84))
    source = """
import base64
import hashlib
import json
import os
import sys
import tempfile
import zlib
from pathlib import Path

minimum_python = (3, 14)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("Use a Python 3.14 kernel for this complete-book practical course.")
try:
    import pydantic
except ImportError as error:
    raise RuntimeError('Run %pip install "pydantic==2.13.4", then restart the kernel.') from error
if pydantic.__version__.split(".")[0] != "2":
    raise RuntimeError('Use Pydantic 2; the tested version is 2.13.4.')

# Frozen, reviewed course files: data until explicitly loaded by the lesson.
COURSE_ARCHIVE = (
ARCHIVE_LINES
)
course_bytes = zlib.decompress(base64.b85decode(COURSE_ARCHIVE))
if hashlib.sha256(course_bytes).hexdigest() != "ARCHIVE_DIGEST":
    raise ValueError("Embedded course files failed their integrity check")
course_files = json.loads(course_bytes)
if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd().resolve()
if "COURSE_RUNTIME_DIRECTORY" not in globals():
    COURSE_RUNTIME_DIRECTORY = tempfile.TemporaryDirectory(prefix="lucy-practical-runtime-")
COURSE_ROOT = Path(COURSE_RUNTIME_DIRECTORY.name)
for course_relative, course_content in course_files.items():
    course_target = COURSE_ROOT / course_relative
    if not course_target.resolve().is_relative_to(COURSE_ROOT.resolve()):
        raise ValueError("Invalid embedded relative path")
    course_target.parent.mkdir(parents=True, exist_ok=True)
    course_target.write_text(course_content, encoding="utf-8")
for course_import_path in (COURSE_ROOT, COURSE_ROOT / "src"):
    if str(course_import_path) not in sys.path:
        sys.path.insert(0, str(course_import_path))
COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "UNIT_ID"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
ROOT = COURSE_ROOT
print("Python", sys.version.split()[0], "Pydantic", pydantic.__version__)
print("Offline teaching files ready:", len(course_files))
print("Save your work here:", COURSE_WORK)
"""
    source = source.replace("ARCHIVE_LINES", encoded_lines).replace("ARCHIVE_DIGEST", digest)
    source = source.replace("UNIT_ID", identity)
    cell = code(source, "setup", "embedded-runtime")
    cell.metadata["jupyter"] = {"source_hidden": True}
    return [
        markdown(f"""
## Run the self-contained setup

Use a **Python 3.14** Jupyter kernel and **Pydantic 2**. If needed, run
`%pip install "pydantic==2.13.4"` once in a separate cell and restart the kernel.
Package installation needs internet; the lesson itself needs no repository download, API key
or prior notebook. The complete source runtime uses Python 3.14, so this edition does not claim
compatibility with a hosted notebook service's default interpreter.

The collapsed cell contains {count} frozen teaching files. Base85 represents compressed bytes
as text; `zlib` decompresses them; SHA-256 checks that the decoded files match this edition.
These are supplied packaging operations, not learner algorithms. `tempfile` creates an isolated
working copy; `Path` handles file locations; `sys.path` tells Python where the supplied modules
live. The code is available for inspection below and performs no package installation itself.
The subsequent lesson teaches the libraries used by the mechanisms you will implement.

Run setup on every fresh kernel. It writes scratch runtime files separately from your retained
`practical-work/{identity}` folder. Rerunning setup restores the frozen support files and keeps
your saved work. Restarting a kernel clears variables, not saved submission files. Source basis:
Sovereign Agent `{PIN}`. Some tasks use reviewed local subprocesses; they are not an OS sandbox.

<details><summary>Supplied offline setup and teaching files</summary>
"""),
        cell,
        markdown("</details>"),
    ]


def reference_start(chapter):
    if chapter in WAVE_CHAPTERS:
        make_reference = (
            "\n    source_task_class = runpy.run_path(str(COURSE_ROOT / "
            '"book/always_on/exercises/source_tasks_v1.py"))["SourceTas'
            'k"]\n    reference_task = source_task_class(COURSE_ROOT, CH'
            "APTER_NUMBER)\n    try:\n        reference_task.install(text"
            "wrap.dedent(reference_task.fragment))\n        reference_ob"
            'servation = reference_task.visible("SUPPLIED_REFERENCE_STA'
            'RT")\n        if reference_observation["status"] != "PASS":'
            '\n            raise RuntimeError("The supplied starting poi'
            'nt did not pass its connection check")\n        reference_t'
            "ask.save(COURSE_INPUT, reference_observation)\n    finally:"
            "\n        reference_task.close()\n"
        )
    else:
        reference_unit = next(u for u in UNITS if u.identity == f"ch{chapter:02d}-a")
        reference_imports = [
            ast.get_source_segment(reference_unit.solution.read_text(), node)
            for node in ast.parse(reference_unit.solution.read_text()).body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        reference_code = "\n\n".join(
            [
                *reference_imports,
                *(
                    cell.source
                    for cell in adapt_legacy(reference_unit, True)
                    if cell.cell_type == "code"
                ),
            ]
        )
        reference_encoded = base64.b85encode(zlib.compress(reference_code.encode(), 9)).decode()
        reference_lines = "\n".join(
            f'        "{reference_encoded[i : i + 80]}"'
            for i in range(0, len(reference_encoded), 80)
        )
        make_reference = (
            "    reference_encoded = (\n"
            + reference_lines
            + (
                "\n    )\n    reference_code = zlib.decompress(base64.b85deco"
                "de(reference_encoded)).decode()\n    reference_namespace = "
                "{'COURSE_ROOT': COURSE_ROOT, 'COURSE_WORK': COURSE_WORK}\n "
                "   exec(compile(reference_code, '<supplied-unit-a-referenc"
                "e>', 'exec'), reference_namespace)\n    if not COURSE_INPUT"
                ".is_file():\n        raise RuntimeError('The supplied refer"
                "ence did not produce its handoff')\n"
            )
        )
    source = """
import json
import runpy
import shutil
import textwrap
from pathlib import Path

COURSE_INPUT = COURSE_WORK / "chCHAPTER_PAD-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
MAKE_REFERENCE
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
print("The core task below validates the selected artifact before using it.")
"""
    source = source.replace("MAKE_REFERENCE", make_reference.rstrip())
    source = source.replace("CHAPTER_NUMBER", str(chapter)).replace("CHAPTER_PAD", f"{chapter:02d}")
    return [
        markdown("""
## Choose an explicit starting point for this independent notebook

This Unit B runs without Unit A. By default it prepares a **supplied reference starting point**
and labels its provenance. It is not evidence that you built Unit A. To investigate your own
successful implementation, set `LEARNER_HANDOFF` to its saved path before running the cell.
An invalid selected file refuses; it is never silently replaced with the reference.

`SourceTask` supplies copied-source execution and handoff validation; `RuntimeLab` supplies the
controlled failure experiment. Their public operations are introduced beside the main exercise.
The artifact stores identity and observations; no variables from another kernel are required.
"""),
        code("LEARNER_HANDOFF = None", "setup", "handoff-selection"),
        markdown("<details><summary>Prepare and validate the supplied starting artifact</summary>"),
        code(source, "setup", "independent-reference-start"),
        markdown("</details>"),
    ]


def adapt_legacy(unit, instructor):
    cells = copy.deepcopy(jupytext.read(unit.source).cells)
    solution_text = unit.solution.read_text()
    replacements = {}
    for node in ast.parse(solution_text).body:
        if isinstance(node, ast.FunctionDef):
            replacements[node.name] = ast.get_source_segment(solution_text, node)
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            replacements[node.targets[0].id] = ast.get_source_segment(solution_text, node)
    for cell in cells:
        if cell.cell_type == "markdown":
            cell.source = re.sub(r"\*\*Student edition v1[^\n]+", "", cell.source)
            cell.source = re.sub(
                r"^# Chapter[^\n]+",
                "## Main practical: construct, connect and challenge",
                cell.source,
            )
            cell.source = cell.source.replace(
                "Run from the locked Sovereign Agent development environment.",
                "The self-contained setup above supplies the frozen development runtime.",
            )
            cell.source = cell.source.replace(
                "This unit requires the Sovereign Agent checkout and Python 3.14.",
                "The setup above supplies the required source; use Python 3.14.",
            )
            cell.source = cell.source.replace(
                "Read the chapter and the caller around the function",
                "Inspect the supplied caller around the function",
            )
            cell.source = cell.source.replace(
                "Place the Unit A handoff beside this notebook.",
                "The starting-point cell has selected the Unit A artifact explicitly.",
            )
            cell.source = cell.source.replace(
                (
                    "A missing handoff is an explicit prerequisite failure; the"
                    " notebook will not silently substitute reference code."
                ),
                (
                    "A selected learner handoff must validate; the default refe"
                    "rence start is labelled separately."
                ),
            )
            cell.source = cell.source.replace(
                (
                    "The student release executes cleanly even before Unit A is"
                    " complete, but a missing handoff is recorded as missing. I"
                    "t is never replaced with an invented success."
                ),
                (
                    "The supplied starting point is reference evidence. It lets"
                    " you study this unit independently without claiming a comp"
                    "leted learner implementation of Unit A."
                ),
            )
            cell.source = cell.source.replace(
                "Place `ch01-unit-a-handoff-v1.json` beside this notebook.",
                "The starting-point cell selected an explicit reference or learner handoff.",
            )
            continue
        source = cell.source
        if "ROOT = next(" in source:
            tree = ast.parse(source)
            for node in reversed(tree.body):
                remove = isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in {"start", "ROOT"}
                    for target in node.targets
                )
                remove = remove or (
                    isinstance(node, ast.If) and ast.unparse(node.test) == "ROOT is None"
                )
                if remove:
                    segment = ast.get_source_segment(source, node)
                    assert source.count(segment) == 1
                    source = source.replace(
                        segment, "ROOT = COURSE_ROOT" if "ROOT = next(" in segment else "", 1
                    )
        if instructor and "learner-owned" in cell.metadata.get("tags", []):
            tree = ast.parse(source)
            targets = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
            targets += [
                target.id
                for node in tree.body
                if isinstance(node, ast.Assign)
                for target in node.targets
                if isinstance(target, ast.Name)
            ]
            matches = [name for name in targets if name in replacements]
            assert len(matches) <= 1, (unit.identity, targets)
            if matches:
                source = replacements[matches[0]]
        cell.source = source
    return cells


def transfer_cells(chapter, instructor):
    task = BANK[chapter]
    cases = repr(task["cases"])
    return [
        markdown(f"""
## Changed-constraint construction: {task["title"]}

**Allow twenty minutes.** Spend three minutes predicting, ten implementing and tracing, five
on a new case of your own, and two explaining the surviving limitation. This is dedicated work,
not an invitation to run a supplied answer. Both units revisit the same invariant after different
core experiences; in Unit B, attempt this task from memory before consulting Unit A.

{task["contract"]}

Write your expected values before running the table. Keep one accepted case and one refusal.
Your function is passed directly into the driver below. The driver copies inputs and checks
they remain unchanged; it does not replace your implementation with the reference answer.

<details><summary>Hint 1 — identify the authoritative inputs</summary>
Name the source field for each output value. Which input changes while the rule remains the same?
</details>
<details><summary>Hint 2 — choose the boundary cases</summary>
Start with exact empty, exact equality and one value on each side of the boundary where valid.
Do not add a special case for a visible product name or operation identity.
</details>
"""),
        code(task["solution"] if instructor else task["starter"], "exercise", "transfer-owned"),
        code(
            f"""
import copy
import json

TRANSFER_CASES = {cases}

def same_transfer_value(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            same_transfer_value(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            same_transfer_value(a, e) for a, e in zip(actual, expected, strict=True)
        )
    return actual == expected


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        before = copy.deepcopy(supplied)
        raised = None
        try:
            actual = candidate(*supplied)
        except NotImplementedError:
            raised = "NotImplementedError"
            actual = {{"unfinished": True}}
        except Exception as error:
            raised = type(error).__name__
            actual = {{"raises": raised}}
        expects_error = isinstance(expected, dict) and set(expected) == {{"raises"}}
        correct = raised == expected["raises"] if expects_error else (
            raised is None and same_transfer_value(actual, expected)
        )
        passed = correct and same_transfer_value(supplied, before)
        observations.append({{
            "case": label, "expected": expected, "observed": actual, "passed": passed
        }})
        print("PASS" if passed else "NEEDS_WORK", label, "expected", expected, "observed", actual)
    return observations

transfer_observations = run_transfer(transfer_check, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
""",
            "assessment",
            "transfer-invocation",
        ),
        markdown("""
### Design a counterexample and retrieve the mechanism

Add one new case with an independently calculated expected outcome to `TRANSFER_CASES` and rerun
the driver. Change one condition at a time. Then deliberately replace your candidate with a
constant answer in a temporary copy and show a case that rejects it. Restore your implementation.
Explain why that counterexample is stronger than repeating the original example with a new name.

Without viewing the worked example, write the invariant in words and trace one observed value
back to its input. Identify which part is a local fixture result and which claim would need a
live provider, host or external-system observation. Keep a first attempt even if you used a hint.
"""),
    ]


def author_unit(unit, instructor=False):
    chapter = int(unit.identity[2:4])
    letter = unit.identity[-1]
    title = re.search(r"^# .+?— (.+)$", unit.source.read_text(), re.M).group(1)
    catalog = json.loads((ROOT / "book/always_on/exercises/source-tasks-v1.json").read_text())[
        "chapters"
    ]
    specification = next((item for item in catalog if item["chapter"] == chapter), None)
    if specification:
        core_goal = (
            specification["construct"]
            if letter == "a"
            else (
                "Repair the failure: " + specification["diagnosis"] + " " + specification["connect"]
            )
        )
    else:
        core_goal = {
            "ch01-a": (
                "Implement a response reader that accepts exactly one compl"
                "eted assistant text response; connect it to the exact shop"
                " snapshot and refuse malformed envelopes."
            ),
            "ch01-b": (
                "Repair exact SKU and quantity validation, recompute the dr"
                "aft cost, and refuse a hostile proposal despite its claime"
                "d authority."
            ),
            "ch03-a": (
                "Implement next-call admission under call-count and cost-ex"
                "posure limits; trace actual tool observations through the "
                "bounded loop."
            ),
            "ch03-b": (
                "Repair failed-attempt exposure accounting and distinguish "
                "repeated tool-call IDs from exhausted provider attempts."
            ),
            "ch09-a": (
                "Implement durable admission, uncertainty and receipt trans"
                "itions; settle a reservation exactly once from matching su"
                "pplier evidence."
            ),
            "ch09-b": (
                "Repair a retry that invents an operation identity, then no"
                "rmalize another supplier's discovery response without chan"
                "ging intent."
            ),
        }[unit.identity]
    edition_label = "Instructor worked edition" if instructor else "Student edition"
    transfer_title = BANK[chapter]["title"].lower()
    core_activity = "Construct and connect" if letter == "a" else "Reproduce, diagnose and repair"
    cells = [
        markdown(f"""
# Chapter {chapter}, Unit {letter.upper()}: {title}

**{edition_label} · 90 minutes of dedicated work · 2026-09-09**

This is one of two practical units for Chapter {chapter}. Unit A constructs and connects the
mechanism; Unit B investigates a controlled failure, repairs it and transfers the invariant.
Each is a complete ninety-minute session, with its own setup and required conceptual introductions.
Basic Python variables, conditions, loops, functions, lists and dictionaries are the starting
knowledge. Libraries and specialized concepts used here are introduced below before the main task.

By the end you should be able to:

1. Explain the chapter's mechanism using a prediction and an observed intermediate result.
2. {core_goal}
3. Solve **{transfer_title}** using changed inputs and an independent expectation.
4. Retain your implementation, failed/corrected observations, causal explanation and limits.

| Minutes | Dedicated activity | Evidence you produce |
|---|---|---|
| 0–5 | State the problem and make a prediction | Initial prediction in your own words |
| 5–25 | Foundations and library examples | Values, explanations, revised predictions |
| 25–35 | Trace setup and the main interface | Input → learner function → observation |
| 35–60 | {core_activity} | Source, visible checks and runtime evidence |
| 60–80 | Implement and challenge the transfer task | Function and a new counterexample |
| 80–90 | Retrieve, explain and save | Exit ticket and retained submission |

Installation is preparation time. These are planning estimates, not measured completion times.
Use the reference primers when a term is unfamiliar; in Unit B retrieve an explanation before
re-reading it. Run All checks that the artifact executes. Unfinished student functions deliberately
produce NEEDS_WORK. Keep your first attempt before opening answers.
""")
    ]
    cells += bootstrap(unit.identity, instructor)
    cells += [
        markdown("## Commit to a prediction before the examples"),
        code(
            """
prediction_notes = {
    "prediction": "Write the expected behavior before running the worked example.",
    "reason": "Name the input and rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
""",
            "prediction",
            "learner-notes",
        ),
    ]
    cells += fragment("python-data-v1.md")
    if chapter == 2:
        primer = runpy.run_path(str(ROOT / "scripts/build_ch02_classroom_v2.py"))["primer"](
            instructor
        )
        for item in primer:
            item["source"] = item["source"].replace(
                (
                    "For the full 90-minute class, learn this introduction in n"
                    "otebook 1 and use its identical copy\nin notebook 2 as a re"
                    "ference. Starting notebook 2 on its own takes about 60 min"
                    "utes including\nthis introduction; the subsequent core acti"
                    "vities take 40 minutes."
                ),
                (
                    "This complete introduction supports either independent nin"
                    "ety-minute unit.\nIts small repair checkpoint is preparatio"
                    "n for the full tool-factory and transfer exercises."
                ),
            )
        cells += [
            code("from pydantic import BaseModel, ConfigDict, Field, ValidationError", "foundation")
        ]
        cells += [nbformat.from_dict(item) for item in primer]
    elif chapter != 1:
        cells += fragment("pydantic-v1.md")
    if chapter in SQL_CHAPTERS:
        cells += fragment("sqlite-v1.md")
    cells += fragment(f"ch{chapter:02d}-foundations-v1.md")
    if letter == "b":
        cells += reference_start(chapter)
    cells += [
        markdown("""
## Understand the supplied execution interface

The course runtime is provided so your implementation can be connected to real callers and
storage. `SourceTask(ROOT, chapter)` makes a private copy. `install(source)` replaces only the
declared function; `visible()` invokes the real chapter probe; `save(path, result)` retains a
successful implementation and its evidence. `load(path)` checks the saved identities and hashes.
`inject_failure()` changes the declared boundary; `repair(fragment)` replaces that broken fragment.
`close()` removes the scratch copy after you retain evidence. These methods are supplied harness
operations, not additional packages you must discover or install.

`RuntimeLab` provides the same copied-source failure experiment without the complete-function
construction layer. Its `run` method records exit status, observations and the compared expectation.
A subprocess log from an unfinished learner implementation is feedback about that implementation;
it is not a successful connection. A syntax error in the notebook cell itself is a separate issue
to fix. The task below names which interface it uses.

For direct-function units, the visible driver calls your callback without installing a source
string. In either case, trace where your code is invoked. Supplied fixtures, database wrappers and
replay models are labelled infrastructure; your own implementation and changed-case explanation
are the evidence of learning.
""")
    ]
    solution_imports = [
        ast.get_source_segment(unit.solution.read_text(), node)
        for node in ast.parse(unit.solution.read_text()).body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    if solution_imports:
        cells += [
            markdown(
                "The supplied helper imports below are available to your implementation. "
                "`append_event(db, name, data)` records an event in the current database "
                "transaction; it does not contact a provider or send an order."
            ),
            code("\n".join(solution_imports), "setup", "supplied-helpers"),
        ]
    cells += adapt_legacy(unit, instructor)
    cells += transfer_cells(chapter, instructor)
    if chapter == 2:
        cells += [
            markdown(
                "### Connect the reservation rule to both callers\n"
                "Predict the reported need and draft total. Both callers below invoke "
                "your function. A four-tub draft must refuse after two tubs are reserved."
            ),
            code(
                """
if TRANSFER_PASSED:
    reservation_row = {"on_hand": 1, "target": 5, "reserved": 2}
    def reservation_stock():
        return {"needed": transfer_check(reservation_row)}
    def reservation_draft(quantity):
        if quantity != transfer_check(reservation_row):
            raise ValueError("quantity differs from current sellable-stock need")
        return {"quantity": quantity, "total_pence": quantity * 325, "status": "DRAFT"}
    assert reservation_stock()["needed"] == 6
    assert reservation_draft(6)["total_pence"] == 1950
    try:
        reservation_draft(4)
    except ValueError:
        print("Old four-tub request refused by the same shared rule.")
    else:
        raise AssertionError("The draft validator ignored the new rule")
    print(reservation_stock(), reservation_draft(6))
else:
    print("Finish the transfer function before connecting its two callers.")
""",
                "integration",
                "transfer-connection",
            ),
        ]
    if chapter == 11:
        cells += [
            markdown(
                "### Observe the effect boundary\n"
                "The handler event is recorded only after your decision. Predict the "
                "event list for the refused write followed by the permitted read."
            ),
            code(
                """
if TRANSFER_PASSED:
    transfer_effects = []
    def mediated_transfer(name, allowed, consequential, authority):
        if not transfer_check(name, ["stock", "buy"], allowed, consequential, authority):
            return "REFUSED"
        transfer_effects.append(name)
        return "RAN"
    assert mediated_transfer("buy", ["buy"], True, False) == "REFUSED"
    assert transfer_effects == []
    assert mediated_transfer("stock", ["stock"], False, False) == "RAN"
    assert transfer_effects == ["stock"]
    print("Observed handler events:", transfer_effects)
else:
    print("Finish the transfer guard before inspecting its effect boundary.")
""",
                "integration",
                "transfer-connection",
            ),
        ]
    if instructor:
        cells += [
            markdown(f"""
## Instructor explanation and additional transfer cases

{BANK[chapter]["reason"]}

Ask for the learner's first prediction and attempt before revealing this version. Passing these
cases verifies behavior on these inputs; it does not establish independent student mastery.
The original core holdouts also run against the connected implementation below.
"""),
            code(
                f"""
INSTRUCTOR_TRANSFER_CASES = {BANK[chapter]["holdouts"]!r}
instructor_transfer = run_transfer(transfer_check, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_transfer)
""",
                "instructor-check",
            ),
            code(instructor_check_source(unit.holdout), "instructor-check", "core-holdout"),
        ]
    cells += [
        markdown("""
## Save your evidence and explain the result

Fill the prediction notes and your explanation before saving. Include the exact observed value,
the input or retained row that caused it, your code's invocation point, one failed hypothesis,
and the strongest claim the evidence still cannot support. A completed code cell alone does not
earn explanation credit. Do not label reference-start behavior as your own Unit A construction.

Keep this edited notebook, the Markdown if used for notes, saved handoff files, and the JSON record
below. Your work folder survives scratch cleanup and can be reopened in a new kernel. An instructor
can ask for an unseen case after the visible checks; keep your implementation general.
"""),
        code(
            f'''
explanation_notes = {{
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}}
course_submission = {{
    "unit": "{unit.identity}", "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes, "explanation": explanation_notes,
    "core_report": exercise_report, "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}}
submission_path = COURSE_WORK / "{unit.identity}-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print("COURSE_REPORT=" + json.dumps({{
    "unit": "{unit.identity}", "transfer_passed": TRANSFER_PASSED,
    "starting_evidence": course_submission["starting_evidence"],
    "edition": "{"instructor" if instructor else "student"}",
}}, sort_keys=True))
''',
            "course-report",
            "retained-evidence",
        ),
    ]
    notebook = nbformat.v4.new_notebook(cells=cells)
    notebook.metadata.update(
        {
            "kernelspec": {"display_name": "Python 3.14", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.14"},
            "course": {
                "unit": unit.identity,
                "planned_minutes": 90,
                "source_basis": PIN,
                "instructor": instructor,
                "self_contained_runtime": True,
            },
            "jupytext": {
                "text_representation": {
                    "extension": ".md",
                    "format_name": "markdown",
                    "format_version": "1.3",
                },
                "notebook_metadata_filter": "all",
            },
        }
    )
    return notebook


def instructor_check_source(path):
    source = path.read_text()
    first = ast.parse(source).body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        if isinstance(first.value.value, str):
            segment = ast.get_source_segment(source, first)
            source = source.replace(segment, "# " + first.value.value.replace("\n", "\n# "), 1)
    return source


def convert(path):
    notebook = jupytext.read(path)
    for index, cell in enumerate(notebook.cells):
        cell.id = hashlib.sha256(f"{path.name}:{index}:{cell.cell_type}".encode()).hexdigest()[:16]
        if cell.cell_type == "code":
            cell.execution_count, cell.outputs = None, []
    nbformat.validate(notebook)
    nbformat.write(notebook, path.with_suffix(".ipynb"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", action="store_true")
    parser.add_argument("--chapters", type=int, nargs="*")
    args = parser.parse_args()
    selected = [
        unit for unit in UNITS if not args.chapters or int(unit.identity[2:4]) in args.chapters
    ]
    for unit in selected:
        for instructor in (False, True):
            folder = EDITION / unit.identity[:4] / ("instructor" if instructor else "student")
            folder.mkdir(parents=True, exist_ok=True)
            source = folder / f"unit-{unit.identity[-1]}-v1.md"
            if args.author:
                notebook = author_unit(unit, instructor)
                jupytext.write(notebook, source, fmt="md")
            convert(source)
            print("BUILT", source.relative_to(ROOT), flush=True)
    print("Canonical Markdown converted; execution is a separate release gate.")


if __name__ == "__main__":
    main()
