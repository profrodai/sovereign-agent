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
    lesson_id: durable-work
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch07-b-report-outbox-lost-reply-exercise
    self_contained_runtime: true
    source_basis: chapter-7-manuscript
    source_unit: ch07-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch07-b
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

# Chapter 7, Unit B: Finish with a report, and send across a lost reply

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-26**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch07/profrod-sovereign-agent-ch07-b-report-outbox-lost-reply-exercise.ipynb) Runs on Google Colab as it ships today (Python 3.13), or on any local Python 3.12+ kernel. It needs nothing beyond Python's standard library.

This is the second of Chapter 7's two practical units. It starts from Unit A's inbox.

In that file, Lucy's opening brief is `finished`, but nothing records what the brief said. That is the fault this unit removes: **finished work nobody will hear about**. You will:

- reproduce the fault;
- build a finish that records the work and its report together;
- send the reports across a network that can lose a reply;
- derive what resending would cost before anyone chooses to do it.

By the end you should be able to:

1. State the two outbox invariants, and detect a broken one with an independent query.
2. Implement `finish`, which moves claimed work to finished and creates its report in one transaction, refusing any worker or state the state machine does not allow.
3. Explain why a send cannot be inside a transaction, and why a lost reply is recorded as *unknown*.
4. Derive the delivery, copies and duplicate probabilities of resending, and check the formulas against cases worked out by hand.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what a stop between finishing and reporting leaves | Written prediction |
| 10–25 | Two invariants, the network boundary, and your starting evidence | Worked outputs and handoff |
| 25–55 | Construct `finish` and pass the visible cases | Learner code and grade table |
| 55–70 | Drain Unit A's inbox and send across a lost reply | Independent observation |
| 70–85 | Changed-constraint task: price a resend policy | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |

These times are planning estimates, not measured completion times. Run All only checks that the notebook executes; the unfinished student functions deliberately report NEEDS_WORK. Keep your first attempt before you open the answers.


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell below creates your work folder and defines the supplied parts of the unit:

