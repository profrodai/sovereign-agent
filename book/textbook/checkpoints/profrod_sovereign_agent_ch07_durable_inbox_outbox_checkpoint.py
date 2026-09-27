# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 7: the learner's WorkQueue against the chapter's acceptance examples.

Work runs through the Chapter 3 loop with authored model turns, so a report can only exist if the
learner's loop produced it. An independent reader checks every expectation. The last example is a
negative control: a finish that forgets the report must be caught.
"""

import runpy
import sqlite3
import tempfile
from dataclasses import replace
from pathlib import Path

LEARNER = Path(__file__).resolve().parents[1] / "learner"
WORK = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch07_work_queue_learner.py"))
LOOP = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch03_agent_loop_learner.py"))
StateStore, WorkQueue, FakeService = WORK["StateStore"], WORK["WorkQueue"], WORK["FakeService"]
work_once, TransitionError = WORK["work_once"], WORK["TransitionError"]


class InjectedFailureError(Exception):
    """The failure injected between finishing the work and creating its report."""


def stop():
    raise InjectedFailureError("stopped between finish and report")


def run_through_loop(text):
    """The Chapter 3 loop with authored turns: the report body is the loop's own answer."""
    model = LOOP["ReplayModel"](LOOP["opening_turns"]())
    tools = LOOP["shop_tools"]
    dispatcher = tools["build_tools"](tools["SHOP"])
    messages = [*LOOP["messages"][:1], {"role": "user", "content": text}]
    result = LOOP["run_loop"](model, dispatcher, messages, limits=LOOP["Limits"]())
    assert result.status == "COMPLETED", result.status
    return result.answer


def observe(path):
    reader = sqlite3.connect(path, autocommit=True)
    try:
        work = reader.execute("SELECT source_id, state FROM work ORDER BY work_id").fetchall()
        reports = reader.execute(
            "SELECT report_id, work_id, delivery FROM reports ORDER BY report_id"
        ).fetchall()
        orphans = reader.execute(
            "SELECT COUNT(*) FROM work WHERE state = 'finished'"
            " AND work_id NOT IN (SELECT work_id FROM reports)"
        ).fetchone()[0]
    finally:
        reader.close()
    return {"work": work, "reports": reports, "finished_without_report": orphans}


def check(label, condition):
    print(f"{'ok  ' if condition else 'FAIL'} {label}")
    if not condition:
        raise SystemExit(1)


def main():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "shop.sqlite3"
        store = StateStore(path)
        store.initialize()
        queue = WorkQueue(store, capacity=3)
        calls = []

        def counted(text):
            calls.append(text)
            return run_through_loop(text)

        check(
            "empty queue: no work, no model call",
            work_once(queue, "w1", counted) is None and calls == [],
        )
        check("admit s1", queue.admit("s1", "lucy", "Prepare the opening brief") == "accepted")
        check(
            "s1 again, same content: duplicate",
            queue.admit("s1", "lucy", "Prepare the opening brief") == "duplicate",
        )
        check(
            "s1 with other text: conflict",
            queue.admit("s1", "lucy", "Order everything") == "conflict",
        )
        check(
            "s2 with s1's text: its own work",
            queue.admit("s2", "lucy", "Prepare the opening brief") == "accepted",
        )
        check(
            "capacity 3: s3 accepted, s4 refused",
            queue.admit("s3", "till", "Count vanilla") == "accepted"
            and queue.admit("s4", "till", "Count chocolate") == "refused",
        )
        check(
            "the refused request was never stored",
            [w[0] for w in observe(path)["work"]] == ["s1", "s2", "s3"],
        )

        report = work_once(queue, "w1", counted)
        seen = observe(path)
        check(
            "s1 ran through the Chapter 3 loop and has one pending report",
            report == "r1.1"
            and calls == ["Prepare the opening brief"]
            and seen["reports"] == [("r1.1", 1, "pending")],
        )

        assignment = queue.claim("w1")
        try:
            queue.finish(assignment, "brief", between=stop)
        except InjectedFailureError:
            pass
        seen = observe(path)
        check(
            "failure between finish and report: neither committed",
            seen["work"][1] == ("s2", "running") and len(seen["reports"]) == 1,
        )

        try:
            queue.finish(replace(assignment, worker_id="w2"), "brief")
            stolen = False
        except TransitionError:
            stolen = True
        check("another worker cannot finish work it did not claim", stolen)
        queue.finish(assignment, "brief")
        check(
            "invariant: no finished work without a report",
            observe(path)["finished_without_report"] == 0,
        )

        service = FakeService()
        check("send r1.1: confirmed", queue.send_one(service) == ("r1.1", "confirmed"))
        service.lose_reply = True
        check("send r2.1, reply lost: unknown", queue.send_one(service) == ("r2.1", "unknown"))
        service.lose_reply = False
        check(
            "no pending report left; unknown is never resent",
            queue.send_one(service) is None and service.accepted == ["r1.1", "r2.1"],
        )
        store.close()

    # Negative control: a finish that forgets the report must be caught by the observer.
    class Forgetful(WorkQueue):
        def finish(self, assignment, body, *, between=None):
            with self.store.immediate() as db:
                db.execute(
                    "UPDATE work SET state = 'finished' WHERE work_id = ?", (assignment.work_id,)
                )
            return "r?"

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "shop.sqlite3"
        store = StateStore(path)
        store.initialize()
        broken = Forgetful(store)
        broken.admit("s1", "lucy", "Prepare the opening brief")
        work_once(broken, "w1", run_through_loop)
        seen = observe(path)
        store.close()
        check(
            "negative control: finished work without a report is caught",
            seen["finished_without_report"] == 1,
        )

    print(
        "Chapter 7 checkpoint: work is admitted once, finished with its report, and sent honestly."
    )


if __name__ == "__main__":
    main()
