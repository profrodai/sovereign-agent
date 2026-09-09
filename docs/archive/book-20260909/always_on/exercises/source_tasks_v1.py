"""Run learner-authored functions in copies of the real cumulative runtime.

Reviewed local classroom code only. Subprocesses are not a security sandbox.
The existing RuntimeLab owns subprocess execution and original-source checks.
"""

from __future__ import annotations

import ast
import hashlib
import json
import runpy
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
RuntimeLab = runpy.run_path(str(HERE.parent / "educator/runtime_labs_v1.py"))["RuntimeLab"]
TASKS = json.loads((HERE / "source-tasks-v1.json").read_text())["chapters"]


class SourceTask(RuntimeLab):
    """Replace a complete named function, preserving its real callers and storage."""

    def __init__(self, root, chapter):
        super().__init__(root, chapter)
        self.chapter = chapter
        self.task = next(row for row in TASKS if row["chapter"] == chapter)
        nodes = [
            node
            for node in ast.walk(ast.parse(self.original))
            if isinstance(node, ast.FunctionDef) and node.name == self.task["function"]
        ]
        if len(nodes) != 1:
            raise ValueError("construction target must identify exactly one function")
        node = nodes[0]
        self.function_name = node.name
        self.indent = " " * node.col_offset
        lines = self.original.splitlines(keepends=True)
        self.fragment = "".join(lines[node.lineno - 1 : node.end_lineno])
        self.installed = None

    def install(self, source):
        if not isinstance(source, str) or not source.strip():
            raise ValueError("submit a complete function definition")
        parsed = ast.parse(textwrap.dedent(source))
        if (
            len(parsed.body) != 1
            or not isinstance(parsed.body[0], ast.FunctionDef)
            or parsed.body[0].name != self.function_name
        ):
            raise ValueError("submit only the declared complete function")
        replacement = textwrap.indent(textwrap.dedent(source).strip() + "\n", self.indent)
        if self.original.count(self.fragment) != 1:
            raise ValueError("construction target is no longer unique")
        updated = self.original.replace(self.fragment, replacement, 1)
        ast.parse(updated)
        self.target.write_text(updated)
        self.installed = textwrap.dedent(source).strip() + "\n"

    def inject_failure(self):
        if self.installed is None:
            raise ValueError("install the Unit A implementation before injecting the failure")
        source = self.target.read_text()
        before, after = self.spec["before"], self.spec["after"]
        if source.count(before) != 1:
            raise ValueError("Unit B requires the named mutation boundary exactly once")
        self.target.write_text(source.replace(before, after, 1))

    def visible(self, phase="CONNECTED"):
        self.probe.write_text(self.spec["probe"])
        return self.run(phase, expected=self.spec["expected_baseline"])

    def transfer(self, probe):
        self.probe.write_text(Path(probe).read_text())
        return self.run("TRANSFER", expected={"passed": True})

    def save(self, path, record):
        if record["status"] != "PASS" or self.installed is None:
            raise ValueError("an observed successful connection is required for the handoff")
        document = {
            "schema": 1,
            "chapter": self.chapter,
            "runtime_sha256": hashlib.sha256(self.original.encode()).hexdigest(),
            "implementation": self.installed,
            "implementation_sha256": hashlib.sha256(self.installed.encode()).hexdigest(),
            "observation": record["observation"],
            "status": "VISIBLE_PASSED",
        }
        Path(path).write_text(json.dumps(document, sort_keys=True, indent=2) + "\n")

    def load(self, path):
        document = json.loads(Path(path).read_text())
        if (
            document.get("schema") != 1
            or document.get("chapter") != self.chapter
            or document.get("status") != "VISIBLE_PASSED"
            or document.get("runtime_sha256") != hashlib.sha256(self.original.encode()).hexdigest()
            or not isinstance(document.get("implementation"), str)
            or document.get("implementation_sha256")
            != hashlib.sha256(document["implementation"].encode()).hexdigest()
        ):
            raise ValueError("handoff identity or bytes do not match this chapter")
        self.install(document["implementation"])
        return document


def source_task(root, chapter):
    return SourceTask(root, chapter)
