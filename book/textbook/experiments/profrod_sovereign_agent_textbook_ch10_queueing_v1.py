# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 10 experiment: how long do stock events wait for one worker?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch10_queueing_v1.py \
      --out ch10-queueing-receipt.json

Each job is one real model call (Ollama on localhost): a short note to Lucy about a stock event.
Two workloads: "notes", where every job is a short note, and "mixed", where one job in five is
a long weekly report instead.
  - Service: for each workload, a pilot runs 60 jobs one after another and records their service
    times, giving E[S] and E[S^2].
  - Queueing: jobs arrive at random (a Poisson process) at rates that would keep one worker busy
    50% and 80% of the time, and one worker serves them in order. The receipt compares the mean
    wait before service with Pollaczek-Khinchine and with the exponential special case, and checks
    Little's law on the same run.
"""

from __future__ import annotations

import argparse
import json
import platform
import queue
import random
import runpy
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
QUEUE = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch10_queueing_learner.py")
)
MODEL = "qwen2.5:0.5b"
FLAVORS = ["vanilla", "chocolate", "pistachio", "strawberry", "mint", "coffee", "mango", "lemon"]


def job(seed, report_share):
    """One job: a short note to Lucy about a stock event or, with probability `report_share`, a
    long weekly report. Returns its service time."""
    chooser = random.Random(seed)
    event = f"{chooser.choice(FLAVORS).capitalize()} fell to {chooser.randint(0, 3)} tubs."
    if chooser.random() < report_share:
        task, tokens = "Write Lucy a detailed weekly stock report that covers this event.", 600
    else:
        task, tokens = "Write Lucy a short note about it.", 120
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are Lucy's shop assistant."},
            {"role": "user", "content": f"Stock event: {event} {task}"},
        ],
        "stream": False,
        "options": {"temperature": 0.7, "seed": seed, "num_predict": tokens},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urlopen(request, timeout=120) as response:
        json.loads(response.read())
    return time.perf_counter() - started


def run_queue(rate, count, seed, report_share):
    """Poisson arrivals at `rate` into a FIFO queue served by one worker. Returns per-job times."""
    offsets = QUEUE["arrivals"](rate, count, seed)
    pending = queue.Queue()
    records = []
    start = time.perf_counter()

    def produce():
        for n, offset in enumerate(offsets):
            time.sleep(max(0.0, start + offset - time.perf_counter()))
            pending.put((n, time.perf_counter() - start))

    def serve():
        for _ in range(count):
            n, arrived = pending.get()
            began = time.perf_counter() - start
            seconds = job(10_000 * seed + n, report_share)
            records.append(
                {
                    "job": n,
                    "arrived": round(arrived, 4),
                    "started": round(began, 4),
                    "finished": round(began + seconds, 4),
                }
            )

    producer, worker = threading.Thread(target=produce), threading.Thread(target=serve)
    producer.start()
    worker.start()
    producer.join()
    worker.join()
    return records


def number_in_system(records):
    """Time-average number of jobs waiting or in service, integrated over the run."""
    events = sorted([(r["arrived"], 1) for r in records] + [(r["finished"], -1) for r in records])
    area, count, last = 0.0, 0, events[0][0]
    for moment, change in events:
        area += count * (moment - last)
        count, last = count + change, moment
    return area / (events[-1][0] - events[0][0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pilot", type=int, default=60)
    parser.add_argument("--jobs", type=int, default=400)
    args = parser.parse_args()
    started = time.time()
    job(0, 0)  # load the model before timing
    rows, runs, pilots = [], [], {}
    for w, (workload, share) in enumerate((("notes", 0.0), ("mixed", 0.2))):
        pilot = [round(job(1000 * w + n, share), 4) for n in range(args.pilot)]
        mean, second = QUEUE["moments"](pilot)
        pilots[workload] = {
            "report_share": share,
            "service_seconds": pilot,
            "mean_service": round(mean, 4),
            "second_moment": round(second, 4),
            "squared_cv": round(second / mean**2 - 1, 3),
        }
        for index, rho in enumerate((0.5, 0.8)):
            rate = rho / mean
            seed = 9 + 10 * w + index
            records = run_queue(rate, args.jobs, seed, share)
            waits = [r["started"] - r["arrived"] for r in records]
            stays = [r["finished"] - r["arrived"] for r in records]
            served = [r["finished"] - r["started"] for r in records]
            run_mean, run_second = QUEUE["moments"](served)
            span = records[-1]["arrived"] - records[0]["arrived"]
            realized_rate = (len(records) - 1) / span
            realized_rho = realized_rate * run_mean  # arrivals and service as they happened
            rows.append(
                {
                    "workload": workload,
                    "target_utilization": rho,
                    "arrival_rate_per_second": round(rate, 4),
                    "jobs": len(records),
                    "measured_utilization": round(sum(served) / records[-1]["finished"], 3),
                    "measured_mean_wait": round(sum(waits) / len(waits), 3),
                    "pk_wait_from_pilot": round(QUEUE["pk_wait"](rate, mean, second), 3),
                    "utilization_from_this_run": round(realized_rho, 3),
                    "pk_wait_from_this_run": round(
                        QUEUE["pk_wait"](realized_rate, run_mean, run_second), 3
                    )
                    if realized_rho < 1
                    else None,  # the queue was unstable over this run: no steady state
                    "exponential_wait_from_pilot": round(QUEUE["exponential_wait"](rate, mean), 3),
                    "littles_law_number": round(number_in_system(records), 3),
                    "littles_law_rate_times_stay": round(
                        realized_rate * sum(stays) / len(stays), 3
                    ),
                    "longest_wait": round(max(waits), 3),
                }
            )
            runs.append({"workload": workload, "target_utilization": rho, "records": records})
            progress = {"pilots": pilots, "rows": rows, "runs": runs}
            args.out.with_suffix(".partial.json").write_text(json.dumps(progress) + "\n")
    receipt = {
        "schema": 1,
        "experiment": "ch10-queueing-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "model": MODEL,
        "pilots": pilots,
        "rows": rows,
        "seconds": round(time.time() - started, 1),
        "runs": runs,
    }
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in receipt.items() if k not in ("runs", "pilots")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
