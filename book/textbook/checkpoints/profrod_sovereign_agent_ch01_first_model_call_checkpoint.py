# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 1: what a model call computes, then one explicit request, with an offline fixture.

The fundamentals come first: the learner file's tokenizer, softmax, temperature, sampler and
cross-entropy are checked against properties derived in the chapter, including a negative control
that a broken sampler must fail.
"""

import argparse
import copy
import hashlib
import json
import math
import random
import runpy
from pathlib import Path
from urllib.request import HTTPRedirectHandler, Request, build_opener

SHOP = {
    "customer": "Lucy",
    "currency": "USD",
    "products": [
        {"sku": "SKU-VANILLA", "name": "Vanilla", "on_hand": 2, "reorder_point": 8},
        {"sku": "SKU-CHOCOLATE", "name": "Chocolate", "on_hand": 12, "reorder_point": 6},
        {"sku": "SKU-STRAWBERRY", "name": "Strawberry", "on_hand": 1, "reorder_point": 5},
    ],
}


def messages(shop):
    return [
        {
            "role": "system",
            "content": "Write a short morning stock brief for Lucy. "
            "Use only the supplied stock facts. Name products below their reorder points. "
            "Do not purchase anything or claim that an order exists.",
        },
        {"role": "user", "content": json.dumps(shop, sort_keys=True)},
    ]


def payload(shop, model="qwen3"):
    return {
        "model": model,
        "messages": messages(shop),
        "stream": False,
        "temperature": 0,
        "max_tokens": 256,
        "reasoning_effort": "none",
    }


def read_brief(document):
    if not isinstance(document, dict):
        raise ValueError("completion envelope must be an object")
    choices = document.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("one completion required")
    choice = choices[0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        raise ValueError("completion did not finish normally")
    message = choice.get("message", {})
    if not isinstance(message, dict) or message.get("tool_calls") or message.get("refusal"):
        raise ValueError("a plain completed brief was expected")
    if message.get("role") != "assistant":
        raise ValueError("assistant completion role required")
    text = message.get("content")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("nonempty brief required")
    return text


def stock_facts(shop):
    return [
        (p["sku"], p["on_hand"], max(0, p["reorder_point"] - p["on_hand"]))
        for p in sorted(shop["products"], key=lambda p: p["sku"])
    ]


def check_brief(text, shop):
    lower = text.lower()
    problems = [
        "omits low product " + p["name"]
        for p in shop["products"]
        if p["on_hand"] < p["reorder_point"] and p["name"].lower() not in lower
    ]
    for phrase in ("placed the supplier order", "placed an order", "purchased"):
        if phrase in lower:
            problems.append("possible unsupported action: " + phrase)
    return problems


def snapshot_id(shop):
    return hashlib.sha256(json.dumps(shop, sort_keys=True).encode()).hexdigest()


def build(shop):
    snapshot = copy.deepcopy(shop)
    return {"snapshot": snapshot_id(snapshot), "body": payload(snapshot)}


def review_brief(built, document, current_shop):
    if built["snapshot"] != snapshot_id(current_shop):
        raise ValueError("shop changed since the request was built; request a fresh brief")
    text = read_brief(document)
    return {
        "status": "NEEDS_FACTUAL_REVIEW",
        "draft": text,
        "flags": check_brief(text, current_shop),
        "stock_facts": stock_facts(current_shop),
    }


class RefuseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused; use the configured endpoint directly")


def live_call(body):
    # A socket-operation timeout, not a total wall-clock guarantee. Chapter 3
    # introduces the killable transport used by the cumulative agent.
    request = Request(
        "http://localhost:11434/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with build_opener(RefuseRedirects()).open(request, timeout=30) as response:
        raw = response.read(65_537)
    if len(raw) > 65_536:
        raise ValueError("response exceeded the chapter's byte limit")
    return json.loads(raw)


OFFLINE_RESPONSE = {
    "choices": [
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "Vanilla has 2 tubs and strawberry has 1: "
                "both are below their reorder points. "
                "Chocolate has 12 tubs, above its reorder point. No orders have been placed.",
            },
        }
    ]
}


def fundamentals():
    learner = runpy.run_path(
        str(
            Path(__file__).resolve().parents[1]
            / "learner"
            / "profrod_sovereign_agent_ch01_model_call_learner.py"
        )
    )
    notes = learner["SHOP_NOTES"]
    merges = learner["train_bpe"](notes, 100)
    for text in (notes, learner["HELD_OUT_NOTES"], " pistachio", "Crème brûlée, 🍦"):
        assert learner["decode"](learner["encode"](text, merges)) == text
    print("ok   any text round-trips through the tokenizer, accented and emoji included")

    softmax = learner["softmax"]
    shifted = softmax([z + 100 for z in (2.0, 1.0, 0.0)])
    assert all(math.isclose(a, b) for a, b in zip(shifted, softmax([2.0, 1.0, 0.0]), strict=True))
    assert math.isclose(sum(softmax([1000.0, 999.0, 998.0])), 1.0)
    print("ok   softmax ignores a shift and stays finite at large logits")

    model = learner["train_bigram"](learner["encode"](notes, merges), merges)
    logits = model.logits(b".")
    entropy = learner["entropy_bits"]
    for t in (0.75, 1.0, 1.5):
        p = softmax(logits, t)
        mean = sum(pi * z for pi, z in zip(p, logits, strict=True))
        variance = sum(pi * (z - mean) ** 2 for pi, z in zip(p, logits, strict=True))
        numeric = (entropy(softmax(logits, t + 1e-5)) - entropy(softmax(logits, t - 1e-5))) / 2e-5
        assert math.isclose(variance / t**3 / math.log(2), numeric, rel_tol=1e-4)
    print("ok   dH/dT = Var(z) / T^3 matches a numerical derivative")

    def chi_square_z(sampler):
        p = softmax(model.logits(b" of"))
        rng, counts, draws = random.Random(3), [0] * len(p), 20_000
        for _ in range(draws):
            counts[sampler(p, rng)] += 1
        chi = sum((c - draws * pi) ** 2 / (draws * pi) for pi, c in zip(p, counts, strict=True))
        return (chi - (len(p) - 1)) / math.sqrt(2 * (len(p) - 1))

    assert abs(chi_square_z(learner["sample"])) < 3
    print("ok   the sampler's frequencies pass a chi-square test")

    def off_by_one(p, rng):
        return min(len(p) - 1, learner["sample"](p, rng) + 1)

    assert chi_square_z(off_by_one) > 100
    print("ok   negative control: an off-by-one sampler fails the same test")

    held_out = learner["encode"](learner["HELD_OUT_NOTES"], merges)
    assert 1 < learner["perplexity"](model, held_out) < 10
    print(
        "ok   held-out perplexity is finite and small, because smoothing keeps every token possible"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen3")
    args = parser.parse_args()
    fundamentals()
    built = build(SHOP)
    body = built["body"]
    body["model"] = args.model
    try:
        document = live_call(body) if args.live else OFFLINE_RESPONSE
        review = review_brief(built, document, SHOP)
    except OSError, ValueError:
        parser.exit(
            1,
            "Model call failed. Start Ollama and pull the selected model; "
            "check the Chapter 1 setup, then retry. No order was sent.\n",
        )
    print("LIVE MODEL RESPONSE" if args.live else "OFFLINE RESPONSE FIXTURE")
    print(review["draft"])
    if review["flags"]:
        print("Warning flags; factual review required:", review["flags"])


if __name__ == "__main__":
    main()
