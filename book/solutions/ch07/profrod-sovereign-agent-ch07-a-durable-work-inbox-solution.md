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
    lesson_id: durable-work
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch07-a-durable-work-inbox-solution
    self_contained_runtime: true
    source_basis: chapter-7-manuscript
    source_unit: ch07-a
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch07-a
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

# Chapter 7, Unit A: Build a durable work inbox

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-26**

This is the worked edition of Chapter 7, Unit A. It contains:

- complete answers;
- the instructor explanation;
- holdout cases that the student edition does not show.

Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, using only the standard library.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what a restart keeps | Written prediction |
| 10–35 | Occurrences, triggers, states and Little's law, as worked examples | Observed outputs |
| 35–60 | Construct `admit` and pass the visible cases | Learner code and grade table |
| 60–70 | Connect it to a morning of requests and a worker | Independent observation |
| 70–85 | Changed-constraint task: admit by promised minutes | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell below creates your work folder and defines the supplied parts of the unit:

- **The work table**, with a trigger that enforces the state machine.
- **A fresh-database helper.**
- **A supplied worker** with two moves: `claim`, which takes the oldest pending request, and `finish_plain`, which marks it finished. `finish_plain` records the work as done but does not keep the answer anywhere. Unit B starts from exactly that gap.
- **An independent observer**, which reads the file through its own connection.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch07-a`. Restarting a kernel clears variables, not saved files.

<details><summary>Supplied setup, schema, worker and observer</summary>

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
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch07-course-"))

# The only moves a work item may make.
TRANSITIONS = {("pending", "running"), ("running", "finished")}

# The inbox, as Chapter 7 defines it: one row per admitted occurrence, named by its source.
WORK_SCHEMA = (
    "CREATE TABLE work ("
    " work_id INTEGER PRIMARY KEY,"
    " source_id TEXT NOT NULL UNIQUE,"
    " session_id TEXT NOT NULL,"
    " text TEXT NOT NULL,"
    " state TEXT NOT NULL CHECK (state IN ('pending', 'running', 'finished')),"
    " worker_id TEXT)",
    "CREATE TRIGGER work_transitions BEFORE UPDATE OF state ON work"
    " WHEN NOT ((OLD.state = 'pending' AND NEW.state = 'running')"
    " OR (OLD.state = 'running' AND NEW.state = 'finished'))"
    " BEGIN SELECT RAISE(ABORT, 'transition not allowed'); END",
)


def connect(path):
    """A connection that never opens a transaction by itself: every BEGIN is yours."""
    return sqlite3.connect(path, autocommit=True)


def fresh_database(name):
    """A new database file with the work table, replacing any earlier copy."""
    path = COURSE_WORK / f"{name}.sqlite3"
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    connection = connect(path)
    for statement in WORK_SCHEMA:
        connection.execute(statement)
    connection.close()
    return path


def claim(connection, worker_id):
    """Move the oldest pending item to running for one worker; its work_id, or None."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute(
            "SELECT work_id FROM work WHERE state = 'pending' ORDER BY work_id LIMIT 1"
        ).fetchone()
        if row is not None:
            connection.execute(
                "UPDATE work SET state = 'running', worker_id = ? WHERE work_id = ?",
                (worker_id, row[0]),
            )
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")
    return None if row is None else row[0]


def finish_plain(connection, work_id):
    """Mark running work finished. The answer is not kept: Unit B's subject."""
    connection.execute("UPDATE work SET state = 'finished' WHERE work_id = ?", (work_id,))


def observe(path):
    """What a separate reader finds: every item's source, session, text and state."""
    reader = connect(path)
    try:
        work = reader.execute(
            "SELECT source_id, session_id, text, state FROM work ORDER BY work_id"
        ).fetchall()
    finally:
        reader.close()
    open_work = sum(1 for row in work if row[3] in ("pending", "running"))
    return {"work": [list(row) for row in work], "open": open_work}


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch07-a"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0], "SQLite", sqlite3.sqlite_version)
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

Lucy taps "Prepare the opening brief" in the car park, the signal drops, and she taps it again. Her program keeps accepted requests in a Python list, and it restarts before the worker reaches them. Before you run anything below, write down:

- how many requests the restarted program knows about;
- how many briefs would be prepared if the program had *not* restarted.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write what a restarted program knows, and how many briefs run otherwise.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### A list forgets; a table does not

A request the program has accepted is a promise. A promise kept only in a variable dies with the process. The example below keeps the same two requests in a list and in a table, then "restarts": a new list, and a new connection to the same file. Predict both lines.

```python tags=["foundation", "worked-example"]
with tempfile.TemporaryDirectory() as intro_folder:
    intro_list = ["Prepare the opening brief", "Prepare the opening brief"]
    intro_path = Path(intro_folder) / "inbox.sqlite3"
    intro_writer = connect(intro_path)
    intro_writer.execute("CREATE TABLE work (text TEXT NOT NULL)")
    intro_writer.executemany("INSERT INTO work VALUES (?)", [(text,) for text in intro_list])
    intro_writer.close()

    intro_list = []  # what a new process starts with
    intro_reader = connect(intro_path)
    intro_rows = intro_reader.execute("SELECT text FROM work").fetchall()
    intro_reader.close()
