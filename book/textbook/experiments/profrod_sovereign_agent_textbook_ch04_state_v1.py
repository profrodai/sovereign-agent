# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 4 experiment: what survives a crash, and what a busy database costs a second writer.

Part 1, crash. A child process dies (os._exit, no cleanup, no exception handler) between the
event write and the stock write: once inside the store's transaction, once in a version with no
transaction. An independent reader then checks the invariant stock == sum(events).

Part 2, contention. A holder process takes the write lock for h ms in every T ms. A prober tries
to write at uniformly random moments. The chapter derives:

    P(refused | busy timeout 0)       = h / T
    P(refused | busy timeout >= h)    = 0
    E[wait    | busy timeout >= h]    = h^2 / (2T)   (if the waiter wakes the instant it frees)

The run records measured values next to those predictions, with a 95% Wilson interval for each
refusal rate. Where they disagree, the record says so; that is a result too.

    python book/textbook/experiments/profrod_sovereign_agent_textbook_ch04_state_v1.py
    python book/textbook/experiments/profrod_sovereign_agent_textbook_ch04_state_v1.py --quick
    python ... --out ch04-state-receipt.json

Standard library only; Python 3.12 or newer, which includes Colab's 3.13.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import os
import platform
import random
import runpy
import sqlite3
import statistics
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

LEARNER_PATH = (
    Path(__file__).resolve().parents[1]
    / "learner/profrod_sovereign_agent_ch04_state_store_learner.py"
)


def learner() -> dict:
    return runpy.run_path(str(LEARNER_PATH))


# ---- Part 1: crash between the two writes ---------------------------------------------------


def die() -> None:
    os._exit(17)  # the process ends here: no rollback, no finally, no flush of Python state


def crash_inside_transaction(path: str) -> None:
    names = learner()
    store = names["StateStore"](path)
    store.apply(names["StockEvent"]("e2", "vanilla", 7, "delivery"), between=die)


def crash_without_transaction(path: str) -> None:
    connection = sqlite3.connect(path, autocommit=True)  # every statement commits on its own
    connection.execute(
        "INSERT INTO events (event_id, sku, delta, payload, reason) VALUES (?, ?, ?, ?, ?)",
        ("e2", "vanilla", 7, '{"delta":7,"reason":"delivery","sku":"vanilla"}', "delivery"),
    )
    die()
    connection.execute("UPDATE stock SET tubs = tubs + 7 WHERE sku = 'vanilla'")


def crash_trial(target) -> dict:
    names = learner()
    with tempfile.TemporaryDirectory() as folder:
        path = str(Path(folder) / "shop.sqlite3")
        store = names["StateStore"](path)
        store.initialize()
        store.apply(names["StockEvent"]("e1", "vanilla", 2, "opening count"))
        store.close()
        child = multiprocessing.get_context("spawn").Process(target=target, args=(path,))
        child.start()
        child.join(30)
        seen = names["observe"](path)
    return {
        "exit_code": child.exitcode,
        "stock": seen["stock"],
        "events": seen["events"],
        "invariant_holds": seen["stock"] == seen["sums"],
    }


# ---- Part 2: two writers ---------------------------------------------------------------------


def holder(path: str, hold_s: float, period_s: float, stop_at: float, ready) -> None:
    connection = sqlite3.connect(path, autocommit=True, timeout=5)
    ready.set()
    while time.monotonic() < stop_at:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("UPDATE stock SET tubs = tubs WHERE sku = 'vanilla'")
        time.sleep(hold_s)
        connection.execute("COMMIT")
        time.sleep(period_s - hold_s)
    connection.close()


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


# SQLite's default busy handler (sqliteDefaultBusyCallback in main.c) sleeps these milliseconds
# between retries, then 100 ms each. A waiter therefore notices a freed lock at the next check,
# not the instant it frees.
BUSY_DELAYS_MS = (1, 2, 5, 10, 15, 20, 25, 25, 25, 50, 50, 100)


def stepped_wait_ms(hold_ms: float, period_ms: float) -> float:
    """E[wait] when the lock frees at r ~ Uniform(0, h) and the waiter checks at the busy steps."""
    checks, total = [0.0], 0.0
    for delay in BUSY_DELAYS_MS:
        total += delay
        checks.append(total)
    while checks[-1] < hold_ms:
        checks.append(checks[-1] + 100)
    expected, previous = 0.0, 0.0
    for check in checks[1:]:
        upper = min(check, hold_ms)
        if upper > previous:
            expected += (upper - previous) * check
        previous = check
        if check >= hold_ms:
            break
    return (hold_ms / period_ms) * expected / hold_ms


