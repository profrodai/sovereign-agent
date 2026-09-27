# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 1 experiment: test the chapter's derivations against measurement, and record a receipt.

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch01_model_v1.py \
      --out ch01-model-receipt.json [--live --model qwen3:0.6b]

Offline, it measures the learner file's own model:
  1. tokenization: tokens per character and bits per character as merges grow;
  2. smoothing: held-out bits per character across add-alpha values;
  3. temperature: entropy H(T) against the derived dH/dT = Var(z) / T^3;
  4. sampling: empirical frequencies against their binomial standard errors.
With --live, it asks a real model (an Ollama server on localhost) for log-probabilities, and
measures the same quantities there: the probability of its own answer, per-token entropy, and
how many distinct answers sampling produces at each temperature.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import runpy
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

LEARNER = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "learner"
        / "profrod_sovereign_agent_ch01_model_call_learner.py"
    )
)
NOTES, HELD_OUT = LEARNER["SHOP_NOTES"], LEARNER["HELD_OUT_NOTES"]
train_bpe, encode, train_bigram = LEARNER["train_bpe"], LEARNER["encode"], LEARNER["train_bigram"]
softmax, sample, entropy_bits = LEARNER["softmax"], LEARNER["sample"], LEARNER["entropy_bits"]
cross_entropy_bits = LEARNER["cross_entropy_bits"]


def bits_per_character(model, text, merges):
    tokens = encode(text, merges)
    return cross_entropy_bits(model, tokens) * (len(tokens) - 1) / len(text)


def tokenization():
    rows = []
    for merges_wanted in (0, 25, 50, 100, 200):
        merges = train_bpe(NOTES, merges_wanted)
        tokens = encode(NOTES, merges)
        model = train_bigram(tokens, merges, alpha=0.001)
        rows.append(
            {
                "merges": len(merges),
                "tokens": len(tokens),
                "characters_per_token": round(len(NOTES) / len(tokens), 3),
                "train_bits_per_token": round(cross_entropy_bits(model, tokens), 3),
                "train_bits_per_character": round(bits_per_character(model, NOTES, merges), 3),
                "held_out_bits_per_character": round(
                    bits_per_character(model, HELD_OUT, merges), 3
                ),
            }
        )
    return rows


def smoothing(merges):
    tokens = encode(NOTES, merges)
    rows = []
    for alpha in (1.0, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001, 0.0001):
        model = train_bigram(tokens, merges, alpha=alpha)
        rows.append(
            {
                "alpha": alpha,
                "train_bits_per_character": round(bits_per_character(model, NOTES, merges), 3),
                "held_out_bits_per_character": round(
                    bits_per_character(model, HELD_OUT, merges), 3
                ),
            }
        )
    return rows


def temperature(model, context):
    logits = model.logits(context)
    rows = []
    for t in (0.25, 0.5, 1.0, 1.5, 2.0):
        p = softmax(logits, t)
        mean = sum(pi * z for pi, z in zip(p, logits, strict=True))
        variance = sum(pi * (z - mean) ** 2 for pi, z in zip(p, logits, strict=True))
        derived = variance / t**3 / math.log(2)  # dH/dT in bits per unit temperature
        h = 1e-5
        numeric = (entropy_bits(softmax(logits, t + h)) - entropy_bits(softmax(logits, t - h))) / (
            2 * h
        )
        rows.append(
            {
                "temperature": t,
                "entropy_bits": round(entropy_bits(p), 4),
                "dH_dT_derived": round(derived, 4),
                "dH_dT_finite_difference": round(numeric, 4),
                "top_token_probability": round(max(p), 4),
            }
        )
    return rows


def busiest_context(model):
    """The token with the most observed successors: the context the model knows best."""
    return max(model.counts, key=lambda token: (sum(model.counts[token].values()), token))


def sampling(model, context, draws=20_000, seed=7):
    p = softmax(model.logits(context))
    rng = random.Random(seed)
    counts = [0] * len(p)
    for _ in range(draws):
        counts[sample(p, rng)] += 1
    worst = 0.0
    for pi, count in zip(p, counts, strict=True):
        standard_error = math.sqrt(pi * (1 - pi) / draws)
        if standard_error:
            worst = max(worst, abs(count / draws - pi) / standard_error)
    # Pearson's chi-square over all tokens: with k categories it has k - 1 degrees of freedom,
    # mean k - 1 and variance 2(k - 1), so it tests all tokens at once without cherry-picking.
    chi_square = sum((c - draws * pi) ** 2 / (draws * pi) for pi, c in zip(p, counts, strict=True))
    freedom = len(p) - 1
    top = sorted(range(len(p)), key=lambda i: -p[i])[:5]
    return {
        "draws": draws,
        "largest_deviation_in_standard_errors": round(worst, 2),
        "tokens": len(p),
        "chi_square": round(chi_square, 1),
        "degrees_of_freedom": freedom,
        "chi_square_z": round((chi_square - freedom) / math.sqrt(2 * freedom), 2),
        "top_tokens": [
            {
                "token": model.vocabulary[i].decode("utf-8", "replace"),
                "probability": round(p[i], 4),
                "observed": round(counts[i] / draws, 4),
            }
            for i in top
        ],
    }


def chat(model, messages, **options):
    body = {"model": model, "messages": messages, "stream": False, **options}
    request = Request(
        "http://127.0.0.1:11434/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def live(model):
    question = (
        "Lucy's freezer holds 2 tubs of vanilla (target 8), 11 of chocolate (target 6) and "
        "1 of strawberry (target 5). In one sentence, which flavors should she order?"
    )
    messages = [{"role": "user", "content": question}]
    greedy = chat(model, messages, temperature=0, logprobs=True, top_logprobs=5, max_tokens=60)
    choice = greedy["choices"][0]
    content = choice.get("logprobs", {}).get("content") or []
    log_probability = sum(item["logprob"] for item in content)
    entropies = []
    for item in content:
        tops = [math.exp(t["logprob"]) for t in item.get("top_logprobs", [])]
        rest = max(0.0, 1 - sum(tops))
        entropies.append(-sum(p * math.log2(p) for p in tops + [rest] if p > 0))
    distinct = {}
    for t in (0.0, 0.7, 1.5):
        answers = set()
        for seed in range(10):
            reply = chat(model, messages, temperature=t, seed=seed, max_tokens=60)
            answers.add(reply["choices"][0]["message"]["content"].strip())
        distinct[str(t)] = len(answers)
    return {
        "model": model,
        "greedy_answer": choice["message"]["content"].strip(),
        "answer_tokens": len(content),
        "answer_log_probability_nats": round(log_probability, 3),
        "answer_probability": log_probability and math.exp(log_probability),
        "mean_top5_entropy_bits_per_token": round(sum(entropies) / max(1, len(entropies)), 3),
        "usage": greedy.get("usage"),
        "distinct_answers_in_10_samples": distinct,
        "note": "Entropy is estimated from the top 5 alternatives plus one bucket for the rest, "
        "so it is a lower bound on the true per-token entropy.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen2.5:0.5b")
    args = parser.parse_args()
    merges = train_bpe(NOTES, 100)
    model = train_bigram(encode(NOTES, merges), merges, alpha=0.001)
    receipt = {
        "schema": 1,
        "experiment": "ch01-model-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "tokenization": tokenization(),
        "smoothing_at_100_merges": smoothing(merges),
        "context": busiest_context(model).decode("utf-8"),
        "temperature": temperature(model, busiest_context(model)),
        "sampling": sampling(model, busiest_context(model)),
    }
    if args.live:
        receipt["live"] = live(args.model)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump(receipt, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