print("the list after a restart: ", intro_list)
print("the table after a restart:", intro_rows)
```

The table kept both requests, so it also kept the mistake: two taps became two rows, and a worker would prepare two briefs and pay the model twice. Durability alone does not answer the question "is this the same request?"

### Identity belongs to the occurrence, not the text

Lucy's two taps carry the same **source identity**: the messaging service names each message, and her phone resent the same message. An hour later the till might send the same text, "Count vanilla", for a different reason. That is a different occurrence with its own identity. **Text is not identity.**

The work table therefore makes `source_id` unique. When a repeat arrives, the decision has three outcomes:

- **duplicate:** same identity, same content. Record nothing new.
- **conflict:** same identity, different content. Someone reused a name, so refuse the request and say so.
- **new:** an identity not seen before. Admit it.

`INSERT OR IGNORE` looks like a shortcut for the duplicate case. Predict what it does to the conflicting request below.

```python tags=["foundation", "worked-example"]
with tempfile.TemporaryDirectory() as intro_folder:
    intro_db = connect(Path(intro_folder) / "identity.sqlite3")
    intro_db.execute("CREATE TABLE work (source_id TEXT PRIMARY KEY, text TEXT NOT NULL)")
    for intro_request in [
        ("tg-101", "Prepare the opening brief"),
        ("tg-101", "Prepare the opening brief"),
        ("tg-101", "Order everything"),
        ("till-7", "Count vanilla"),
        ("till-8", "Count vanilla"),
    ]:
        intro_changed = intro_db.execute(
            "INSERT OR IGNORE INTO work VALUES (?, ?)", intro_request
        ).rowcount
        print(intro_request, "stored" if intro_changed else "ignored")
    intro_db.close()
