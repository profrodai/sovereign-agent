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
    instructor: true
    lesson_id: durable-state
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch04-a-durable-state-store-solution
    self_contained_runtime: true
    source_basis: chapter-4-manuscript
    source_unit: ch04-a
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch04-a
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

# Chapter 4, Unit A: Build a durable state store

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-26**

This is the worked edition of Chapter 4, Unit A. It contains complete answers, the instructor explanation and a holdout case the student edition does not show. Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, with the standard library only.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what survives a failure between two writes | Written prediction |
| 10–35 | SQLite, constraints, transactions and `with`, worked examples | Observed outputs |
| 35–60 | Construct `apply_event` and pass the visible cases | Learner code and grade table |
| 60–70 | Connect it to a day of the shop and reopen the file | Independent observation |
| 70–85 | Changed-constraint task: decide an append without a database | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

This unit needs only Python's standard library: `sqlite3` ships with every Python, including Google Colab's. The collapsed cell below creates your work folder and defines the supplied parts of the unit: the schema, a helper that starts a fresh database file, and an **independent observer** that reads the file through its own connection. The observer never calls your code, so it cannot inherit a mistake your code makes about its own state.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch04-a`; restarting a kernel clears variables, not saved files.

<details><summary>Supplied setup, schema and observer</summary>

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

# The Chapter 4 schema, version 1: current stock and the log of events that explains it.
SCHEMA_V1 = (
    "CREATE TABLE stock (sku TEXT PRIMARY KEY, tubs INTEGER NOT NULL CHECK (tubs >= 0))",
    "CREATE TABLE events (event_id TEXT PRIMARY KEY, sku TEXT NOT NULL, delta INTEGER NOT NULL)",
    "CREATE TABLE meta (key TEXT PRIMARY KEY, value INTEGER)",
    "INSERT INTO meta VALUES ('stock.version', 1)",
)


class EventConflictError(Exception):
    """An event identity that already exists with different content."""


def connect(path):
    """A connection that never opens a transaction by itself: every BEGIN is yours."""
    return sqlite3.connect(path, autocommit=True)


def fresh_database(name):
    """A new database file with the version-1 schema, replacing any earlier copy."""
    path = COURSE_WORK / f"{name}.sqlite3"
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    connection = connect(path)
    for statement in SCHEMA_V1:
        connection.execute(statement)
    connection.close()
    return path


def observe(path):
    """What a separate reader finds in the file: stock, events and per-product event sums."""
    reader = connect(path)
    try:
        stock = dict(reader.execute("SELECT sku, tubs FROM stock ORDER BY sku"))
        events = [row[0] for row in reader.execute("SELECT event_id FROM events ORDER BY rowid")]
        sums = dict(reader.execute("SELECT sku, SUM(delta) FROM events GROUP BY sku ORDER BY sku"))
    finally:
        reader.close()
    return {"stock": stock, "events": events, "sums": sums, "invariant": stock == sums}


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch04-a"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0], "SQLite", sqlite3.sqlite_version)
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

Lucy's program records a delivery of seven vanilla tubs as two writes: an event row, then the new stock count. The process stops between them. Write what a *new* connection will find, and why, before you run anything below.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write what a new connection finds after a stop between the two writes.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### SQLite: a table in a file

A **database** here is one file. A **connection** is a handle through which your program talks to it; it is not the data itself. A **table** holds rows; each **column** is one attribute. `CREATE TABLE stock (sku TEXT PRIMARY KEY, tubs INTEGER NOT NULL)` declares two columns: `sku` identifies a product, and `PRIMARY KEY` says no two rows may share one. `INSERT` adds a row and `SELECT` reads rows.

The `?` marks in a statement are **parameters**: values travel separately from the SQL text, so a product name can never be read as an instruction. Predict what the second connection prints.

```python tags=["foundation", "worked-example"]
with tempfile.TemporaryDirectory() as intro_folder:
    intro_path = Path(intro_folder) / "intro.sqlite3"
    intro_writer = connect(intro_path)
    intro_writer.execute("CREATE TABLE stock (sku TEXT PRIMARY KEY, tubs INTEGER NOT NULL)")
    intro_writer.execute("INSERT INTO stock (sku, tubs) VALUES (?, ?)", ("vanilla", 2))
    intro_writer.close()
    intro_reader = connect(intro_path)
    intro_rows = intro_reader.execute("SELECT sku, tubs FROM stock").fetchall()
    intro_reader.close()