def contention_trial(
    hold_ms: int, period_ms: int, timeout_s: float, attempts: int, seed: int
) -> dict:
    names = learner()
    rng = random.Random(seed)
    with tempfile.TemporaryDirectory() as folder:
        path = str(Path(folder) / "shop.sqlite3")
        store = names["StateStore"](path)
        store.initialize()
        store.apply(names["StockEvent"]("e1", "vanilla", 2, "opening count"))
        store.close()
        context = multiprocessing.get_context("spawn")
        ready = context.Event()
        budget_s = attempts * period_ms / 1000 * 0.75 + 5
        process = context.Process(
            target=holder,
            args=(path, hold_ms / 1000, period_ms / 1000, time.monotonic() + budget_s, ready),
        )
        process.start()
        ready.wait(30)
        time.sleep(period_ms / 1000)
        prober = sqlite3.connect(path, autocommit=True, timeout=timeout_s)
        refused, waits = 0, []
        for _ in range(attempts):
            time.sleep(rng.uniform(0, period_ms / 1000))
            started = time.perf_counter()
            try:
                prober.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError:
                refused += 1
                continue
            waits.append((time.perf_counter() - started) * 1000)
            prober.execute("COMMIT")
        prober.close()
        process.join(budget_s + 30)
    h, t = hold_ms, period_ms
    low, high = wilson(refused, attempts)
    return {
        "hold_ms": h,
        "period_ms": t,
        "busy_timeout_s": timeout_s,
        "attempts": attempts,
        "refused": refused,
        "refused_rate": refused / attempts,
        "refused_rate_95": [round(low, 4), round(high, 4)],
        "predicted_refused_rate": h / t if timeout_s == 0 else 0.0,
        "prediction_inside_interval": low <= (h / t if timeout_s == 0 else 0.0) <= high,
        "mean_wait_ms": round(statistics.fmean(waits), 3) if waits else None,
        "predicted_mean_wait_ms": round(h * h / (2 * t), 3) if timeout_s >= h / 1000 else None,
        "predicted_mean_wait_stepped_ms": round(stepped_wait_ms(h, t), 3)
        if timeout_s >= h / 1000
        else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quick", action="store_true", help="fewer attempts, for a smoke run")
    parser.add_argument("--out", type=Path, help="write the receipt JSON here")
    parser.add_argument("--seed", type=int, default=4)
    args = parser.parse_args()
    attempts = 60 if args.quick else 300

    record = {
        "experiment": "profrod-sovereign-agent-ch04-state-v1",
        "ranAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "cpu_count": os.cpu_count(),
        },
        "crash": {
            "inside_transaction": crash_trial(crash_inside_transaction),
            "without_transaction": crash_trial(crash_without_transaction),
        },
        "contention": [
            contention_trial(hold, 100, timeout, attempts, args.seed + index)
            for index, (hold, timeout) in enumerate(
                [(10, 0.0), (30, 0.0), (50, 0.0), (10, 1.0), (30, 1.0), (50, 1.0)]
            )
        ],
    }
    for name, trial in record["crash"].items():
        print(
            f"crash {name}: exit {trial['exit_code']}, stock {trial['stock']}, "
            f"events {trial['events']}, invariant holds: {trial['invariant_holds']}"
        )
    for trial in record["contention"]:
        wait = (
            f", mean wait {trial['mean_wait_ms']} ms"
            f" (instant-wake model {trial['predicted_mean_wait_ms']},"
            f" stepped model {trial['predicted_mean_wait_stepped_ms']})"
            if trial["mean_wait_ms"] is not None and trial["busy_timeout_s"]
            else ""
        )
        print(
            f"h={trial['hold_ms']}ms T={trial['period_ms']}ms timeout={trial['busy_timeout_s']}s: "
            f"refused {trial['refused']}/{trial['attempts']} = {trial['refused_rate']:.3f} "
            f"95% [{trial['refused_rate_95'][0]:.3f}, {trial['refused_rate_95'][1]:.3f}] "
            f"(model {trial['predicted_refused_rate']:.3f}){wait}"
        )
    if args.out:
        args.out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"receipt: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
