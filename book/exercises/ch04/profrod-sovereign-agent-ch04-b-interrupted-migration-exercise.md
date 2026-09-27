---
jupyter:
  authors:
  - name: Prof Rod
    website: https://profrod.ai
  course:
    book_url: https://profrod.ai/book
    community_url: https://profrod.ai/community
    distribution_version: '2026-09-10'
    edition: nineteen-chapter-v1
    instructor: false
    lesson_id: durable-state
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch04-b-interrupted-migration-exercise
    self_contained_runtime: true
    source_basis: chapter-4-manuscript
    source_unit: ch04-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch04-b
  jupytext:
    notebook_metadata_filter: all
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  language_info:
    name: python
    version: '3.12'
---

# Chapter 4, Unit B: Diagnose an interrupted migration and repair it

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-26**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch04/profrod-sovereign-agent-ch04-b-interrupted-migration-exercise.ipynb) Runs on Google Colab as it ships today (Python 3.13), or on any local Python 3.12+ kernel. It needs nothing beyond Python's standard library.

This is the second practical unit for Chapter 4. Unit A built `apply_event` and saved a day of Lucy's shop. Here the shop's program changes its schema: events gain a `reason` column. You will reproduce a schema change that stops half-way, see why rerunning it fails, and build `migrate` so a change and its version number commit together. Retrieve Unit A's transaction rule before re-reading it below.

By the end you should be able to:

1. Explain why a schema version must commit in the same transaction as the change it names.
2. Reproduce a half-applied migration and explain the error a rerun produces.
3. Implement `migrate`, which applies every missing version in order in one transaction and refuses a database newer than the program.
4. Plan which migrations a file needs from its version and the program's, for any owner.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what a rerun does after a stop half-way through a migration | Written prediction |
| 10–25 | Versions form a line; choose your starting evidence | Worked outputs and handoff |
| 25–40 | Reproduce the interrupted migration | Independent failure evidence |
| 40–65 | Construct `migrate` and pass the visible cases | Learner code and grade table |
| 65–75 | Migrate Unit A's shop | Independent observation |
| 75–85 | Changed-constraint task: plan migrations for any owner | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |

These are planning estimates, not measured completion times. Run All checks that the notebook executes; unfinished student functions deliberately produce NEEDS_WORK.


## Run the self-contained setup

This unit needs only Python's standard library. The collapsed cell creates your work folder and defines the supplied parts: the version-1 and version-2 migrations, helpers that read and write a version number, a fresh-database helper, and the independent observer. It also holds a supplied reference `apply_event`, used only when you start from the supplied Unit A instead of your own.

<details><summary>Supplied setup, migrations and observer</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch04-course-"))

# The stock tables' line of versions. Each migration turns version k - 1 into version k.
MIGRATIONS = {
    1: (
        "CREATE TABLE stock (sku TEXT PRIMARY KEY, tubs INTEGER NOT NULL CHECK (tubs >= 0))",
        "CREATE TABLE events"
        " (event_id TEXT PRIMARY KEY, sku TEXT NOT NULL, delta INTEGER NOT NULL)",
    ),
    2: ("ALTER TABLE events ADD COLUMN reason TEXT NOT NULL DEFAULT 'unrecorded'",),
}


class UnsupportedSchemaError(Exception):
    """A database written by a newer program than this one."""


def connect(path):
    """A connection that never opens a transaction by itself: every BEGIN is yours."""
    return sqlite3.connect(path, autocommit=True)


def read_version(connection, owner="stock"):
    """The version of one owner's tables; 0 when the file has never been migrated for it."""
    exists = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'meta'"
    ).fetchone()
    if not exists:
        return 0
    row = connection.execute(
        "SELECT value FROM meta WHERE key = ?", (f"{owner}.version",)
    ).fetchone()
    return int(row[0]) if row else 0


def write_version(connection, owner, version):
    connection.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER)")
    connection.execute(
        "INSERT INTO meta VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = excluded.value",
        (f"{owner}.version", version),
    )


def fresh_database(name, version=1):
    """A new file at the given stock version (0 means empty), replacing any earlier copy."""
    path = COURSE_WORK / f"{name}.sqlite3"
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    connection = connect(path)
    for step in range(1, version + 1):
        for statement in MIGRATIONS[step]:
            connection.execute(statement)
    if version:
        write_version(connection, "stock", version)
    connection.close()
    return path