- **The work and report tables**, with triggers for the state machine and for report bodies that never change.
- **The supplied moves:** `claim` and `send_one`.
- **A controlled messaging service**, `FakeService`, which can accept a message and then lose its reply.
- **`prepare`**, a stand-in for your Chapter 3 loop. It returns a fixed answer for a request's text. The book's checkpoint runs your real loop; a Colab kernel does not have your chapter files.
- **An independent observer**, which reads the file through its own connection.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch07-b`.

<details><summary>Supplied setup, tables, moves, service and observer</summary>

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

# Chapter 7's work queue: the inbox from Unit A, and the outbox of reports.
QUEUE_SCHEMA = (
    "CREATE TABLE work ("
    " work_id INTEGER PRIMARY KEY,"
    " source_id TEXT NOT NULL UNIQUE,"
    " session_id TEXT NOT NULL,"
    " text TEXT NOT NULL,"
    " state TEXT NOT NULL CHECK (state IN ('pending', 'running', 'finished')),"
    " worker_id TEXT)",
    "CREATE TABLE reports ("
    " report_id TEXT PRIMARY KEY,"
    " work_id INTEGER NOT NULL REFERENCES work (work_id),"
    " generation INTEGER NOT NULL,"
    " body TEXT NOT NULL,"
    " delivery TEXT NOT NULL"
    " CHECK (delivery IN ('pending', 'sending', 'confirmed', 'unknown')),"
    " receipt TEXT,"
    " UNIQUE (work_id, generation))",
    "CREATE TRIGGER work_transitions BEFORE UPDATE OF state ON work"
    " WHEN NOT ((OLD.state = 'pending' AND NEW.state = 'running')"
    " OR (OLD.state = 'running' AND NEW.state = 'finished'))"
    " BEGIN SELECT RAISE(ABORT, 'transition not allowed'); END",
    "CREATE TRIGGER report_body_fixed BEFORE UPDATE OF body, work_id, generation ON reports"
    " BEGIN SELECT RAISE(ABORT, 'a report never changes what it says'); END",
)


class TransitionError(Exception):
    """A work item asked to move between states the state machine does not allow."""


class TransportUncertainError(Exception):
    """The send may have been accepted: the reply was lost."""


def connect(path):
    """A connection that never opens a transaction by itself: every BEGIN is yours."""
    return sqlite3.connect(path, autocommit=True)


def fresh_database(name, work=()):
    """A new file with the queue tables, holding the given (source, session, text, state) rows."""
    path = COURSE_WORK / f"{name}.sqlite3"
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    connection = connect(path)
    for statement in QUEUE_SCHEMA:
        connection.execute(statement)
    connection.executemany(
        "INSERT INTO work (source_id, session_id, text, state) VALUES (?, ?, ?, ?)",
        [tuple(row) for row in work],
    )
    connection.close()
    return path


def claim(connection, worker_id):
    """Move the oldest pending item to running for one worker: (work_id, text), or None."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute(
            "SELECT work_id, text FROM work WHERE state = 'pending' ORDER BY work_id LIMIT 1"
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
    return row


def send_one(connection, transport):
    """Send the oldest pending report once: (report_id, outcome), or None when none waits.

    The report is marked "sending" and committed before the network call, which never runs
    inside a transaction. A receipt confirms it; a lost reply makes it "unknown", and an
    unknown report is never picked up again here.
    """
    row = connection.execute(
        "SELECT report_id, body FROM reports WHERE delivery = 'pending'"
        " ORDER BY work_id, generation LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    connection.execute("UPDATE reports SET delivery = 'sending' WHERE report_id = ?", (row[0],))
    try:
        receipt = transport(row[0], row[1])
    except TransportUncertainError:
        outcome, receipt = "unknown", None
    else:
        outcome = "confirmed"
    connection.execute(
        "UPDATE reports SET delivery = ?, receipt = ? WHERE report_id = ?",
        (outcome, receipt, row[0]),
    )
    return row[0], outcome


class FakeService:
    """A controlled messaging service that keeps its own record of accepted sends."""

    def __init__(self, *, idempotent=False):
        self.accepted = []
        self.idempotent = idempotent
        self.lose_reply = False

    def __call__(self, report_id, body):
        if not (self.idempotent and report_id in self.accepted):
            self.accepted.append(report_id)
        if self.lose_reply:
            raise TransportUncertainError("accepted, but the reply was lost")
        return f"receipt-{len(self.accepted)}"


def prepare(text):
    """A stand-in for the Chapter 3 loop: a fixed answer for each request's text."""
    return f"Done: {text}. No purchase."


def observe(path):
    """What a separate reader finds, and whether the two outbox invariants hold."""
    reader = connect(path)
    try:
        work = reader.execute("SELECT source_id, state FROM work ORDER BY work_id").fetchall()
        reports = reader.execute(
            "SELECT report_id, source_id, delivery FROM reports JOIN work USING (work_id)"
            " ORDER BY work_id, generation"
        ).fetchall()
        unreported = reader.execute(
            "SELECT source_id FROM work WHERE state = 'finished'"
            " AND work_id NOT IN (SELECT work_id FROM reports) ORDER BY work_id"
        ).fetchall()
        (misplaced,) = reader.execute(
            "SELECT COUNT(*) FROM reports JOIN work USING (work_id) WHERE state != 'finished'"
        ).fetchone()
    finally:
        reader.close()
    return {
        "work": [list(row) for row in work],
        "reports": [list(row) for row in reports],
        "unreported": [row[0] for row in unreported],
        "r2": misplaced == 0,
    }


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch07-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0], "SQLite", sqlite3.sqlite_version)
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

A worker finishes Lucy's opening brief. The program records it in two steps: it marks the work finished, then it stores the report. The process stops between the two.

Before you run anything below, write what an independent reader will find, and whether Lucy will ever receive the brief.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write what a reader finds after a stop between finishing and reporting.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Two invariants the outbox must keep

When work finishes, the shop owes the requester a report. Write this as two invariants:

$$
\text{(R1)}\quad \forall w:\ \mathrm{state}(w) = \text{finished} \Rightarrow \exists r:\ \mathrm{work}(r) = w
\qquad
\text{(R2)}\quad \forall r:\ \mathrm{state}(\mathrm{work}(r)) = \text{finished}.
$$

- **R1:** every finished item has a report.
- **R2:** every report belongs to finished work.

Each invariant is a query an independent reader can run. The supplied observer runs both. It lists finished work that has no report under `unreported`, and reports R2 as `r2`.

The example below finishes one item in two separate statements, and stops between them. It then does the same inside one transaction. Predict both observations.

```python tags=["foundation", "worked-example"]
intro_rows = [("tg-101", "lucy", "Prepare the opening brief", "running")]