```

`INSERT OR IGNORE` treated the conflict ("Order everything" under `tg-101`) exactly like the duplicate. It stored nothing and told nobody. A reused identity is a fault, whether it comes from a buggy client or a till whose counter reset. Your `admit` must read the existing row and **compare the content**, so that a conflict is reported rather than silently dropped.

### States, and a trigger that enforces them

A work item is `pending` until a worker claims it, `running` while the worker is on it, and `finished` afterwards. A **state machine** lists the allowed moves:

$$
\text{pending} \xrightarrow{\ \text{claim}\ } \text{running} \xrightarrow{\ \text{finish}\ } \text{finished}.
$$

Everything else is forbidden. Finished work does not go back to pending, and pending work does not become finished without having run.

The setup's **trigger** makes the database refuse any other update of `state`, whichever code issues it. A trigger runs implicitly: the `UPDATE` never mentions it. That lets it catch a bug you did not know you had, and it is also why this one enforces a single rule, which you can read in `WORK_SCHEMA`. Predict which of the three updates below the database refuses.

```python tags=["foundation", "worked-example"]
with tempfile.TemporaryDirectory() as intro_folder:
    intro_db = connect(Path(intro_folder) / "states.sqlite3")
    for intro_statement in WORK_SCHEMA:
        intro_db.execute(intro_statement)
    intro_db.execute(
        "INSERT INTO work (source_id, session_id, text, state)"
        " VALUES ('tg-101', 'lucy', 'Prepare the opening brief', 'pending')"
    )
    for intro_state in ["finished", "running", "pending"]:
        try:
            intro_db.execute("UPDATE work SET state = ? WHERE source_id = 'tg-101'", (intro_state,))
            print("to", intro_state, "-> allowed")
        except sqlite3.IntegrityError as intro_error:
            print("to", intro_state, "-> refused:", intro_error)
    print("allowed moves:", sorted(TRANSITIONS))
    intro_db.close()
