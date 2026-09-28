# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 13 experiment: how long should a lease be, and what does a replacement do?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch13_leases_v1.py \
      --out ch13-leases-receipt.json

A worker's turn is one real model call (Ollama on localhost). Work lives in a SQLite table with
an owner, a generation and an expiry.
  - Turns: a pilot measures how long 40 turns take.
  - False expiry: a worker claims the work under a lease, runs one turn and then completes it
    with a fenced write. A replacement scans for expired work every 50 ms and claims it. For
    leases at the pilot's median, its 90th percentile and twice its maximum, the receipt counts
    how often the replacement took over a worker that was still working, and whether that
    worker's completion was refused.
  - Detection: a worker claims the work and stops at a random moment during a turn, as a crashed
    worker would. The receipt compares the time until the replacement claims it with
    lease - turn / 2 + scan / 2.
  - Recovery: a real model is handed the transcript of a worker that stopped after calling
    place_order, and told to continue. The receipt counts how often it places the order again.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import runpy
import sqlite3
import statistics
import tempfile
import threading
import time
from contextlib import closing
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
LEASE = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch13_leases_learner.py")
)
MODEL = "qwen2.5:0.5b"
SCAN = 0.05
TASKS = [
    "Decide whether to reorder vanilla: 2 tubs left, 5 sold per day, delivery takes 2 days.",
    "Draft a short note to the supplier asking to move Friday's delivery to Thursday.",
    "Summarize this week's sales for Lucy: vanilla 31, chocolate 24, pistachio 9.",
    "List what to check before approving an order of 6 tubs of vanilla at 250 cents each.",
    "Explain to Lucy why the pistachio order is still marked unknown.",
    "Plan tomorrow's opening checklist for the shop in three steps.",
    "Reply to a customer asking whether the shop has dairy-free flavors.",
    "Decide whether a 20% discount on pistachio is worth it to clear old stock.",
]


def chat(body):
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def turn(seed):
    """One worker turn: a real model call on one of Lucy's tasks."""
    started = time.perf_counter()
    chat(
        {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are Lucy's shop assistant."},
                {"role": "user", "content": TASKS[seed % len(TASKS)]},
            ],
            "stream": False,
            "options": {"temperature": 0.7, "seed": seed, "num_predict": 256},
        }
    )
    return time.perf_counter() - started


class Work:
    """One durable work item: owner, generation and expiry, fenced by generation."""

    def __init__(self, path):
        self.path = path
        with closing(self.connect()) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS work("
                "id INTEGER PRIMARY KEY, owner TEXT, generation INTEGER, expires REAL, result TEXT)"
            )
            connection.execute("DELETE FROM work")
            connection.execute("INSERT INTO work VALUES (1, NULL, 0, 0, NULL)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=30, isolation_level=None)

    def claim(self, owner, lease):
        """Take unfinished work if it is unowned or its lease has expired; return the generation."""
        now = time.time()
        with closing(self.connect()) as connection:
            changed = connection.execute(
                "UPDATE work SET owner=?, generation=generation+1, expires=? "
                "WHERE id=1 AND result IS NULL AND (owner IS NULL OR expires <= ?)",
                (owner, now + lease, now),
            ).rowcount
            generation = connection.execute("SELECT generation FROM work WHERE id=1").fetchone()[0]
        return generation if changed else None

    def complete(self, generation, result):
        """A fenced write: it lands only if the writer still holds the current generation."""
        with closing(self.connect()) as connection:
            current = connection.execute("SELECT generation FROM work WHERE id=1").fetchone()[0]
            if not LEASE["fenced"](generation, current):
                return False
            return bool(
                connection.execute(
                    "UPDATE work SET result=?, owner=NULL WHERE id=1 AND generation=?",
                    (result, generation),
                ).rowcount
            )


def scan_until(work, lease, stop):
    """The replacement: look for expired work every SCAN seconds until it claims it or `stop`."""
    while not stop.is_set():
        if work.claim("replacement", lease) is not None:
            return time.time()
        time.sleep(SCAN)
    return None


def false_expiry(root, pilot, trials):
    rules = [
        ("pilot median", LEASE["percentile"](pilot, 50)),
        ("pilot 90th percentile", LEASE["percentile"](pilot, 90)),
        ("twice the pilot maximum", 2 * max(pilot)),
    ]
    rows, records = [], []
    for rule, lease in rules:
        lease = round(lease, 3)
        for n in range(trials):
            work = Work(root / "work.sqlite")
            generation = work.claim("worker", lease)
            stop, taken = threading.Event(), {}
            scanner = threading.Thread(
                target=lambda w=work, s=stop, t=taken, lz=lease: t.update(at=scan_until(w, lz, s))
            )
            scanner.start()
            seconds = turn(1000 + n)
            done = work.complete(generation, "worker's result")
            stop.set()
            scanner.join()
            records.append(
                {
                    "rule": rule,
                    "lease_seconds": lease,
                    "turn_seconds": round(seconds, 3),
                    "taken_over_while_working": taken.get("at") is not None,
                    "worker_completion_accepted": done,
                }
            )
        mine = [r for r in records if r["rule"] == rule]
        rows.append(
            {
                "rule": rule,
                "lease_seconds": lease,
                "trials": trials,
                "predicted_false_expiry": round(LEASE["false_expiry_share"](pilot, lease), 3),
                "measured_false_expiry": round(
                    statistics.mean(r["taken_over_while_working"] for r in mine), 3
                ),
                "stale_completions_accepted": sum(
                    r["taken_over_while_working"] and r["worker_completion_accepted"] for r in mine
                ),
            }
        )
    return rows, records


def detection(root, pilot, trials):
    lease = round(2 * max(pilot), 3)
    typical = LEASE["percentile"](pilot, 50)
    chooser = random.Random(12)
    delays = []
    for _ in range(trials):
        work = Work(root / "crash.sqlite")
        claimed = time.time()
        work.claim("worker", lease)
        crash = claimed + chooser.uniform(0, typical)  # the worker stops here, mid-turn
        time.sleep(max(0, crash - time.time()))
        found = scan_until(work, lease, threading.Event())
        delays.append(round(found - crash, 3))
    return {
        "lease_seconds": lease,
        "turn_seconds": typical,
        "scan_seconds": SCAN,
        "trials": trials,
        "predicted_mean_delay": round(LEASE["detection_delay"](lease, typical, SCAN), 3),
        "measured_mean_delay": round(statistics.mean(delays), 3),
        "delays": delays,
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {"sku": {"type": "string"}, "quantity": {"type": "integer"}},
                "required": ["sku", "quantity"],
            },
        },
    }
    for name, description in (
        ("place_order", "Send a purchase order to the supplier. The supplier charges for it."),
        ("lookup_order", "Ask the supplier whether it already has an order for this product."),
    )
]