def intro_stop():
    raise RuntimeError("stopped between finish and report")


for intro_label in ["two statements", "one transaction"]:
    intro_path = fresh_database("intro-" + intro_label.replace(" ", "-"), intro_rows)
    intro_db = connect(intro_path)
    if intro_label == "one transaction":
        intro_db.execute("BEGIN IMMEDIATE")
    try:
        intro_db.execute("UPDATE work SET state = 'finished' WHERE work_id = 1")
        intro_stop()
        intro_db.execute(
            "INSERT INTO reports (report_id, work_id, generation, body, delivery)"
            " VALUES ('r1.1', 1, 1, 'brief', 'pending')"
        )
    except RuntimeError:
        if intro_db.in_transaction:
            intro_db.execute("ROLLBACK")
    intro_db.close()
    print(intro_label, "->", observe(intro_path))
```

With two statements, R1 broke. The brief is finished, and nothing on disk says Lucy is owed a report, so no later process will ever send one. In one transaction, the rollback removed the finish as well, and the work is still `running`, which is honest.

Chapter 4's atomicity is what makes this work. If the finish transaction preserves R1 and R2 whenever it runs in full, and nobody can observe it run in part, then both invariants hold in every state a reader can see.

### The network is outside the transaction

Sending a report means calling a service on the other side of a network. No database transaction can include that call: the service keeps its own records, and a crash can happen at any instant around the call.

The dangerous case is a send that the service **accepts** but whose reply never arrives. Predict what the caller sees, and what the service has recorded.

```python tags=["foundation", "worked-example"]
intro_service = FakeService()
intro_service.lose_reply = True
try:
    intro_service("r1.1", "brief")
    intro_caller_saw = "a receipt"
except TransportUncertainError as intro_error:
    intro_caller_saw = f"an error: {intro_error}"
print("the caller saw:       ", intro_caller_saw)
print("the service accepted: ", intro_service.accepted)
```

The caller heard nothing it could trust, yet the service holds the message. From the caller's side, "lost before arrival" and "accepted, reply lost" look identical.

So the outbox gives each report its own small state machine, and `send_one` follows it:

- The report is marked **sending**, and that is committed **before** the call. If the process dies during the call, a reader can see that a send may have happened.
- A receipt marks it **confirmed**.
- An uncertain failure marks it **unknown**. An unknown report is never picked up again automatically. Whether to resend it is a decision, and the transfer task below prices that decision.

## Choose an explicit starting point

This unit starts from Unit A's inbox. To use your own, replace `None` with the path to your `practical-work/ch07-a/ch07-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import shutil