print("A new connection finds:", intro_rows)
assert intro_rows == [("vanilla", 2)]
```

Reading a row back through the *same* connection proves little; it may see its own unfinished work. A second connection finding the row proves the row reached the file. That is how every check in this unit works.

### Constraints refuse bad states at the storage boundary

A **constraint** is a rule the database enforces on every write, whichever code path makes it. `CHECK (tubs >= 0)` refuses a negative count; the primary key refuses a second row for the same product. A refused write raises `sqlite3.IntegrityError`. Predict which of the two inserts below is refused, and by which rule.

```python tags=["foundation", "worked-example"]
with tempfile.TemporaryDirectory() as intro_folder:
    intro_db = connect(Path(intro_folder) / "rules.sqlite3")
    intro_db.execute(
        "CREATE TABLE stock (sku TEXT PRIMARY KEY, tubs INTEGER NOT NULL CHECK (tubs >= 0))"
    )
    intro_db.execute("INSERT INTO stock VALUES ('vanilla', 2)")
    for intro_row in [("vanilla", 5), ("chocolate", -1)]:
        try:
            intro_db.execute("INSERT INTO stock VALUES (?, ?)", intro_row)
        except sqlite3.IntegrityError as intro_error:
            print("refused", intro_row, "->", intro_error)
    print("kept:", intro_db.execute("SELECT sku, tubs FROM stock").fetchall())
    intro_db.close()
```

### Transactions: all of a group, or none of it

A **transaction** groups writes. `BEGIN IMMEDIATE` starts one and takes the database's write lock. `COMMIT` publishes the whole group. `ROLLBACK` discards it. Until `COMMIT`, no other connection sees any of the group. Our connections use `autocommit=True`, so outside a transaction each statement commits on its own. That is exactly what makes a two-write change dangerous without one.

The shop's **invariant** is that each product's stock equals the sum of its events. The example below makes the same delivery twice with a failure between the two writes: once as two separate statements, once inside a transaction. Predict both results.

```python tags=["foundation", "worked-example"]
with tempfile.TemporaryDirectory() as intro_folder:
    intro_db = connect(Path(intro_folder) / "two-writes.sqlite3")
    intro_db.execute("CREATE TABLE stock (sku TEXT PRIMARY KEY, tubs INTEGER NOT NULL)")
    intro_db.execute("CREATE TABLE events (event_id TEXT PRIMARY KEY, sku TEXT, delta INTEGER)")
    intro_db.execute("INSERT INTO stock VALUES ('vanilla', 2)")
    intro_db.execute("INSERT INTO events VALUES ('e1', 'vanilla', 2)")

    def intro_state():
        stock = intro_db.execute("SELECT tubs FROM stock").fetchone()[0]
        total = intro_db.execute("SELECT SUM(delta) FROM events").fetchone()[0]
        return {"stock": stock, "sum_of_events": total, "agree": stock == total}

    try:
        intro_db.execute("INSERT INTO events VALUES ('e2', 'vanilla', 7)")
        raise RuntimeError("stopped between the two writes")
    except RuntimeError:
        pass
    print("without a transaction:", intro_state())
    intro_db.execute("DELETE FROM events WHERE event_id = 'e2'")

    intro_db.execute("BEGIN IMMEDIATE")
    try:
        intro_db.execute("INSERT INTO events VALUES ('e2', 'vanilla', 7)")
        raise RuntimeError("stopped between the two writes")
    except RuntimeError:
        intro_db.execute("ROLLBACK")
    print("inside a transaction:  ", intro_state())
    intro_db.close()
```

Without a transaction, the event committed on its own and the invariant broke by exactly seven. Inside the transaction, the rollback removed the event, and the invariant held. Notice that the failure still happened: rolling back is not recovery, so a real caller must still learn that the delivery was not recorded.

### `with` and context managers

Writing `BEGIN`, `try`, `ROLLBACK` and `COMMIT` around every change invites the one forgotten `ROLLBACK`. Python's `with` statement runs set-up code, then your block, then tear-down code, whether the block succeeds or raises. `contextlib.contextmanager` turns a generator into something `with` can use: code before `yield` runs on entry; if the block raises, the exception reappears at the `yield`. Predict the three printed lines.

```python tags=["foundation", "worked-example"]
from contextlib import contextmanager


