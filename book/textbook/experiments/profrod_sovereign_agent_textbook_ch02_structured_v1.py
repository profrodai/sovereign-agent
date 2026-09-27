# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 2 experiment: does a schema make a model's structured output correct, or only valid?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch02_structured_v1.py \
      --out ch02-structured-receipt.json [--live]

Offline, it enumerates a toy model exactly and compares token-level masking with conditioning on
validity. With --live, a real model (served by Ollama on localhost) turns twelve of Lucy's order
requests into {"sku", "quantity"}, five samples each at temperature 0.7, twice: asked for JSON in
the prompt only, and with the JSON schema enforced by the server's constrained decoding. Each
answer is scored at three levels: it parses as JSON; it satisfies the schema; it is the right order.
"""

from __future__ import annotations

import argparse
import json
import platform
import runpy
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
DECODE = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch02_constrained_decoding_learner.py")
)
END = DECODE["END"]

# The toy model: "a" is likely first, but almost never followed by a valid "y".
TOY = {
    (): {"a": 0.9, "b": 0.1},
    ("a",): {"x": 0.99, "y": 0.01},
    ("b",): {"y": 1.0},
    ("a", "x"): {END: 1.0},
    ("a", "y"): {END: 1.0},
    ("b", "y"): {END: 1.0},
}
VALID = {("a", "y"), ("b", "y")}

CATALOG = {"V": "vanilla", "S": "strawberry", "C": "chocolate", "M": "mango", "P": "pistachio"}
SCHEMA = {
    "type": "object",
    "properties": {
        "sku": {"type": "string", "enum": sorted(CATALOG)},
        "quantity": {"type": "integer", "minimum": 1},
    },
    "required": ["sku", "quantity"],
    "additionalProperties": False,
}
REQUESTS = [
    ("Order 6 tubs of vanilla.", ("V", 6)),
    ("We need four tubs of strawberry.", ("S", 4)),
    ("Please get 10 chocolate.", ("C", 10)),
    ("Mango: 3 tubs, please.", ("M", 3)),
    ("Half a dozen pistachio.", ("P", 6)),
    ("A dozen vanilla tubs for the weekend.", ("V", 12)),
    ("Strawberry is low, order two.", ("S", 2)),
    ("Could you draft 7 tubs of the chocolate one?", ("C", 7)),
    ("Top up mango by five tubs.", ("M", 5)),
    ("One tub of pistachio for the tasting.", ("P", 1)),
    ("Order vanilla, eight tubs.", ("V", 8)),
    ("Reorder strawberry: we need 9.", ("S", 9)),
]
SYSTEM = (
    "Turn Lucy's request into a draft order. Products and their SKUs: "
    + ", ".join(f"{sku} = {name}" for sku, name in CATALOG.items())
    + '. Reply with only a JSON object with keys "sku" (one of the SKUs) and "quantity" '
    "(a positive integer), and nothing else."
)


def toy_comparison():
    valid = lambda s: s in VALID  # noqa: E731
    viable = lambda s: any(v[: len(s)] == s for v in VALID)  # noqa: E731
    everything = DECODE["sequences"](TOY)
    wanted = DECODE["conditioned"](TOY, valid)
    got = DECODE["masked"](TOY, valid, viable)
    return {
        "p_valid_unconstrained": round(sum(p for s, p in everything.items() if valid(s)), 4),
        "conditioned": {"".join(s): round(p, 4) for s, p in sorted(wanted.items())},
        "masked": {"".join(s): round(p, 4) for s, p in sorted(got.items())},
        "total_variation": round(DECODE["total_variation"](wanted, got), 4),
    }


def chat(model, request, constrained, seed):
    body = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": request}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.7, "seed": seed, "num_predict": 80},
    }
    if constrained:
        body["format"] = SCHEMA
    req = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=120) as response:
        return json.loads(response.read())["message"]["content"]


def score(text, expected):
    try:
        value = json.loads(text)
    except ValueError:
        return {"parses": False, "schema": False, "correct": False}
    schema = (
        isinstance(value, dict)
        and set(value) == {"sku", "quantity"}
        and value.get("sku") in CATALOG
        and type(value.get("quantity")) is int
        and value["quantity"] >= 1
    )
    correct = schema and (value["sku"], value["quantity"]) == expected
    return {"parses": True, "schema": schema, "correct": correct}


def live(runs, samples=5):
    table = []
    for model in ("qwen2.5:0.5b", "qwen2.5:1.5b"):
        for constrained in (False, True):
            counts = {"parses": 0, "schema": 0, "correct": 0}
            for request, expected in REQUESTS:
                for sample in range(samples):
                    text = chat(model, request, constrained, seed=1 + sample)
                    result = score(text, expected)
                    for key in counts:
                        counts[key] += result[key]
                    runs.append(
                        {
                            "model": model,
                            "constrained": constrained,
                            "request": request,
                            "sample": sample,
                            "answer": text,
                            **result,
                        }
                    )
            n = len(REQUESTS) * samples
            row = {"model": model, "constrained": constrained, "answers": n} | {
                key: f"{value}/{n}" for key, value in counts.items()
            }
            table.append(row)
            print(json.dumps(row), flush=True)
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    started = time.time()
    receipt = {
        "schema": 1,
        "experiment": "ch02-structured-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "toy": toy_comparison(),
    }
    if args.live:
        runs = []
        receipt["structured_output"] = live(runs)
        receipt["runs"] = runs
    receipt["seconds"] = round(time.time() - started, 1)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump({k: v for k, v in receipt.items() if k != "runs"}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