def columns(path, table):
    reader = connect(path)
    try:
        return [row[1] for row in reader.execute(f"PRAGMA table_info({table})")]
    finally:
        reader.close()


def observe(path):
    """What a separate reader finds: version, event columns, stock and events."""
    reader = connect(path)
    try:
        version = read_version(reader)
        tables = {row[0] for row in reader.execute("SELECT name FROM sqlite_schema")}
        stock = (
            dict(reader.execute("SELECT sku, tubs FROM stock ORDER BY sku"))
            if "stock" in tables
            else {}
        )
        events = (
            [row[0] for row in reader.execute("SELECT event_id FROM events ORDER BY rowid")]
            if "events" in tables
            else []
        )
    finally:
        reader.close()
    return {
        "version": version,
        "event_columns": columns(path, "events") if "events" in tables else [],
        "stock": stock,
        "events": events,
    }


def reference_apply(connection, event_id, sku, delta):
    """The supplied reference for Unit A's apply_event, used only for a reference start."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("INSERT INTO events VALUES (?, ?, ?)", (event_id, sku, delta))
        updated = connection.execute(
            "UPDATE stock SET tubs = tubs + ? WHERE sku = ?", (delta, sku)
        ).rowcount
        if updated == 0:
            connection.execute("INSERT INTO stock VALUES (?, ?)", (sku, delta))
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch04-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0], "SQLite", sqlite3.sqlite_version)
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

A migration adds the `reason` column, then writes "the stock tables are now version 2". The process stops between those two steps. Write what the file holds afterwards, and what happens when the program starts again and runs the migration from version 1.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write what the file holds, and what a rerun does, after a stop half-way.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Versions form a line

A file's schema has a **version**: 0 for an empty file, then 1, 2 and so on. A **migration** turns version $k-1$ into version $k$. To bring a file from version $a$ up to version $b$, apply the migrations $a+1, a+2, \dots, b$ in order; there is exactly one path. The file remembers its version in a small `meta` table, under the name of the tables' owner, here `stock.version`. Chapter 5's memory and Chapter 7's work keep their own lines under their own names, so the order the chapters are written in never decides each other's numbers.

Predict what the reader below prints for an empty file and for a version-1 file.

```python tags=["foundation", "worked-example"]
empty_path = fresh_database("intro-empty", version=0)
v1_path = fresh_database("intro-v1", version=1)
print("empty file:", observe(empty_path))
print("version 1: ", observe(v1_path))
```

Two rules make migration safe. **Each migration commits with its version number:** after any stop, the file is at the old version with the old tables, or at the new version with the new tables, never in between. **A newer file is refused before anything changes:** a program that knows versions up to 2 cannot know what version 3 means, and writing to it could destroy information a newer program depends on. SQLite changes a table's structure inside a transaction like any other write, so `ALTER TABLE` rolls back too.

## Choose an explicit starting point

This unit starts from Unit A's saved day. To use your own, replace `None` with the path to your `practical-work/ch04-a/ch04-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference; your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import shutil

COURSE_INPUT = COURSE_WORK / "ch04-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_day = [
        ("open-v", "vanilla", 2),
        ("open-s", "strawberry", 5),
        ("delivery-17", "vanilla", 7),
        ("sale-203", "vanilla", -3),
    ]
    reference_path = fresh_database("reference-unit-a")
    reference_connection = connect(reference_path)
    for reference_event in reference_day:
        reference_apply(reference_connection, *reference_event)
    reference_connection.close()
    reference_handoff = {
        "unit": "ch04-a",
        "status": "COMPLETED",
        "events": [list(event) for event in reference_day],
        "observed": observe(reference_path),
    }
    COURSE_INPUT.write_text(json.dumps(reference_handoff, indent=2, sort_keys=True) + "\n")
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
```

```python tags=["setup", "handoff-consumer"]
handoff = json.loads(COURSE_INPUT.read_text(encoding="utf-8"))
handoff_status = "VERIFIED" if handoff.get("status") == "COMPLETED" else "INVALID"
shop_path = fresh_database("unit-b-shop")
shop_connection = connect(shop_path)
for handoff_event in handoff["events"]:
    reference_apply(shop_connection, *handoff_event)
shop_connection.close()
print("UNIT_A_HANDOFF", handoff_status)
print("rebuilt shop:", observe(shop_path))
```

## 1. Reproduce the interrupted migration

The supplied `hasty_migrate` below does what a first attempt usually does: it runs each migration statement as it comes, then writes the new version. With `autocommit=True` each statement commits on its own. The experiment stops it after the `ALTER TABLE` and before the version write, on a copy of the shop, and then runs it again.

```python tags=["failure-experiment"]
class StopHalfwayError(Exception):
    """The failure injected after a migration's statements and before its version write."""


