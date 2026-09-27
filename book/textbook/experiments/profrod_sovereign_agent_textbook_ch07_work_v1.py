# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 7 experiment: what retrying a lost reply costs, and Little's law on the real queue.

Part 1, delivery. Each send is lost before the service sees it with probability l, or accepted
with its reply lost with probability p; either way the sender sees no reply, with probability
r = l + (1 - l) p. The chapter derives, for one report:

    never resend           P(delivered) = 1 - l         E[copies] = 1 - l
    retry up to k times    P(delivered) = 1 - l^k      E[copies] = (1 - l)(1 - r^k) / (1 - r)
    retry, receiver drops  P(delivered) = 1 - l^k      E[copies] = 1 - l^k
    repeated report ids

and P(at least two copies) for the plain retry. The run sends N reports under each policy with
seeded losses and records measured values beside the formulas.

Part 2, Little's law. A single worker takes S ticks per item; requests arrive with probability
lambda per tick. The run drives the chapter's WorkQueue on a real SQLite file with a simulated
clock and checks L = lambda W, where L is the mean number of open items read from the database,
lambda the accepted arrival rate and W the mean ticks from admission to finish.

    python book/textbook/experiments/profrod_sovereign_agent_textbook_ch07_work_v1.py \
        [--out receipt.json]
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import runpy
import sqlite3
import statistics
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

LEARNER = Path(__file__).resolve().parents[1] / "learner"


# ---- Part 1: delivery policies ---------------------------------------------------------------


def one_report(
    rng: random.Random, lost_before: float, reply_lost: float, attempts: int, dedupe: bool
) -> int:
    """Copies the service delivers for one report under a policy of up to ``attempts`` sends."""
    delivered = 0
    for _ in range(attempts):
        if rng.random() < lost_before:
            continue  # never reached the service: no reply
        if not (dedupe and delivered):
            delivered += 1
        if rng.random() >= reply_lost:
            break  # the reply arrived: stop
    return delivered


def predicted(lost_before: float, reply_lost: float, attempts: int, dedupe: bool) -> dict:
    lost, p, k = lost_before, reply_lost, attempts
    r = lost + (1 - lost) * p
    if dedupe:
        copies = 1 - lost**k
        at_least_two = 0.0
    else:
        copies = (1 - lost) * (1 - r**k) / (1 - r)
        exactly_one = (1 - p) * (1 - lost**k) + k * p * (1 - lost) * lost ** (k - 1)
        at_least_two = 1 - lost**k - exactly_one
    return {"delivered": 1 - lost**k, "copies": copies, "at_least_two": at_least_two}


def delivery(n: int, seed: int, lost_before: float, reply_lost: float) -> list[dict]:
    rows = []
    for name, attempts, dedupe in [
        ("never resend", 1, False),
        ("retry up to 3", 3, False),
        ("retry up to 3, receiver drops repeats", 3, True),
    ]:
        rng = random.Random(seed)
        copies = [one_report(rng, lost_before, reply_lost, attempts, dedupe) for _ in range(n)]
        rows.append(
            {
                "policy": name,
                "reports": n,
                "delivered": sum(1 for c in copies if c) / n,
                "copies": sum(copies) / n,
                "at_least_two": sum(1 for c in copies if c >= 2) / n,
                "predicted": predicted(lost_before, reply_lost, attempts, dedupe),
            }
        )
    return rows


# ---- Part 2: Little's law on the real queue ---------------------------------------------------


def little(ticks: int, seed: int, arrival: float, service: int, capacity: int) -> dict:
    work = runpy.run_path(str(LEARNER / "profrod_sovereign_agent_ch07_work_queue_learner.py"))
    rng = random.Random(seed)
    with tempfile.TemporaryDirectory() as folder:
        store = work["StateStore"](Path(folder) / "shop.sqlite3")
        # This part measures queueing, not durability: skip the flush on every commit.
        store.connection.execute("PRAGMA synchronous = OFF")
        store.initialize()
        queue = work["WorkQueue"](store, capacity=capacity)
        admitted_at, times, open_counts = {}, [], []
        accepted = refused = 0
        current, current_source, done_at = None, None, 0
        for tick in range(ticks):
            if rng.random() < arrival:
                source = f"s{tick}"
                outcome = queue.admit(source, "lucy", "Prepare the opening brief")
                if outcome == "accepted":
                    accepted += 1
                    admitted_at[source] = tick
                else:
                    refused += 1
            if current is not None and tick >= done_at:
                queue.finish(current, "brief")
                times.append(tick - admitted_at[current_source])
                current = None
            if current is None:
                current = queue.claim("w1")
                if current is not None:
                    (current_source,) = store.connection.execute(
                        "SELECT source_id FROM work WHERE work_id = ?", (current.work_id,)
                    ).fetchone()
                    done_at = tick + service
            (count,) = store.connection.execute(
                "SELECT COUNT(*) FROM work WHERE state IN ('pending', 'running')"
            ).fetchone()
            open_counts.append(count)
        store.close()
    lam = accepted / ticks
    mean_l = statistics.fmean(open_counts)
    mean_w = statistics.fmean(times)
    rho = arrival * service
    return {
        "ticks": ticks,
        "arrival_per_tick": arrival,
        "service_ticks": service,
        "capacity": capacity,
        "accepted": accepted,
        "refused": refused,
        "lambda_accepted": round(lam, 5),
        "L_measured": round(mean_l, 4),
        "W_measured": round(mean_w, 4),
        "lambda_times_W": round(lam * mean_w, 4),
        "utilization": round(rho, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    record = {
        "experiment": "profrod-sovereign-agent-ch07-work-v1",
        "ranAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "delivery": {
            "lost_before": 0.02,
            "reply_lost": 0.05,
            "rows": delivery(100_000, args.seed, 0.02, 0.05),
        },
        "little": [
            little(4000, args.seed, 0.2, 3, capacity=1000),
            little(4000, args.seed, 0.3, 3, capacity=1000),
            little(4000, args.seed, 0.3, 3, capacity=3),
        ],
    }
    for row in record["delivery"]["rows"]:
        guess = row["predicted"]
        print(
            f"{row['policy']}: delivered {row['delivered']:.4f} (model {guess['delivered']:.4f}), "
            f"copies {row['copies']:.4f} (model {guess['copies']:.4f}), "
            f"2+ copies {row['at_least_two']:.4f} (model {guess['at_least_two']:.4f})"
        )
    for run in record["little"]:
        print(
            f"lambda={run['arrival_per_tick']} S={run['service_ticks']} "
            f"capacity={run['capacity']}: "
            f"L {run['L_measured']} vs lambda*W {run['lambda_times_W']} "
            f"(W {run['W_measured']}, accepted {run['accepted']}, refused {run['refused']})"
        )
    if args.out:
        args.out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"receipt: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
