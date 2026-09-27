# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 9 experiment: where does the wait for a chat reply go?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch09_latency_v1.py \
      --out ch09-latency-receipt.json

Real models served by Ollama on localhost; Ollama reports how many prompt tokens it evaluated
and how long prefill and decode took.
  - Prefill: prompts of one to eight copies of the shop notes, each starting with a fresh marker
    so no cached prefix can be reused, three times each, on qwen2.5:0.5b and qwen2.5:1.5b. The
    receipt fits a line through prefill time per token against prompt tokens, which gives
    prefill time = b * n + c * n^2.
  - Decode: the time per generated token for each model.
  - Streaming: the time until the first piece of a streamed reply arrives, against the time for
    the whole reply.
  - Prefix cache: an eight-turn conversation in which each turn adds Lucy's message and the reply,
    once with an unchanged history and once with a marker at the start that changes every turn.
    The receipt records the prompt tokens Ollama evaluated each turn, and the time to reply.
"""

from __future__ import annotations

import argparse
import json
import platform
import runpy
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
LATENCY = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch09_latency_learner.py")
)
MEMORY = runpy.run_path(
    str(ROOT / "book/textbook/experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py")
)
NOTES = "\n".join(f"- {note}" for note in MEMORY["NOTES"])
QUESTIONS = [q for q, _, _ in MEMORY["QUESTIONS"][:8]]


def call(body, stream=False):
    body = {"stream": stream, **body}
    body.setdefault("options", {}).setdefault("num_ctx", 8192)
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urlopen(request, timeout=300) as response:
        if not stream:
            data = json.loads(response.read())
            data["wall_seconds"] = time.perf_counter() - started
            return data
        first = None
        for line in response:
            piece = json.loads(line)
            if first is None and piece.get("message", {}).get("content"):
                first = time.perf_counter() - started
            if piece.get("done"):
                piece["first_piece_seconds"] = first
                piece["wall_seconds"] = time.perf_counter() - started
                return piece
    raise RuntimeError("stream ended without a final message")


def prefill(model, repeats):
    rows = []
    for copies in (1, 2, 4, 6, 8):
        for repeat in range(repeats):
            marker = uuid.uuid4().hex  # a fresh start, so nothing cached can be reused
            prompt = f"[{marker}]\nShop notes:\n" + "\n".join([NOTES] * copies)
            data = call(
                {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt + "\nReply with OK."}],
                    "options": {"temperature": 0, "num_predict": 1},
                }
            )
            rows.append(
                {
                    "copies": copies,
                    "repeat": repeat,
                    "prompt_tokens": data["prompt_eval_count"],
                    "prefill_seconds": round(data["prompt_eval_duration"] / 1e9, 4),
                }
            )
    # time / n = b + c * n, so a line through the per-token times gives b and c
    per_token, squared = LATENCY["fit_line"](
        [r["prompt_tokens"] for r in rows],
        [r["prefill_seconds"] / r["prompt_tokens"] for r in rows],
    )
    shortest, longest = (
        min(rows, key=lambda r: r["prompt_tokens"]),
        max(rows, key=lambda r: r["prompt_tokens"]),
    )
    return {
        "rows": rows,
        "seconds_per_token": round(per_token, 9),
        "seconds_per_token_squared": round(squared, 12),
        "tokens_per_second_shortest": round(
            shortest["prompt_tokens"] / shortest["prefill_seconds"]
        ),
        "tokens_per_second_longest": round(longest["prompt_tokens"] / longest["prefill_seconds"]),
    }


def decode(model):
    data = call(
        {
            "model": model,
            "messages": [{"role": "user", "content": "Describe Lucy's ice cream shop in detail."}],
            "options": {"temperature": 0, "num_predict": 200},
        }
    )
    seconds = data["eval_duration"] / 1e9
    return {
        "output_tokens": data["eval_count"],
        "seconds_per_output_token": round(seconds / data["eval_count"], 5),
    }


def streaming(model, repeats):
    rows = []
    for repeat in range(repeats):
        data = call(
            {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Shop notes:\n{NOTES}\n\n{QUESTIONS[repeat]} "
                        "Explain your answer in a short paragraph.",
                    }
                ],
                "options": {"temperature": 0.7, "seed": 1 + repeat, "num_predict": 150},
            },
            stream=True,
        )
        rows.append(
            {
                "first_piece_seconds": round(data["first_piece_seconds"], 3),
                "whole_reply_seconds": round(data["wall_seconds"], 3),
                "output_tokens": data["eval_count"],
            }
        )
    return rows


def conversation(model, cached):
    messages, rows = [], []
    for turn, question in enumerate(QUESTIONS):
        system = "You are Lucy's shop assistant. Answer from the shop notes.\n" + NOTES
        if not cached:
            system = f"[{uuid.uuid4().hex}]\n" + system  # changes every turn: no reusable prefix
        messages.append({"role": "user", "content": question})
        data = call(
            {
                "model": model,
                "messages": [{"role": "system", "content": system}, *messages],
                "options": {"temperature": 0, "num_predict": 60},
            }
        )
        messages.append({"role": "assistant", "content": data["message"]["content"]})
        rows.append(
            {
                "turn": turn + 1,
                "prompt_tokens_evaluated": data["prompt_eval_count"],
                "prefill_seconds": round(data["prompt_eval_duration"] / 1e9, 4),
                "reply_seconds": round(data["wall_seconds"], 3),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    started = time.time()
    models = {}
    for model in ("qwen2.5:0.5b", "qwen2.5:1.5b"):
        call({"model": model, "messages": [{"role": "user", "content": "Hi"}]})  # load it
        models[model] = {
            "prefill": prefill(model, args.repeats),
            "decode": decode(model),
            "streaming": streaming(model, 5),
        }
    chat = "qwen2.5:0.5b"
    call({"model": chat, "messages": [{"role": "user", "content": "Hi"}]})
    receipt = {
        "schema": 1,
        "experiment": "ch09-latency-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "models": models,
        "conversation_model": chat,
        "conversation": {
            "cached": conversation(chat, cached=True),
            "uncached": conversation(chat, cached=False),
        },
        "seconds": None,
    }
    receipt["seconds"] = round(time.time() - started, 1)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    summary = {
        model: {
            "prefill": {k: v for k, v in m["prefill"].items() if k != "rows"},
            "decode": m["decode"],
            "streaming": m["streaming"],
        }
        for model, m in models.items()
    }
    print(json.dumps({"models": summary, "conversation": receipt["conversation"]}, indent=2))


if __name__ == "__main__":
    main()