@contextmanager
def intro_guard(label):
    print("enter", label)
    try:
        yield label
    except ValueError:
        print("undo", label)
        raise
    else:
        print("keep", label)


with intro_guard("first"):
    pass
try:
    with intro_guard("second"):
        raise ValueError("refused")
except ValueError:
    pass
```

**Retrieval check:** explain a connection versus a file, a constraint versus a check in your own code, and a rollback versus recovery. Reference: Python's [sqlite3](https://docs.python.org/3/library/sqlite3.html) and [contextlib](https://docs.python.org/3/library/contextlib.html) documentation.

## Main practical: construct, connect and challenge

Lucy's shop records every change to stock as an **event**: an opening count, a delivery, a sale. Each event has an identity chosen by whoever records it, so the same delivery reported twice carries the same `event_id`. You will implement `apply_event`, which records one event and its stock change so that the invariant can never be observed broken.

## 1. The supplied schema

```python tags=["setup"]
day_path = fresh_database("unit-a-day")
print(observe(day_path))
```

## 2. Construct `apply_event`

`apply_event(connection, event, between=None)` receives a connection from `connect` and an event dictionary with `event_id`, `sku` and `delta`. It must:

- write the event row and the stock change **in one transaction**, adding `delta` to the product's stock (a product seen for the first time starts from zero);
- return `"applied"` for a new event;
- return `"duplicate"`, writing nothing, when the same `event_id` already exists with the same `sku` and `delta`;
- raise `EventConflictError`, writing nothing, when the `event_id` exists with other content;
- call `between()`, if given, after writing the event and before changing stock, and leave **neither** write if anything raises;
- let `sqlite3.IntegrityError` from a negative count propagate, again leaving neither write.

The starter below works on the easy path only. Run the visible cases to see where it fails, then repair it.

```python tags=["exercise", "learner-owned", "ch04-apply-event"]
def apply_event(connection, event, between=None):
    """Return "applied" or "duplicate"; raise EventConflictError on a reused identity."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute(
            "SELECT sku, delta FROM events WHERE event_id = ?", (event["event_id"],)
        ).fetchone()
        if row is not None and row != (event["sku"], event["delta"]):
            raise EventConflictError(f"event {event['event_id']} already exists with other content")
        if row is None:
            connection.execute(
                "INSERT INTO events VALUES (?, ?, ?)",
                (event["event_id"], event["sku"], event["delta"]),
            )
            if between is not None:
                between()
            updated = connection.execute(
                "UPDATE stock SET tubs = tubs + ? WHERE sku = ?", (event["delta"], event["sku"])
            ).rowcount
            if updated == 0:
                connection.execute(
                    "INSERT INTO stock VALUES (?, ?)", (event["sku"], event["delta"])
                )
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")
    return "applied" if row is None else "duplicate"
```

<details><summary>Hint 1 — the boundary</summary>

Everything from the first read to the last write belongs in one `BEGIN IMMEDIATE` … `COMMIT`. Any exception inside must reach a `ROLLBACK` before it continues to the caller.

</details>

<details><summary>Hint 2 — the duplicate decision</summary>

Before writing, read the existing row for this `event_id`. No row: new. A row with the same `sku` and `delta`: duplicate. Any other row: conflict.

</details>

<details><summary>Hint 3 — the structure</summary>

`BEGIN IMMEDIATE`, then `try:` read, decide, write, `except BaseException: ROLLBACK; raise`, and `COMMIT` after the `try`. Return the decision you made.

</details>

```python tags=["assessment", "visible"]
import copy


class StopBetweenWritesError(Exception):
    """The failure injected between the event write and the stock write."""


def stop_between():
    raise StopBetweenWritesError("stopped between the two writes")


def seeded():
    """A fresh file with one committed event: vanilla opening count of 2."""
    path = fresh_database("visible")
    seed = connect(path)
    seed.execute("INSERT INTO events VALUES ('e1', 'vanilla', 2)")
    seed.execute("INSERT INTO stock VALUES ('vanilla', 2)")
    seed.close()
    return path


OPENING = {"stock": {"vanilla": 2}, "events": ["e1"]}
VISIBLE_CASES = [
    (
        "a new delivery",
        {"event_id": "e2", "sku": "vanilla", "delta": 7},
        None,
        "applied",
        {"stock": {"vanilla": 9}, "events": ["e1", "e2"]},
    ),
    (
        "the same event again",
        {"event_id": "e1", "sku": "vanilla", "delta": 2},
        None,
        "duplicate",
        OPENING,
    ),
    (
        "a reused identity",
        {"event_id": "e1", "sku": "vanilla", "delta": 5},
        None,
        "EventConflictError",
        OPENING,
    ),
    (
        "a stop between the writes",
        {"event_id": "e2", "sku": "vanilla", "delta": 7},
        stop_between,
        "StopBetweenWritesError",
        OPENING,
    ),
    (
        "a sale below zero",
        {"event_id": "e3", "sku": "vanilla", "delta": -3},
        None,
        "IntegrityError",
        OPENING,
    ),
]


def grade_apply(candidate, cases):
    rows = []
    for label, event, between, expected, expected_state in cases:
        path = seeded()
        connection = connect(path)
        supplied = copy.deepcopy(event)
        try:
            observed = candidate(connection, supplied, between)
        except Exception as error:
            observed = type(error).__name__
        if connection.in_transaction:
            connection.execute("ROLLBACK")
            observed = f"{observed} (left a transaction open)"
        connection.close()
        seen = observe(path)
        state = {"stock": seen["stock"], "events": seen["events"]}
        passed = observed == expected and state == expected_state and supplied == event
        rows.append(
            {
                "case": label,
                "expected": expected,
                "observed": observed,
                "state": state,
                "status": "PASS" if passed else "FAIL",
            }
        )
    return rows


visible_results = grade_apply(apply_event, VISIBLE_CASES)
VISIBLE_PASSED = all(row["status"] == "PASS" for row in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 3. Connect it to a day of the shop

Once the visible cases pass, the cell below runs a day of Lucy's shop through *your* `apply_event` on a real file: an opening count for two products, a delivery, a sale and the same delivery reported again. Then it closes the connection and asks the independent observer what the file holds. Predict the final stock before running it.

```python tags=["integration", "learner-path"]
DAY = [
    {"event_id": "open-v", "sku": "vanilla", "delta": 2},
    {"event_id": "open-s", "sku": "strawberry", "delta": 5},
    {"event_id": "delivery-17", "sku": "vanilla", "delta": 7},
    {"event_id": "sale-203", "sku": "vanilla", "delta": -3},
    {"event_id": "delivery-17", "sku": "vanilla", "delta": 7},
]
connected = None
if VISIBLE_PASSED:
    day_path = fresh_database("unit-a-day")
    day_connection = connect(day_path)
    outcomes = [apply_event(day_connection, event) for event in DAY]
    day_connection.close()
    connected = observe(day_path)
    print("outcomes:", outcomes)
    print("reopened:", connected)
    assert outcomes == ["applied", "applied", "applied", "applied", "duplicate"]
    assert connected["stock"] == {"strawberry": 5, "vanilla": 6}
    assert connected["invariant"]
else:
    print("CONNECTION_NOT_READY — repair apply_event, then run again.")
```

Trace `delivery-17` from the second report to the observer's output: why did the stock not rise to 13? Which rule in your code, and which row in the file, made that so?

## 4. Save the handoff

Unit B starts from this day's events. The handoff records them, and what the observer saw, in a JSON file in your work folder.

```python tags=["handoff"]
ARTIFACT_PATH = Path("ch04-unit-a-handoff-v1.json")
artifact_status = "NOT_WRITTEN"
if connected is not None:
    handoff_reader = connect(day_path)
    handoff = {
        "unit": "ch04-a",
        "status": "COMPLETED",
        "events": handoff_reader.execute(
            "SELECT event_id, sku, delta FROM events ORDER BY rowid"
        ).fetchall(),
        "observed": connected,
    }
    handoff_reader.close()
    ARTIFACT_PATH.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact_status = "WRITTEN"
    print(ARTIFACT_PATH)
else:
    print("HANDOFF_NOT_WRITTEN")
```

## Exit ticket

Explain why the rollback in the worked example is not recovery, why a duplicate must write nothing, and which observation proves the invariant held after the day.

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch04-a",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": artifact_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: decide an append without a database

**Allow fifteen minutes.** Predict for three minutes, implement and trace for eight, and spend four on a case of your own.

The chapter defines appending an event as a function on the set of events. Implement that decision on its own, with no database: `transfer_check(existing, event)` receives `existing`, a dictionary from `event_id` to a two-item list `[sku, delta]`, and an `event` dictionary. Return `"APPEND"` for a new identity, `"DUPLICATE"` when the identity exists with the same content, and `"CONFLICT"` when it exists with other content. Do not change either input.

Write your expected values before running the table. The driver passes your function in directly; it copies the inputs and checks they come back unchanged.

<details><summary>Hint — the three cases</summary>
Look up the identity first. Only then compare content.
</details>

```python tags=["exercise", "transfer-owned"]
def transfer_check(existing, event):
    previous = existing.get(event["event_id"])
    if previous is None:
        return "APPEND"
    return "DUPLICATE" if previous == [event["sku"], event["delta"]] else "CONFLICT"
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    (
        "a new identity",
        [{"e1": ["vanilla", 2]}, {"event_id": "e2", "sku": "vanilla", "delta": 7}],
        "APPEND",
    ),
    (
        "the same event again",
        [{"e1": ["vanilla", 2]}, {"event_id": "e1", "sku": "vanilla", "delta": 2}],
        "DUPLICATE",
    ),
    (
        "same identity, other amount",
        [{"e1": ["vanilla", 2]}, {"event_id": "e1", "sku": "vanilla", "delta": 3}],
        "CONFLICT",
    ),
    (
        "same identity, other product",
        [{"e1": ["vanilla", 2]}, {"event_id": "e1", "sku": "strawberry", "delta": 2}],
        "CONFLICT",
    ),
    ("an empty log", [{}, {"event_id": "e1", "sku": "vanilla", "delta": 2}], "APPEND"),
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

Add one case with an independently worked expected outcome and rerun the driver. Then replace your function with one that always answers `"APPEND"` in a temporary copy, and name the case that rejects it. Explain why a counterexample that changes one field at a time is stronger than repeating a passing case with a new identity.


## Instructor explanation and additional transfer cases

The misconception to listen for is that a transaction "retries" or "repairs". It does neither: it makes the group of writes invisible until `COMMIT`, and `ROLLBACK` discards the group. The failure still reaches the caller. The second is that a duplicate is harmless because the row "already exists": the starter's duplicate raised `IntegrityError` from the primary key *after* nothing else changed, but a duplicate delivery written as a new event with a new identity would double the stock. Idempotence comes from the identity the caller chose before the first attempt. The cases below add an identity that differs only in case and an event with a zero delta.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    (
        "identity is case-sensitive",
        [{"e1": ["vanilla", 2]}, {"event_id": "E1", "sku": "vanilla", "delta": 2}],
        "APPEND",
    ),
    (
        "a zero change is still content",
        [{"e1": ["vanilla", 0]}, {"event_id": "e1", "sku": "vanilla", "delta": 0}],
        "DUPLICATE",
    ),
]
instructor_observations = run_transfer(transfer_check, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
holdout_path = fresh_database("holdout")
holdout_connection = connect(holdout_path)
apply_event(holdout_connection, {"event_id": "h1", "sku": "chocolate", "delta": 4})
try:
    apply_event(holdout_connection, {"event_id": "h2", "sku": "mango", "delta": 3}, stop_between)
except StopBetweenWritesError:
    pass
holdout_connection.close()
holdout_seen = observe(holdout_path)
assert holdout_seen["stock"] == {"chocolate": 4}, holdout_seen
assert holdout_seen["events"] == ["h1"] and holdout_seen["invariant"]
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch04-a"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill the prediction notes and your explanation before saving. Include the exact observed value, the input that caused it, your code's invocation point, one failed hypothesis, and the strongest claim the evidence still cannot support. This unit tested a raised exception between two writes in one process; it did not stop the process itself, and it did not cut power.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch04-a",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch04-a-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch04-a",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "instructor",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
<!-- #endregion -->
