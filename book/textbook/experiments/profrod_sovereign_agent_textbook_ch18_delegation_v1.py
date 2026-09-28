# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 18 experiment: do parallel subagents pay on a local model, and how do their errors add?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch18_delegation_v1.py \
      --out ch18-delegation-receipt.json [--model qwen2.5:0.5b]

A real model (served by Ollama on localhost) answers Chapter 5's twelve direct questions about
Lucy's forty notes, each question as one "subagent" task with every note in context.
  - Parallelism: four subagent tasks run one after another, then all four at once, three times
    each; the receipt compares wall times with Amdahl's law.
  - Composition: every question is answered ten times at temperature 0.7. A composed task needs
    four subagents right at once; the receipt compares the measured joint success with the product
    of the four accuracies.
  - Voting: for each question, three samples vote; the receipt compares how often at least two of
    three are right with the independent-errors prediction.
Answers are graded by Chapter 5's whole-word grader.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import platform
import runpy
import statistics
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
DELEGATE = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch18_delegation_learner.py")
)
MEMORY = runpy.run_path(
    str(ROOT / "book/textbook/experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py")
)
MODEL = "qwen2.5:0.5b"  # replaced by --model; the small model makes errors worth composing
NOTES = "\n".join(f"- {note}" for note in MEMORY["NOTES"])
QUESTIONS = MEMORY["QUESTIONS"][:12]
GROUPS = [range(0, 4), range(4, 8), range(8, 12)]


def ask(question, temperature, seed):
    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Answer the question from the shop notes, in one short sentence.",
            },
            {"role": "user", "content": f"Shop notes:\n{NOTES}\n\nQuestion: {question}"},
        ],
        "stream": False,
        "options": {"temperature": temperature, "seed": seed, "num_predict": 60, "num_ctx": 4096},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def parallelism():
    tasks = [q for q, _, _ in QUESTIONS[:4]]
    ask(tasks[0], 0, 1)  # load the model before timing
    rows = []
    for repeat in range(3):
        started = time.perf_counter()
        for i, question in enumerate(tasks):
            ask(question, 0, 100 * repeat + i)
        sequential = time.perf_counter() - started
        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            seeds = [200 + 100 * repeat + i for i in range(len(tasks))]
            list(pool.map(lambda question, seed: ask(question, 0, seed), tasks, seeds))
        parallel = time.perf_counter() - started
        rows.append(
            {"sequential_seconds": round(sequential, 3), "parallel_seconds": round(parallel, 3)}
        )
    speedup = statistics.median(r["sequential_seconds"] / r["parallel_seconds"] for r in rows)
    # Solve Amdahl for the parallel fraction that explains the measured speedup with 4 workers.
    fraction = (1 - 1 / speedup) / (1 - 1 / 4)
    return {
        "subagents": 4,
        "rows": rows,
        "median_speedup": round(speedup, 3),
        "implied_parallel_fraction": round(fraction, 3),
        "amdahl_if_fully_parallel": DELEGATE["amdahl_speedup"](1.0, 4),
    }


def sampling(runs):
    correct = []
    for index, (question, _, expected) in enumerate(QUESTIONS):
        row = []
        for sample in range(10):
            answer = ask(question, 0.7, 1 + sample)["message"]["content"]
            ok = MEMORY["graded"](answer, expected)
            row.append(ok)
            runs.append({"question": index, "sample": sample, "answer": answer, "correct": ok})
        correct.append(row)
    accuracy = [sum(r) / len(r) for r in correct]
    composed = []
    for group in GROUPS:
        predicted = DELEGATE["all_correct"]([accuracy[i] for i in group])
        measured = sum(all(correct[i][s] for i in group) for s in range(10)) / 10
        composed.append(
            {
                "questions": list(group),
                "predicted_product": round(predicted, 3),
                "measured": measured,
            }
        )
    votes = []
    for index, row in enumerate(correct):
        triples = [row[0:3], row[3:6], row[6:9]]
        measured = sum(sum(t) >= 2 for t in triples) / 3
        votes.append(
            {
                "question": index,
                "single_accuracy": round(accuracy[index], 2),
                "predicted_majority_of_3": round(
                    DELEGATE["majority_accuracy"](accuracy[index], 3), 3
                ),
                "measured_majority_of_3": round(measured, 3),
            }
        )
    return {"accuracy": [round(a, 2) for a in accuracy], "composed": composed, "votes": votes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="qwen2.5:0.5b")
    args = parser.parse_args()
    global MODEL
    MODEL = args.model
    started = time.time()
    runs = []
    receipt = {
        "schema": 1,
        "experiment": "ch18-delegation-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "model": MODEL,
        "parallelism": parallelism(),
        "sampling": sampling(runs),
        "tokens_example": DELEGATE["delegation_tokens"](600, [30, 30, 30, 30], 200),
    }
    receipt["seconds"] = round(time.time() - started, 1)
    receipt["runs"] = runs
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump({k: v for k, v in receipt.items() if k != "runs"}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
