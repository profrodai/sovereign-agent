# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 3 experiment: does agent reliability compound over steps the way the chapter derives?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch03_reliability_v1.py \
      --out ch03-reliability-receipt.json [--model qwen2.5:1.5b] [--instances 25]

A real model (served by Ollama on localhost) runs the learner's own bounded loop on a task of n
steps: look up the stock of n listed products with a tool, then report the total. For n in
{1, 2, 4, 8} it measures:
  - per-step success: the share of required lookups the model made correctly;
  - task success: every lookup made and the reported total exactly right;
and fits log(task success) = n log p + log a, where p is per-step reliability and a the
reliability of the final answer step, to test whether success compounds as p ** n.
Then, at n = 4 and temperature 0.8, it retries each failed instance up to four times and compares
success within k attempts with independent retries and with a "hard fraction" model.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import re
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOOP = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch03_agent_loop_learner.py")
)
run_loop, HTTPModel, Limits = LOOP["run_loop"], LOOP["HTTPModel"], LOOP["Limits"]
SKUS = [
    "SKU-VANILLA",
    "SKU-CHOCOLATE",
    "SKU-STRAWBERRY",
    "SKU-MANGO",
    "SKU-PISTACHIO",
    "SKU-LEMON",
    "SKU-COFFEE",
    "SKU-MINT",
    "SKU-CARAMEL",
    "SKU-COCONUT",
    "SKU-BANANA",
    "SKU-CHERRY",
]


class StockTool:
    """A read-only stock tool, and optionally an add tool. Every call is recorded for grading.

    Arguments are validated before use, as Chapter 2 requires: a malformed request is refused
    with an error the model can read, never allowed to crash the loop.
    """

    def __init__(self, stock, arithmetic=False):
        self.stock, self.arithmetic, self.calls = stock, arithmetic, []

    def schemas(self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "stock",
                    "description": "Return how many tubs of one product are in the freezer.",
                    "parameters": {
                        "type": "object",
                        "properties": {"sku": {"type": "string", "description": "Product SKU"}},
                        "required": ["sku"],
                        "additionalProperties": False,
                    },
                },
            }
        ]
        if self.arithmetic:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": "add",
                        "description": "Return the exact sum of a list of integers.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "numbers": {"type": "array", "items": {"type": "integer"}}
                            },
                            "required": ["numbers"],
                            "additionalProperties": False,
                        },
                    },
                }
            )
        return tools

    def invoke(self, call):
        arguments = call.arguments if isinstance(call.arguments, dict) else {}
        if call.name == "add" and self.arithmetic:
            numbers = arguments.get("numbers")
            self.calls.append(("add", None))
            if not isinstance(numbers, list) or not all(type(x) is int for x in numbers):
                return {"error": "numbers must be a list of integers"}
            return {"sum": sum(numbers)}
        sku = arguments.get("sku")
        if not isinstance(sku, str):
            self.calls.append((call.name, None))
            return {"error": "sku must be a string"}
        self.calls.append((call.name, sku))
        if call.name != "stock" or sku not in self.stock:
            return {"error": "unknown tool or product"}
        return {"sku": sku, "tubs": self.stock[sku]}


def transport_at(temperature, seed):
    """Send the learner's request with a chosen temperature and seed."""
    from sovereign_agent.http_transport import request

    def send(url, *, data, headers, timeout):
        payload = json.loads(data)
        payload.update(temperature=temperature, seed=seed)
        payload.pop("reasoning_effort", None)
        return request(url, data=json.dumps(payload).encode(), headers=headers, timeout=timeout)

    return send


def run_task(model, n, instance, temperature=0.0, attempt=0, arithmetic=False):
    rng = random.Random(1000 * n + instance)
    stock = {sku: rng.randint(0, 20) for sku in SKUS}
    wanted = rng.sample(SKUS, n)
    tool = StockTool(stock, arithmetic)
    messages = [
        {
            "role": "system",
            "content": "You help an ice cream shop. Use the stock tool to look up products. "
            "Never guess a stock level."
            + (" Use the add tool for any arithmetic." if arithmetic else ""),
        },
        {
            "role": "user",
            "content": "Look up the stock of each of these products with the stock tool: "
            + ", ".join(wanted)
            + ". Then reply with only the total number of tubs across them, as an integer.",
        },
    ]
    result = run_loop(
        HTTPModel(model=model, request=transport_at(temperature, 7919 * attempt + instance)),
        tool,
        messages,
        limits=Limits(model_calls=n + 3, tool_calls=2 * n + 4, seconds=120),
    )
    looked_up = {sku for name, sku in tool.calls if name == "stock" and sku}
    steps_done = sum(1 for sku in wanted if sku in looked_up)
    numbers = re.findall(r"-?\d+", result.answer or "")
    answer_right = bool(numbers) and int(numbers[-1]) == sum(stock[s] for s in wanted)
    return {
        "n": n,
        "instance": instance,
        "arithmetic_tool": arithmetic,
        "status": result.status,
        "steps_done": steps_done,
        "extra_calls": len(tool.calls) - steps_done,
        "answer_right": answer_right,
        "success": steps_done == n and answer_right,
        "model_calls": result.model_calls,
    }