def stop_halfway():
    raise StopHalfwayError("stopped after the change, before the version")


def hasty_migrate(connection, migrations, owner="stock", between=None):
    before = read_version(connection, owner)
    for version in range(before + 1, max(migrations) + 1):
        for statement in migrations[version]:
            connection.execute(statement)
        if between is not None:
            between()
        write_version(connection, owner, version)
    return before, max(migrations)


experiment_path = COURSE_WORK / "experiment.sqlite3"
shutil.copy2(shop_path, experiment_path)
experiment = connect(experiment_path)
try:
    hasty_migrate(experiment, MIGRATIONS, between=stop_halfway)
except StopHalfwayError as stopped:
    print("first run:", stopped)
print("after the stop:", observe(experiment_path)["version"], columns(experiment_path, "events"))
try:
    hasty_migrate(experiment, MIGRATIONS)
    rerun = "completed"
except sqlite3.OperationalError as error:
    rerun = f"OperationalError: {error}"
print("rerun:", rerun)
experiment.close()
assert rerun.startswith("OperationalError")
```

The `reason` column exists but the file still says version 1. The rerun believes it must add the column and fails: `duplicate column name`. The program cannot start. Nothing was lost, but nothing can move either, and the file needs a person to repair it by hand. That is the cost of a version that did not commit with its change.

## 2. Construct `migrate`

`migrate(connection, migrations, owner="stock", between=None)` receives a connection from `connect`, a dictionary of migrations like `MIGRATIONS`, and the owner's name. It must:

- read the owner's current version with `read_version`;
- raise `UnsupportedSchemaError` if that version is above the newest migration it knows, **before changing anything**;
- apply every missing migration in order, call `between()` (if given) after each migration's statements, and write the newest version with `write_version`;
- do all of that **in one transaction**, so that any exception leaves the file exactly as it was;
- return `(before, after)`, the version found and the version written.

The starter is `hasty_migrate`. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch04-migrate"]
def migrate(connection, migrations, owner="stock", between=None):
    """Return (before, after); raise UnsupportedSchemaError for a newer file."""
    return hasty_migrate(connection, migrations, owner, between)
```

<details><summary>Hint 1 — what must commit together</summary>

The statements of every missing migration and the new version number belong to one transaction. Reading the old version belongs in it too, so nothing can change between the read and the writes.

</details>

<details><summary>Hint 2 — refusing a newer file</summary>

Compare the version you read with `max(migrations)` before running any statement. Raising inside the transaction is enough to leave the file untouched, as long as your handler rolls back.

</details>

<details><summary>Hint 3 — the structure</summary>

It is Unit A's shape again: `BEGIN IMMEDIATE`, then `try:` read, check, migrate, write, `except BaseException: ROLLBACK; raise`, and `COMMIT` after the `try`.

</details>