COURSE_INPUT = COURSE_WORK / "ch07-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_handoff = {
        "unit": "ch07-a",
        "status": "COMPLETED",
        "work": [
            ["tg-101", "lucy", "Prepare the opening brief", "finished"],
            ["till-7", "till", "Count vanilla", "pending"],
            ["till-8", "till", "Count vanilla", "pending"],
            ["tg-102", "lucy", "Order everything", "pending"],
        ],
    }
    COURSE_INPUT.write_text(json.dumps(reference_handoff, indent=2, sort_keys=True) + "\n")
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
```

```python tags=["setup", "handoff-consumer"]
handoff = json.loads(COURSE_INPUT.read_text(encoding="utf-8"))
handoff_status = "VERIFIED" if handoff.get("status") == "COMPLETED" else "INVALID"
shop_path = fresh_database("unit-b-shop", handoff["work"])
print("UNIT_A_HANDOFF", handoff_status)
print("rebuilt inbox:", observe(shop_path))
```

The observer already reports `unreported: ['tg-101']`. Unit A's worker finished the brief with `finish_plain`, which kept no answer, so R1 was broken before this unit began.

No code can repair that row honestly. The answer was never stored, and inventing a report would tell Lucy something no worker said. The finish you build now makes the fault impossible for every item that comes after.

## Main practical: construct, connect and challenge

## 1. Construct `finish`

`finish(connection, work_id, worker_id, body, between=None)` receives a connection from `connect`, the claimed item's `work_id`, the claiming `worker_id`, and the answer `body`. It must:

- check that the item is `running` **for this worker**, and otherwise raise `TransitionError`, writing nothing;
- in **one transaction**, move the item to `finished` and insert its report with `delivery` `'pending'`;
- name the report `r{work_id}.{generation}`, where `generation` is one more than the number of reports this item already has (so `r1.1` for the first);
- call `between()`, if given, after the state change and before the report insert, and leave **neither** write if anything raises;
- return the report id, and leave no transaction open.

The starter below writes the two halves one after the other. Run the visible cases to see where it fails, then repair it.

```python tags=["exercise", "learner-owned", "ch07-finish"]
def finish(connection, work_id, worker_id, body, between=None):
    """Mark claimed work finished and create its report; return the report id."""
    connection.execute("UPDATE work SET state = 'finished' WHERE work_id = ?", (work_id,))
    if between is not None:
        between()
    report_id = f"r{work_id}.1"
    connection.execute(
        "INSERT INTO reports (report_id, work_id, generation, body, delivery)"
        " VALUES (?, ?, 1, ?, 'pending')",
        (report_id, work_id, body),
    )
    return report_id
```

<details><summary>Hint 1 — who may finish</summary>

Read `state` and `worker_id` for the item before you change anything. Only `("running", worker_id)` may finish. Anything else is a `TransitionError`, which is clearer to the caller than the trigger's refusal.

</details>

<details><summary>Hint 2 — the boundary</summary>

Everything from that read to the report insert belongs in one `BEGIN IMMEDIATE` … `COMMIT`. Any exception inside it must reach a `ROLLBACK` before it continues to the caller.

</details>

<details><summary>Hint 3 — the generation</summary>

`SELECT COUNT(*) + 1 FROM reports WHERE work_id = ?`, read inside the transaction. Chapter 12's recovery can create a second report for the same work. It will be `r{work_id}.2`, and it will never rewrite `r{work_id}.1`, which may already be on Lucy's phone.

</details>

```python tags=["assessment", "visible"]
import copy


class StopBetweenError(Exception):
    """The failure injected between the finish and the report."""


def stop_between():
    raise StopBetweenError("stopped between finish and report")


def seeded():
    """Item 1 running for w1, item 2 pending, item 3 finished with report r3.1."""
    path = fresh_database(
        "visible",
        [
            ("tg-101", "lucy", "Prepare the opening brief", "running"),
            ("till-7", "till", "Count vanilla", "pending"),
            ("till-8", "till", "Count vanilla", "finished"),
        ],
    )
    seed = connect(path)
    seed.execute("UPDATE work SET worker_id = 'w1' WHERE work_id = 1")
    seed.execute(
        "INSERT INTO reports (report_id, work_id, generation, body, delivery)"
        " VALUES ('r3.1', 3, 1, 'Counted 6 tubs.', 'pending')"
    )
    seed.close()
    return path


UNCHANGED = {
    "work": [["tg-101", "running"], ["till-7", "pending"], ["till-8", "finished"]],
    "reports": [["r3.1", "till-8", "pending"]],
}
VISIBLE_CASES = [
    (
        "finish claimed work",
        (1, "w1", "brief", None),
        "r1.1",
        {
            "work": [["tg-101", "finished"], ["till-7", "pending"], ["till-8", "finished"]],
            "reports": [["r1.1", "tg-101", "pending"], ["r3.1", "till-8", "pending"]],
        },
    ),
    (
        "a stop between finish and report",
        (1, "w1", "brief", stop_between),
        "StopBetweenError",
        UNCHANGED,
    ),
    ("a worker that did not claim it", (1, "w2", "brief", None), "TransitionError", UNCHANGED),
    ("pending work nobody claimed", (2, "w1", "brief", None), "TransitionError", UNCHANGED),
    ("finished work, finished again", (3, "w1", "brief", None), "TransitionError", UNCHANGED),
]