def wilson(successes, trials, z=1.96):
    """95% Wilson score interval for a binomial proportion (Chapter 15 derives it)."""
    if trials == 0:
        return (0.0, 1.0)
    phat = successes / trials
    centre = (phat + z * z / (2 * trials)) / (1 + z * z / trials)
    half = z * math.sqrt(phat * (1 - phat) / trials + z * z / (4 * trials * trials))
    half /= 1 + z * z / trials
    return (round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3))


def fit_log_linear(points):
    """Least squares of log(s_n) = n log p + log a over the n with s_n > 0."""
    usable = [(n, math.log(s)) for n, s in points if s > 0]
    if len(usable) < 2:
        return None
    mean_n = sum(n for n, _ in usable) / len(usable)
    mean_y = sum(y for _, y in usable) / len(usable)
    slope = sum((n - mean_n) * (y - mean_y) for n, y in usable) / sum(
        (n - mean_n) ** 2 for n, _ in usable
    )
    intercept = mean_y - slope * mean_n
    return {"p": round(math.exp(slope), 4), "a": round(math.exp(intercept), 4)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="qwen2.5:1.5b")
    parser.add_argument("--instances", type=int, default=25)
    args = parser.parse_args()
    started = time.time()

    by_length = []
    runs = []
    for n in (1, 2, 4, 8):
        rows = [run_task(args.model, n, i) for i in range(args.instances)]
        runs.extend(rows)
        successes = sum(r["success"] for r in rows)
        steps = sum(r["steps_done"] for r in rows)
        answers_given_steps = [r["answer_right"] for r in rows if r["steps_done"] == n]
        by_length.append(
            {
                "n": n,
                "task_success": round(successes / len(rows), 3),
                "task_success_95": wilson(successes, len(rows)),
                "per_step_success": round(steps / (n * len(rows)), 3),
                "answer_right_when_all_steps_done": (
                    round(sum(answers_given_steps) / len(answers_given_steps), 3)
                    if answers_given_steps
                    else None
                ),
                "statuses": {
                    s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}
                },
            }
        )
        print(json.dumps(by_length[-1]), flush=True)
    with_add = []
    for n in (4, 8):
        rows = [run_task(args.model, n, i, arithmetic=True) for i in range(args.instances)]
        runs.extend(rows)
        successes = sum(r["success"] for r in rows)
        with_add.append(
            {
                "n": n,
                "task_success": round(successes / len(rows), 3),
                "task_success_95": wilson(successes, len(rows)),
                "per_step_success": round(sum(r["steps_done"] for r in rows) / (n * len(rows)), 3),
            }
        )
        print(json.dumps({"with_add_tool": with_add[-1]}), flush=True)
    fit = fit_log_linear([(row["n"], row["task_success"]) for row in by_length])
    predictions = None
    if fit:
        predictions = [
            {
                "n": row["n"],
                "measured": row["task_success"],
                "fitted_a_p_to_n": round(fit["a"] * fit["p"] ** row["n"], 3),
                "per_step_to_n": round(row["per_step_success"] ** row["n"], 3),
            }
            for row in by_length
        ]

    retries = []
    for i in range(args.instances):
        outcome = []
        for attempt in range(4):
            outcome.append(run_task(args.model, 4, i, temperature=0.8, attempt=attempt)["success"])
            if outcome[-1]:
                break
        retries.append(outcome)
    first_try = sum(o[0] for o in retries) / len(retries)
    within = [sum(any(o[:k]) for o in retries) / len(retries) for k in (1, 2, 3, 4)]
    never = sum(not any(o) for o in retries) / len(retries)
    # Hard-fraction model: tasks that never succeed are hard; the rest succeed with q per attempt,
    # estimated from their first attempts.
    solvable = [o for o in retries if any(o)]
    q_solvable = sum(o[0] for o in solvable) / len(solvable) if solvable else 0.0
    retry_table = [
        {
            "attempts": k,
            "measured": round(within[k - 1], 3),
            "independent_retries": round(LOOP["retry_success"](first_try, k), 3),
            "hard_fraction_model": round(LOOP["retry_success"](q_solvable, k, hard=never), 3),
        }
        for k in (1, 2, 3, 4)
    ]

    receipt = {
        "schema": 1,
        "experiment": "ch03-reliability-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "model": args.model,
        "instances_per_length": args.instances,
        "by_length": by_length,
        "with_add_tool": with_add,
        "fit": fit,
        "predictions": predictions,
        "retries_at_n4_T0.8": {
            "first_attempt_success": round(first_try, 3),
            "never_succeeded_in_4": round(never, 3),
            "q_among_solvable": round(q_solvable, 3),
            "table": retry_table,
        },
        "seconds": round(time.time() - started, 1),
        "runs": runs,
    }
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump({k: v for k, v in receipt.items() if k != "runs"}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
