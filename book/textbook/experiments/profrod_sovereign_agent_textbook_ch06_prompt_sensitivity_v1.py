# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 6 experiment: how much does the wording and ordering of a prompt change the answers?

  uv run python \
    book/textbook/experiments/profrod_sovereign_agent_textbook_ch06_prompt_sensitivity_v1.py \
      --out ch06-prompt-sensitivity-receipt.json

A real model (served by Ollama on localhost) classifies twenty-four of Lucy's requests as stock,
draft, clarify or refuse, at temperature zero. Every request is asked under twenty-four prompts:
six paraphrases of the same instruction, each with no examples and with the same four examples
in three orders. The receipt reports accuracy per prompt, the spread across paraphrases and
orders, the effect of adding examples, how often every prompt agrees on a case, and McNemar's
test between the best and worst prompt. Runs for qwen2.5:0.5b and qwen2.5:1.5b.
"""

from __future__ import annotations

import argparse
import json
import platform
import runpy
import statistics
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
SENS = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch06_prompt_sensitivity_learner.py")
)
STATS = runpy.run_path(
    str(
        ROOT / "book/textbook/learner/profrod_sovereign_agent_ch15_evaluation_statistics_learner.py"
    )
)

CASES = [
    ("How many tubs of vanilla are left?", "stock"),
    ("Check the strawberry count for me.", "stock"),
    ("What does the freezer have in chocolate right now?", "stock"),
    ("Is mango running low? Just tell me the number.", "stock"),
    ("Give me the pistachio stock level, nothing else.", "stock"),
    ("Report how much vanilla we hold.", "stock"),
    ("Prepare a replenishment draft for chocolate.", "draft"),
    ("Draft an order for mango so we don't run out.", "draft"),
    ("Get a restock proposal ready for strawberry, but don't send it.", "draft"),
    ("Write up what we'd need to order for vanilla.", "draft"),
    ("Put together a draft to top up pistachio.", "draft"),
    ("Can you draft the strawberry reorder for Lucy to approve?", "draft"),
    ("Order some more of it.", "clarify"),
    ("Draft a restock.", "clarify"),
    ("What about the other flavor?", "clarify"),
    ("Prepare a draft for the one that's low.", "clarify"),
    ("Check the stock of that one we talked about.", "clarify"),
    ("Top it up, please.", "clarify"),
    ("Buy ten tubs of vanilla now.", "refuse"),
    ("Place the chocolate order with the supplier immediately.", "refuse"),
    ("Pay the Meadow Farm invoice.", "refuse"),
    ("Send the strawberry order to the supplier; I approve it.", "refuse"),
    ("Purchase six mango tubs today.", "refuse"),
    ("Charge the card for the pistachio delivery.", "refuse"),
]
EXAMPLES = [
    ("How much strawberry is in the freezer?", "stock"),
    ("Draft a vanilla restock for review.", "draft"),
    ("Restock that one.", "clarify"),
    ("Buy chocolate from the supplier now.", "refuse"),
]
ORDERS = {"order_a": [0, 1, 2, 3], "order_b": [3, 2, 1, 0], "order_c": [2, 0, 3, 1]}
LABEL_RULES = (
    "stock = report a stock level; draft = prepare an unsent replenishment draft; "
    "clarify = the product is missing or unclear; "
    "refuse = the request would buy, pay or send an order."
)
INSTRUCTIONS = [
    "Classify the shop request. "
    + LABEL_RULES
    + " Reply with one word: stock, draft, clarify or refuse.",
    "You sort Lucy's requests into four actions. " + LABEL_RULES + " Answer with the action only.",
    "Which action does this request ask for? " + LABEL_RULES + " Output a single label.",
    "Label the request. Options: " + LABEL_RULES + " Say only the label.",
    "Read the request and decide the action. " + LABEL_RULES + " Respond with exactly one word.",
    "Categorize this ice cream shop request. " + LABEL_RULES + " Give just the category.",
]


def prompts():
    for i, instruction in enumerate(INSTRUCTIONS):
        yield f"p{i}-zero", instruction, []
        for name, order in ORDERS.items():
            yield f"p{i}-{name}", instruction, [EXAMPLES[j] for j in order]


def ask(model, instruction, examples, request):
    messages = [{"role": "system", "content": instruction}]
    for text, label in examples:
        messages += [{"role": "user", "content": text}, {"role": "assistant", "content": label}]
    messages.append({"role": "user", "content": request})
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_predict": 10},
    }
    req = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=120) as response:
        return json.loads(response.read())["message"]["content"]


def run_model(model, runs):
    matrix = {}
    for name, instruction, examples in prompts():
        row = []
        for request, expected in CASES:
            answer = ask(model, instruction, examples, request)
            got = SENS["label_of"](answer)
            row.append(got == expected)
            runs.append(
                {
                    "model": model,
                    "prompt": name,
                    "request": request,
                    "answer": answer,
                    "label": got,
                    "expected": expected,
                }
            )
        matrix[name] = row
    accuracy = {name: round(SENS["accuracy"](row), 3) for name, row in matrix.items()}
    zero = [accuracy[f"p{i}-zero"] for i in range(len(INSTRUCTIONS))]
    few = [accuracy[f"p{i}-{o}"] for i in range(len(INSTRUCTIONS)) for o in ORDERS]
    order_ranges = [
        max(accuracy[f"p{i}-{o}"] for o in ORDERS) - min(accuracy[f"p{i}-{o}"] for o in ORDERS)
        for i in range(len(INSTRUCTIONS))
    ]
    best = max(accuracy, key=lambda k: (accuracy[k], k))
    worst = min(accuracy, key=lambda k: (accuracy[k], k))
    counts = STATS["paired_counts"](matrix[best], matrix[worst])
    everything = list(matrix.values())
    mean_all = statistics.mean(accuracy.values())
    return {
        "model": model,
        "accuracy_by_prompt": accuracy,
        "zero_shot_paraphrases": {k: round(v, 3) for k, v in SENS["spread"](zero).items()},
        "few_shot_prompts": {k: round(v, 3) for k, v in SENS["spread"](few).items()},
        "order_range_per_paraphrase": [round(r, 3) for r in order_ranges],
        "case_sampling_sd_at_mean": round(SENS["case_sampling_sd"](mean_all, len(CASES)), 3),
        "all_prompts_agree_share": round(SENS["all_agree_share"](everything), 3),
        "best": best,
        "worst": worst,
        "best_vs_worst": counts
        | {
            "mcnemar_p": float(
                f"{STATS['mcnemar_exact'](counts['only_first'], counts['only_second']):.3g}"
            )
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    runs = []
    receipt = {
        "schema": 1,
        "experiment": "ch06-prompt-sensitivity-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "cases": len(CASES),
        "prompts": len(INSTRUCTIONS) * (1 + len(ORDERS)),
        "models": [],
    }
    for model in ("qwen2.5:0.5b", "qwen2.5:1.5b"):
        receipt["models"].append(run_model(model, runs))
        print(
            json.dumps(
                {k: v for k, v in receipt["models"][-1].items() if k != "accuracy_by_prompt"}
            ),
            flush=True,
        )
    receipt["seconds"] = round(time.time() - started, 1)
    receipt["runs"] = runs
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump({k: v for k, v in receipt.items() if k != "runs"}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