def recovery(samples):
    rows, runs = [], []
    for model in ("qwen2.5:0.5b", "qwen2.5:1.5b"):
        resent = looked_up = 0
        for sample in range(samples):
            messages = [
                {
                    "role": "system",
                    "content": "You are Lucy's shop assistant. You order stock with the tools.",
                },
                {"role": "user", "content": "I approve it: order 6 tubs of vanilla (SKU-VANILLA)."},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "place_order",
                                "arguments": {"sku": "SKU-VANILLA", "quantity": 6},
                            }
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "The worker handling this task stopped before the supplier's "
                    "reply was recorded. You are the replacement worker: continue the task.",
                },
            ]
            message = chat(
                {
                    "model": model,
                    "messages": messages,
                    "tools": TOOLS,
                    "stream": False,
                    "options": {"temperature": 0.7, "seed": 1 + sample, "num_predict": 150},
                }
            )["message"]
            calls = [c["function"] for c in message.get("tool_calls") or []]
            names = [c["name"] for c in calls]
            resent += "place_order" in names
            looked_up += "lookup_order" in names
            runs.append(
                {
                    "model": model,
                    "sample": sample,
                    "text": message.get("content", ""),
                    "calls": calls,
                }
            )
        rows.append(
            {"model": model, "samples": samples, "placed_again": resent, "looked_up": looked_up}
        )
    return rows, runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pilot", type=int, default=40)
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--samples", type=int, default=20)
    args = parser.parse_args()
    started = time.time()
    turn(0)  # load the model before timing
    pilot = [round(turn(1 + n), 3) for n in range(args.pilot)]
    with tempfile.TemporaryDirectory(prefix="ch13-leases-") as temporary:
        root = Path(temporary)
        rows, records = false_expiry(root, pilot, args.trials)
        crash = detection(root, pilot, args.trials)
    recovered, runs = recovery(args.samples)
    receipt = {
        "schema": 1,
        "experiment": "ch13-leases-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "model": MODEL,
        "pilot_turn_seconds": pilot,
        "false_expiry": rows,
        "detection": crash,
        "recovery": recovered,
        "seconds": round(time.time() - started, 1),
        "trials": records,
        "runs": runs,
    }
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    shown = {k: v for k, v in receipt.items() if k not in ("pilot_turn_seconds", "trials", "runs")}
    shown["detection"] = {k: v for k, v in crash.items() if k != "delays"}
    print(json.dumps(shown, indent=2))


if __name__ == "__main__":
    main()