def grade_finish(candidate, cases):
    rows = []
    for label, arguments, expected, expected_state in cases:
        path = seeded()
        connection = connect(path)
        try:
            observed = candidate(connection, *arguments)
        except Exception as error:
            observed = type(error).__name__
        if connection.in_transaction:
            connection.execute("ROLLBACK")
            observed = f"{observed} (left a transaction open)"
        connection.close()
        seen = observe(path)
        state = {"work": seen["work"], "reports": seen["reports"]}
        passed = observed == expected and state == expected_state and not seen["unreported"]
        rows.append(
            {
                "case": label,
                "expected": expected,
                "observed": observed,
                "status": "PASS" if passed else "FAIL",
            }
        )
    return rows


visible_results = grade_finish(finish, VISIBLE_CASES)
VISIBLE_PASSED = all(row["status"] == "PASS" for row in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 2. Drain the inbox, then send across a lost reply

Once the visible cases pass, the cell below runs the rest of Lucy's morning on the file rebuilt from Unit A:

1. One worker claims each pending item, prepares an answer, and finishes it with *your* `finish`.
2. The supplied `send_one` sends the reports. The service loses the reply to the second send.
3. The independent observer reads the file.

Before running it, predict:

- each report's delivery state;
- what the service accepted;
- which finished item is still unreported, and why.

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:
    shop = connect(shop_path)
    finished_reports = []
    while (claimed := claim(shop, "w1")) is not None:
        finished_reports.append(finish(shop, claimed[0], "w1", prepare(claimed[1])))
    service = FakeService()
    sends = [send_one(shop, service)]
    service.lose_reply = True
    sends.append(send_one(shop, service))
    service.lose_reply = False
    sends.append(send_one(shop, service))
    sends.append(send_one(shop, service))
    shop.close()
    connected = observe(shop_path)
    print("reports:", finished_reports)
    print("sends:", sends)
    print("service accepted:", service.accepted)
    print("reopened:", connected)
    assert finished_reports == ["r2.1", "r3.1", "r4.1"]
    assert sends == [("r2.1", "confirmed"), ("r3.1", "unknown"), ("r4.1", "confirmed"), None]
    assert service.accepted == ["r2.1", "r3.1", "r4.1"]
    assert connected["unreported"] == ["tg-101"] and connected["r2"]
else:
    print("CONNECTION_NOT_READY — repair finish, then run again.")
```

Look at `r3.1`. The service accepted it, and the shop's record says `unknown`. That record is not a failure of the outbox. It is the outbox telling the truth: the shop does not know whether the till's count reached anyone.

`tg-101` is still unreported, inherited from Unit A. Every item finished by your `finish` has its report.

## Exit ticket

Answer three questions:

- Why must the finish and the report commit together?
- Why is `sending` committed *before* the call?
- Why does `send_one` never pick up an unknown report again by itself?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch07-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: price a resend policy

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

Should the shop resend an unknown report? Answer with arithmetic, not a feeling.

**The model.** Each send is lost before the service sees it with probability $\ell$. Otherwise the service accepts it, and its reply is lost with probability $p$. The sender cannot tell these two cases apart, so the probability of hearing nothing is

$$
r = \ell + (1 - \ell)\,p.
$$

**The policy.** Resend until a reply arrives, with at most $k$ sends. Send $i$ happens only if sends $1, \dots, i-1$ all went unanswered, which has probability $r^{i-1}$. Each send that happens is accepted with probability $1 - \ell$. So the expected number of copies the service accepts is

$$
\mathbb{E}[\text{copies}] = (1 - \ell)\sum_{i=1}^{k} r^{i-1}.
$$

**Delivery.** The report is missed only if all $k$ sends were lost before arrival, so $P(\text{delivered}) = 1 - \ell^{k}$.

**Exactly one copy** arrives in one of two ways:

- the first accepted send's reply arrives, whichever send that is;
- only one send is ever accepted, its reply is lost, and every other send is lost before arrival.

$$
P(\text{exactly one}) = (1 - p)(1 - \ell^{k}) + k\,p\,(1 - \ell)\,\ell^{k-1},
\qquad
P(\text{two or more}) = 1 - \ell^{k} - P(\text{exactly one}).
$$

**Your task.** Implement `resend_model(ell, p, k)`. It returns a dictionary with `"delivered"`, `"copies"` and `"two_or_more"`. The driver rounds each value to four decimals and compares it with a value worked out by hand, by listing every outcome.

<details><summary>Hint — the sum</summary>
Add the terms $r^{i-1}$ with a loop rather than using the closed form $(1 - r^k)/(1 - r)$. The closed form divides by zero when every send is lost before arrival ($\ell = 1$, so $r = 1$). The loop has no such case.
</details>

```python tags=["exercise", "transfer-owned"]
def resend_model(ell, p, k):
    raise NotImplementedError("Derive delivered, copies and two_or_more for at most k sends")
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    (
        "never resend (k = 1)",
        [0.02, 0.05, 1],
        {"delivered": 0.98, "copies": 0.98, "two_or_more": 0.0},
    ),
    (
        "the chapter's network, at most 3 sends",
        [0.02, 0.05, 3],
        {"delivered": 1.0, "copies": 1.0523, "two_or_more": 0.0499},
    ),
    ("a perfect network", [0.0, 0.0, 3], {"delivered": 1.0, "copies": 1.0, "two_or_more": 0.0}),
    (
        "replies never lost, requests sometimes",
        [0.1, 0.0, 3],
        {"delivered": 0.999, "copies": 0.999, "two_or_more": 0.0},
    ),
    (
        "every other reply lost, 2 sends",
        [0.0, 0.5, 2],
        {"delivered": 1.0, "copies": 1.5, "two_or_more": 0.5},
    ),
]


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        try:
            result = candidate(*supplied)
            actual = {key: round(value, 4) + 0.0 for key, value in sorted(result.items())}
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