```

### How full the inbox gets: Little's law

An inbox that accepts everything will accept more than the worker can do on a bad morning. So admission is **bounded**. Once the number of *open* items (pending or running) reaches a capacity $C$, a new request is refused before anything is stored. A refusal the shop can explain is better than a promise it cannot keep.

To read a capacity, use **Little's law**. Let $L$ be the average number of open items, $\lambda$ the rate at which items are admitted, and $W$ the average time from admission to finish. Then

$$
L = \lambda W.
$$

**Why it holds.** Draw the open count $L(t)$ over a period of length $T$, and count the area under it in two ways:

- **Time slice by time slice**, the area is $\bar{L}\,T$.
- **Item by item**, each item adds one unit of height for as long as it is open. So the area is also the sum of all items' times in the system, $\sum_i W_i = N\bar{W}$.

Set the two counts equal: $\bar{L} = (N/T)\,\bar{W} = \lambda\bar{W}$.

The example below counts both ways on a small timeline, in whole minutes, with every item finished inside the period. Predict whether the two areas agree exactly.

```python tags=["foundation", "worked-example"]
intro_timeline = [(0, 3), (1, 7), (2, 4), (6, 9), (6, 12), (10, 13)]  # (admitted, finished)
intro_period = 15
intro_area_by_time = sum(
    sum(1 for admitted, finished in intro_timeline if admitted <= minute < finished)
    for minute in range(intro_period)
)
intro_area_by_item = sum(finished - admitted for admitted, finished in intro_timeline)
intro_rate = len(intro_timeline) / intro_period
intro_wait = intro_area_by_item / len(intro_timeline)
print("area, time by time:", intro_area_by_time, " area, item by item:", intro_area_by_item)
print(f"L = {intro_area_by_time / intro_period:.3f}   lambda * W = {intro_rate * intro_wait:.3f}")
```

The two areas agree exactly, because every item's time in the system falls inside the period. On a real queue, items still open at the edges make the two counts differ slightly, and the difference shrinks as the period grows.

**Applying it to Lucy's shop.** Her worker takes three minutes per brief, and requests arrive at 0.3 per minute. The chapter's experiment measured about five open items for an unbounded inbox, each waiting about sixteen minutes: $0.3 \times 16.4 \approx 4.9$. The capacity is the number of promises the shop is willing to have outstanding at once.

**Retrieval check:** explain in your own words:

- a list versus a table, across a restart;
- a duplicate versus a conflict;
- why the trigger refuses `pending → finished`;
- what $L$, $\lambda$ and $W$ each measure.

Reference: SQLite's [CREATE TRIGGER](https://sqlite.org/lang_createtrigger.html) and Python's [sqlite3](https://docs.python.org/3/library/sqlite3.html) documentation.

## Main practical: construct, connect and challenge

Every request that reaches Lucy's shop, from her phone, the till or a schedule, arrives with its source identity, a session and its text. You will implement `admit`, which decides what to do with one request and records the decision so that no later reader can see a half-made one.

## 1. The supplied schema

```python tags=["setup"]
inbox_path = fresh_database("unit-a-inbox")
print(observe(inbox_path))
```

## 2. Construct `admit`

`admit(connection, request, capacity)` receives a connection from `connect`, a `request` dictionary with `source_id`, `session_id` and `text`, and an integer `capacity`. It must:

- read, decide and write **in one transaction**;
- return `"duplicate"`, writing nothing, when the `source_id` exists with the same `session_id` and `text`. It answers this **even when the inbox is full**: Lucy's second tap is not new work.
- return `"conflict"`, writing nothing, when the `source_id` exists with other content;
- return `"refused"`, writing nothing, when the request is new but the number of open items (pending or running) has reached `capacity`. Finished work does not count.
- otherwise insert the request as `pending` and return `"accepted"`;
- leave no transaction open, whatever it returns or raises.

The starter below counts the requests still waiting and inserts without asking who sent them. Run the visible cases to see where it fails, then repair it.

```python tags=["exercise", "learner-owned", "ch07-admit"]
def admit(connection, request, capacity):
    """Return "accepted", "duplicate", "conflict" or "refused"."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute(
            "SELECT session_id, text FROM work WHERE source_id = ?", (request["source_id"],)
        ).fetchone()
        if row is not None:
            same = row == (request["session_id"], request["text"])
            decision = "duplicate" if same else "conflict"
        else:
            (open_work,) = connection.execute(
                "SELECT COUNT(*) FROM work WHERE state IN ('pending', 'running')"
            ).fetchone()
            if open_work >= capacity:
                decision = "refused"
            else:
                connection.execute(
                    "INSERT INTO work (source_id, session_id, text, state)"
                    " VALUES (?, ?, ?, 'pending')",
                    (request["source_id"], request["session_id"], request["text"]),
                )
                decision = "accepted"
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")
    return decision
```

<details><summary>Hint 1 — the order of the questions</summary>

Ask about identity first and capacity second. A repeat of a known occurrence is a duplicate or a conflict whatever the inbox holds. Only a *new* occurrence asks for a place.

</details>

<details><summary>Hint 2 — what counts as open</summary>

Count `WHERE state IN ('pending', 'running')`. Finished work has kept its promise and holds no place.

</details>

<details><summary>Hint 3 — why one transaction</summary>

Chapters 8 and 9 add more producers: the phone adapter, the clock and the stock monitor. If two of them each read "two open items" and then each insert, a capacity of three admits four. `BEGIN IMMEDIATE` takes the write lock before the first read, so the count cannot change between the read and the insert. Use the same structure as Chapter 4: `BEGIN IMMEDIATE`, `try:` read, decide, write, `except BaseException: ROLLBACK; raise`, then `COMMIT`.

</details>

```python tags=["assessment", "visible"]
import copy

SEED = [
    ("done-1", "lucy", "Prepare yesterday's close", "finished"),
    ("tg-101", "lucy", "Prepare the opening brief", "pending"),
    ("till-7", "till", "Count vanilla", "running"),
]


def seeded():
    """A fresh inbox holding one finished, one pending and one running item."""
    path = fresh_database("visible")
    seed = connect(path)
    seed.executemany(
        "INSERT INTO work (source_id, session_id, text, state) VALUES (?, ?, ?, ?)", SEED
    )
    seed.close()
    return path


def with_rows(*extra):
    return [list(row) for row in SEED] + [list(row) for row in extra]


VISIBLE_CASES = [
    (
        "a new occurrence with room",
        {"source_id": "till-8", "session_id": "till", "text": "Count chocolate"},
        3,
        "accepted",
        with_rows(("till-8", "till", "Count chocolate", "pending")),
    ),
    (
        "the same text, a new occurrence",
        {"source_id": "till-9", "session_id": "till", "text": "Count vanilla"},
        3,
        "accepted",
        with_rows(("till-9", "till", "Count vanilla", "pending")),
    ),
    (
        "Lucy's second tap",
        {"source_id": "tg-101", "session_id": "lucy", "text": "Prepare the opening brief"},
        3,
        "duplicate",
        with_rows(),
    ),
    (
        "a reused identity",
        {"source_id": "tg-101", "session_id": "lucy", "text": "Order everything"},
        3,
        "conflict",
        with_rows(),
    ),
    (
        "a full inbox",
        {"source_id": "tg-102", "session_id": "lucy", "text": "Order everything"},
        2,
        "refused",
        with_rows(),
    ),
    (
        "Lucy's second tap on a full inbox",
        {"source_id": "tg-101", "session_id": "lucy", "text": "Prepare the opening brief"},
        2,
        "duplicate",
        with_rows(),
    ),
]


def grade_admit(candidate, cases):
    rows = []
    for label, request, capacity, expected, expected_work in cases:
        path = seeded()
        connection = connect(path)
        supplied = copy.deepcopy(request)
        try:
            observed = candidate(connection, supplied, capacity)
        except Exception as error:
            observed = type(error).__name__
        if connection.in_transaction:
            connection.execute("ROLLBACK")
            observed = f"{observed} (left a transaction open)"
        connection.close()
        work = observe(path)["work"]
        passed = observed == expected and work == expected_work and supplied == request
        rows.append(
            {
                "case": label,
                "expected": expected,
                "observed": observed,
                "status": "PASS" if passed else "FAIL",
            }
        )
    return rows


visible_results = grade_admit(admit, VISIBLE_CASES)
VISIBLE_PASSED = all(row["status"] == "PASS" for row in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 3. Connect it to a morning of requests and a worker

Once the visible cases pass, the cell below runs a morning through *your* `admit` on a real file, with a capacity of three:

1. Lucy's tap and its repeat.
2. Two till counts with the same text.
3. A request that finds the inbox full.
4. The supplied worker claims and finishes the oldest item.
5. The refused request is sent again.

It also tries to move finished work back to pending. Then it closes the connection and asks the independent observer what the file holds.

Before running it, predict every outcome and the final state of each item.

```python tags=["integration", "learner-path"]
MORNING = [
    {"source_id": "tg-101", "session_id": "lucy", "text": "Prepare the opening brief"},
    {"source_id": "tg-101", "session_id": "lucy", "text": "Prepare the opening brief"},
    {"source_id": "till-7", "session_id": "till", "text": "Count vanilla"},
    {"source_id": "till-8", "session_id": "till", "text": "Count vanilla"},
    {"source_id": "tg-102", "session_id": "lucy", "text": "Order everything"},
]
connected = None
if VISIBLE_PASSED:
    inbox_path = fresh_database("unit-a-inbox")
    inbox = connect(inbox_path)
    outcomes = [admit(inbox, request, 3) for request in MORNING]
    claimed = claim(inbox, "w1")
    finish_plain(inbox, claimed)
    outcomes.append(admit(inbox, MORNING[-1], 3))
    try:
        inbox.execute("UPDATE work SET state = 'pending' WHERE work_id = ?", (claimed,))
        backwards = "allowed"
    except sqlite3.IntegrityError as error:
        backwards = f"refused: {error}"
    inbox.close()
    connected = observe(inbox_path)
    print("outcomes:", outcomes)
    print("finished work back to pending:", backwards)
    print("reopened:", connected)
    assert outcomes == ["accepted", "duplicate", "accepted", "accepted", "refused", "accepted"]
    assert backwards == "refused: transition not allowed"
    assert [row[3] for row in connected["work"]] == ["finished", "pending", "pending", "pending"]
    assert connected["open"] == 3
else:
    print("CONNECTION_NOT_READY — repair admit, then run again.")
```

Trace `tg-102` through the morning. Why was it refused the first time and accepted the second, although the request was identical? Which row changed state in between, and what did the worker do?

Then look at `tg-101` in the observer's output. It is `finished`, but what did the brief say? Nothing on disk records it. Unit B starts from exactly this file.

## 4. Save the handoff

Unit B starts from this morning's inbox. The handoff records every item and what the observer saw, in a JSON file in your work folder.

```python tags=["handoff"]
ARTIFACT_PATH = Path("ch07-unit-a-handoff-v1.json")
artifact_status = "NOT_WRITTEN"
if connected is not None:
    handoff = {"unit": "ch07-a", "status": "COMPLETED", "work": connected["work"]}
    ARTIFACT_PATH.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact_status = "WRITTEN"
    print(ARTIFACT_PATH)
else:
    print("HANDOFF_NOT_WRITTEN")
```

## Exit ticket

Answer three questions:

- Why must the duplicate check come before the capacity check?
- Why is `INSERT OR IGNORE` not an answer to duplicates?
- Which observation proves that finished work cannot go back to pending?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch07-a",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": artifact_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: admit by promised minutes

**Allow fifteen minutes:** three to predict, eight to implement and trace, and four for a case of your own.

A count of open items treats a one-minute stock count and a twenty-minute brief as equal promises. Lucy would rather bound the **minutes** of work she has promised. Implement that rule with no database.

`transfer_admit(open_work, request, budget)` receives:

- `open_work`: a dictionary from `source_id` to a dictionary with `session_id`, `text`, `minutes` and `state`;
- `request`: a dictionary with the same four keys, minus `state`, plus its own `source_id`;
- `budget`: an integer number of minutes.

Return `"DUPLICATE"` or `"CONFLICT"` by the same identity rule as `admit`. Content now means session, text *and* minutes. Otherwise:

- return `"REFUSE"` when the minutes of pending and running work, **plus the request's own minutes**, would exceed the budget;
- return `"ACCEPT"` otherwise.

Do not change either input. Write your expected values before you run the table. The driver passes your function in directly, copies the inputs, and checks that they come back unchanged.

<details><summary>Hint — what changed from a count</summary>
A count asks "is there a free place?", so it compares the open count with the capacity. A size asks "does this request fit?", so it adds the request's minutes before comparing. A request exactly at the budget fits.
</details>

```python tags=["exercise", "transfer-owned"]
def transfer_admit(open_work, request, budget):
    known = open_work.get(request["source_id"])
    if known is not None:
        fields = ("session_id", "text", "minutes")
        same = all(known[field] == request[field] for field in fields)
        return "DUPLICATE" if same else "CONFLICT"
    promised = sum(
        item["minutes"] for item in open_work.values() if item["state"] in ("pending", "running")
    )
    return "REFUSE" if promised + request["minutes"] > budget else "ACCEPT"
```

```python tags=["assessment", "transfer-invocation"]
BRIEF = {"session_id": "lucy", "text": "Prepare the opening brief", "minutes": 20}
COUNT = {"session_id": "till", "text": "Count vanilla", "minutes": 1}
TRANSFER_CASES = [
    (
        "an empty inbox",
        [{}, {"source_id": "tg-101", **BRIEF}, 30],
        "ACCEPT",
    ),
    (
        "a brief that does not fit",
        [
            {"tg-101": {**BRIEF, "state": "running"}, "till-7": {**COUNT, "state": "pending"}},
            {"source_id": "tg-102", **BRIEF},
            30,
        ],
        "REFUSE",
    ),
    (
        "a count that fits beside the brief",
        [{"tg-101": {**BRIEF, "state": "running"}}, {"source_id": "till-7", **COUNT}, 30],
        "ACCEPT",
    ),
    (
        "finished work holds no minutes",
        [{"tg-101": {**BRIEF, "state": "finished"}}, {"source_id": "tg-102", **BRIEF}, 30],
        "ACCEPT",
    ),
    (
        "exactly at the budget",
        [{"tg-101": {**BRIEF, "state": "pending"}}, {"source_id": "tg-102", **BRIEF}, 40],
        "ACCEPT",
    ),
    (
        "a repeat while full",
        [{"tg-101": {**BRIEF, "state": "pending"}}, {"source_id": "tg-101", **BRIEF}, 20],
        "DUPLICATE",
    ),
    (
        "same identity, other minutes",
        [
            {"tg-101": {**BRIEF, "state": "pending"}},
            {"source_id": "tg-101", **BRIEF, "minutes": 25},
            60,
        ],
        "CONFLICT",
    ),
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


transfer_observations = run_transfer(transfer_admit, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add one case with an expected outcome you worked out independently, and rerun the driver.

Then, in a temporary copy, replace your function with one that checks the budget *without* adding the request's own minutes, and name the case that rejects it. Explain which is the better promise, and why:

- a capacity counted in items;
- a capacity counted in minutes.


## Instructor explanation and additional transfer cases

Four misconceptions come up.

**"A repeat is harmless because the row already exists."** The starter shows why this is wrong. Because it inserts without asking, the unique `source_id` raised on Lucy's second tap. The caller saw an exception, not "duplicate", and a caller that treats an exception as "try again later" retries a request that was in fact admitted. `INSERT OR IGNORE` goes wrong the other way: it quietly swallows a reused identity.

**"Only waiting work takes a place."** Running work is still a promise. The starter counted only pending items, so it admitted a request into a full inbox.

**"Capacity is checked first."** Identity must come first. A full inbox must still recognize a request it has already promised, or Lucy is told "refused" for work that is already queued.

**The transaction is ceremony when there is one worker.** Admission has several *producers* from Chapter 8 onwards. Between a count and an insert, another producer can insert. Only the write lock taken before the first read makes the capacity a bound rather than a hope.

The cases below add a request larger than the whole budget and a zero-minute request on a full inbox.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    (
        "larger than the whole budget",
        [{}, {"source_id": "tg-101", **BRIEF, "minutes": 45}, 30],
        "REFUSE",
    ),
    (
        "a zero-minute request on a full inbox",
        [
            {"tg-101": {**BRIEF, "state": "running"}},
            {"source_id": "tg-9", **COUNT, "minutes": 0},
            20,
        ],
        "ACCEPT",
    ),
]
instructor_observations = run_transfer(transfer_admit, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
holdout_path = fresh_database("holdout")
holdout = connect(holdout_path)
holdout_outcomes = [
    admit(holdout, {"source_id": "h1", "session_id": "lucy", "text": "Brief"}, 2),
    admit(holdout, {"source_id": "h2", "session_id": "till", "text": "Count"}, 2),
]
holdout_claimed = claim(holdout, "w1")
holdout_outcomes.append(
    admit(holdout, {"source_id": "h3", "session_id": "till", "text": "Count"}, 2)
)
finish_plain(holdout, holdout_claimed)
holdout_outcomes.append(
    admit(holdout, {"source_id": "h3", "session_id": "till", "text": "Count"}, 2)
)
holdout_outcomes.append(
    admit(holdout, {"source_id": "h1", "session_id": "lucy", "text": "Other"}, 2)
)
holdout.close()
holdout_seen = observe(holdout_path)
assert holdout_outcomes == ["accepted", "accepted", "refused", "accepted", "conflict"], (
    holdout_outcomes
)
assert [row[0] for row in holdout_seen["work"]] == ["h1", "h2", "h3"] and holdout_seen["open"] == 2
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch07-a"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit ran one producer and one worker in one process. It did not run two producers at once, and it did not measure a real arrival rate.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch07-a",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch07-a-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch07-a",
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