```python tags=["assessment", "visible"]
import copy


def grade_migrate(candidate):
    rows = []

    def record(label, expected, observed, state, expected_state):
        passed = observed == expected and state == expected_state
        rows.append(
            {
                "case": label,
                "expected": expected,
                "observed": observed,
                "status": "PASS" if passed else "FAIL",
            }
        )

    def attempt(path, between=None, migrations=MIGRATIONS):
        connection = connect(path)
        supplied = copy.deepcopy(migrations)
        try:
            observed = candidate(connection, supplied, "stock", between)
        except Exception as error:
            observed = type(error).__name__
        if connection.in_transaction:
            connection.execute("ROLLBACK")
            observed = f"{observed} (left a transaction open)"
        connection.close()
        return observed

    v2_columns = ["event_id", "sku", "delta", "reason"]
    path = fresh_database("visible", version=1)
    record(
        "version 1 to 2",
        (1, 2),
        attempt(path),
        (observe(path)["version"], columns(path, "events")),
        (2, v2_columns),
    )
    record(
        "run again: nothing to do",
        (2, 2),
        attempt(path),
        (observe(path)["version"], columns(path, "events")),
        (2, v2_columns),
    )
    path = fresh_database("visible", version=1)
    observed = attempt(path, between=stop_halfway)
    record(
        "a stop half-way leaves version 1",
        "StopHalfwayError",
        observed,
        (observe(path)["version"], columns(path, "events")),
        (1, ["event_id", "sku", "delta"]),
    )
    record("then a clean rerun works", (1, 2), attempt(path), observe(path)["version"], 2)
    path = fresh_database("visible", version=0)
    record(
        "an empty file",
        (0, 2),
        attempt(path),
        (observe(path)["version"], columns(path, "events")),
        (2, v2_columns),
    )
    path = fresh_database("visible", version=2)
    writer = connect(path)
    writer.execute("UPDATE meta SET value = 3 WHERE key = 'stock.version'")
    writer.execute("INSERT INTO stock VALUES ('vanilla', 2)")
    writer.close()
    record(
        "a newer file is refused",
        "UnsupportedSchemaError",
        attempt(path),
        observe(path)["stock"],
        {"vanilla": 2},
    )
    return rows


visible_results = grade_migrate(migrate)
VISIBLE_PASSED = all(row["status"] == "PASS" for row in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 3. Migrate Unit A's shop

Once the visible cases pass, the cell below migrates the shop rebuilt from your starting evidence, twice, and asks the observer what the file holds. Predict the second result before running.

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:
    before_events = observe(shop_path)["events"]
    shop_connection = connect(shop_path)
    first = migrate(shop_connection, MIGRATIONS)
    second = migrate(shop_connection, MIGRATIONS)
    reasons = shop_connection.execute("SELECT DISTINCT reason FROM events").fetchall()
    shop_connection.close()
    connected = observe(shop_path)
    print("first:", first, "second:", second, "reasons:", reasons)
    print("reopened:", connected)
    assert first == (1, 2) and second == (2, 2)
    assert connected["events"] == before_events and reasons == [("unrecorded",)]
else:
    print("CONNECTION_NOT_READY — repair migrate, then run again.")
```

Every event from Unit A survived, and each gained the default reason. The second call found nothing to do: initialization, like `apply_event`, is idempotent.

## Exit ticket

Explain why the version must commit with the change, why the refusal of a newer file comes before any statement, and what the rerun error in the experiment would have cost Lucy on a Monday morning.

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch04-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: plan migrations for any owner

**Allow fifteen minutes.** Try this from memory before looking back.

Implement `transfer_check(current, known)`: `current` is a file's version for one owner and `known` is the newest version the program knows, both non-negative integers. Return the list of versions to apply, in order, or the string `"REFUSE"` when the file is newer than the program. An up-to-date file needs `[]`. The same rule serves every owner, which is why it is worth getting exactly right.

<details><summary>Hint — the three regions</summary>
Newer than known: refuse. Equal: nothing. Older: every version after `current` up to and including `known`.
</details>

```python tags=["exercise", "transfer-owned"]
def transfer_check(current, known):
    raise NotImplementedError("Plan the migrations before running any")
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("an empty file", [0, 2], [1, 2]),
    ("one version behind", [1, 2], [2]),
    ("up to date", [2, 2], []),
    ("a newer file", [3, 2], "REFUSE"),
    ("a new owner's first version", [0, 1], [1]),
]


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        try:
            actual = candidate(*supplied)
        except NotImplementedError:
            actual = {"unfinished": True}
        except Exception as error:
            actual = {"raises": type(error).__name__}
        passed = actual == expected and supplied == arguments
        observations.append(
            {"case": label, "expected": expected, "observed": actual, "passed": passed}
        )
        print("PASS" if passed else "NEEDS_WORK", label, "expected", expected, "observed", actual)
    return observations


transfer_observations = run_transfer(transfer_check, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case where `known` is 0, work out the answer independently and rerun. Then replace your function with one that ignores `current` in a temporary copy, and name the case that rejects it. Explain which case would have caught the experiment's hasty migration, and why.


## Save your evidence and explain the result

Fill the prediction notes and your explanation before saving. Include the exact observed value, the input that caused it, your code's invocation point, one failed hypothesis, and the strongest claim the evidence still cannot support. This unit raised an exception inside one process; it did not stop the process or the machine.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch04-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch04-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch04-b",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "student",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
<!-- #endregion -->