transfer_observations = run_transfer(resend_model, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Check the derivation against sends, and retrieve the mechanism

A formula can be wrong in a way that the hand-worked cases do not catch. The cell below simulates 20,000 reports on the chapter's network, sending each one to a `FakeService` that loses requests and replies at random. It prints the model beside what the service actually accepted. Run it once your model passes.

Then answer: with $\ell = 0.02$ and $p = 0.05$, what does resending up to three times cost per hundred reports, and what does it buy? The chapter's conclusion is that only the *receiving* side can turn at-least-once sending into an exactly-once effect. Show it: rerun the simulation with `FakeService(idempotent=True)` and compare the copies.

```python tags=["exploration"]
import random


def simulate(ell, p, k, reports, *, idempotent=False, seed=7):
    rng = random.Random(seed)
    service = FakeService(idempotent=idempotent)
    delivered = two_or_more = 0
    for number in range(reports):
        report_id = f"r{number}.1"
        before = len(service.accepted)
        for _ in range(k):
            if rng.random() < ell:
                continue  # lost before the service saw it
            service.lose_reply = rng.random() < p
            try:
                service(report_id, "brief")
                break
            except TransportUncertainError:
                continue
        copies = len(service.accepted) - before
        delivered += copies > 0
        two_or_more += copies > 1
    return {
        "delivered": delivered / reports,
        "copies": len(service.accepted) / reports,
        "two_or_more": two_or_more / reports,
    }


if TRANSFER_PASSED:
    print(
        "model:    ", {key: round(value, 4) for key, value in resend_model(0.02, 0.05, 3).items()}
    )
    print("simulated:", simulate(0.02, 0.05, 3, 20_000))
    print("idempotent receiver:", simulate(0.02, 0.05, 3, 20_000, idempotent=True))
else:
    print("Finish resend_model first; then compare it with the simulation.")
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit stopped a finish with a raised exception inside one process, and it simulated a network. It did not kill the process, and it did not send to a real phone.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch07-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch07-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch07-b",
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
