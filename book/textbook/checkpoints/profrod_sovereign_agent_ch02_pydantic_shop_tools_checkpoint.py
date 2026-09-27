# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 2: typed shop tools over the same in-memory fixture."""

import copy
import json
import math
import random
import runpy
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from sovereign_agent.model_turn import ToolCall
from sovereign_agent.tool_dispatch import Dispatcher, ExecutableTool

SHOP = runpy.run_path(
    str(Path(__file__).with_name("profrod_sovereign_agent_ch01_first_model_call_checkpoint.py"))
)["SHOP"]
PRICES = {"SKU-VANILLA": 250, "SKU-CHOCOLATE": 300, "SKU-STRAWBERRY": 275}


class NoArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProductArguments(NoArguments):
    sku: str = Field(min_length=1, max_length=100)


class DraftArguments(ProductArguments):
    quantity: int = Field(gt=0, le=1000)


def build_tools(shop):
    products = {row["sku"]: copy.deepcopy(row) for row in shop["products"]}
    if len(products) != len(shop["products"]):
        raise ValueError("duplicate product identity")

    def stock(_):
        return [
            {**row, "needed": max(0, row["reorder_point"] - row["on_hand"])}
            for _, row in sorted(products.items())
        ]

    def supplier(args):
        if args.sku not in products:
            raise KeyError("unknown product")
        return {
            "sku": args.sku,
            "supplier": "lucy-local",
            "currency": "USD",
            "unit_cost_cents": PRICES[args.sku],
        }

    def draft(args):
        row = products[args.sku]
        needed = max(0, row["reorder_point"] - row["on_hand"])
        if args.quantity != needed:
            raise ValueError("quantity differs from the replenishment need")
        quote = supplier(ProductArguments(sku=args.sku))
        return {
            **quote,
            "quantity": args.quantity,
            "total_cents": args.quantity * quote["unit_cost_cents"],
            "status": "DRAFT",
        }

    tools = [
        ExecutableTool(
            "list_stock",
            "Read the fixture and deterministic needed quantities.",
            NoArguments,
            stock,
        ),
        ExecutableTool(
            "supplier",
            "Read a product's supplier and unit price in USD cents.",
            ProductArguments,
            supplier,
        ),
        ExecutableTool(
            "draft_order",
            "Calculate a draft with quantity equal to needed. Never purchases.",
            DraftArguments,
            draft,
        ),
    ]
    return Dispatcher(tools, allowed=frozenset(tool.name for tool in tools))


BOOK = Path(__file__).resolve().parents[1]
DECODE = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch02_constrained_decoding_learner.py")
)


def structured():
    """Part A's decoding functions, each checked against an independent computation."""
    assert math.isclose(DECODE["stays_valid"](0.01, 100), 0.99**100)
    logits = [2.0, 1.0, 0.5, -1.0]
    full = DECODE["softmax"](logits)
    kept = DECODE["softmax"](DECODE["mask"](logits, {1, 3}))
    assert kept[0] == kept[2] == 0.0
    assert math.isclose(kept[1], full[1] / (full[1] + full[3]))
    print("ok   masking renormalizes the allowed tokens and zeroes the rest")

    lab = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch02_structured_v1.py")
    )
    toy, valid = lab["TOY"], lab["VALID"]
    rng = random.Random(2)

    def viable(prefix, token):
        if token == lab["END"]:
            return prefix in valid
        return any(v[: len(prefix) + 1] == prefix + (token,) for v in valid)

    def draw(allowed=None):
        prefix = ()
        while True:
            options = [
                (t, p) for t, p in toy[prefix].items() if allowed is None or allowed(prefix, t)
            ]
            tokens, weights = zip(*options, strict=True)
            token = rng.choices(tokens, weights)[0]
            if token == lab["END"]:
                return prefix
            prefix = prefix + (token,)

    kept_samples = [s for s in (draw() for _ in range(200_000)) if s in valid]
    rejection = sum(s == ("a", "y") for s in kept_samples) / len(kept_samples)
    masked_draws = [draw(allowed=viable) for _ in range(20_000)]
    masking = sum(s == ("a", "y") for s in masked_draws) / len(masked_draws)
    comparison = lab["toy_comparison"]()
    assert abs(rejection - comparison["conditioned"]["ay"]) < 0.01
    assert abs(masking - comparison["masked"]["ay"]) < 0.01
    print(f"ok   rejection sampling gives P(ay) {rejection:.3f}; masked sampling {masking:.3f}")


def main():
    structured()
    tools = build_tools(SHOP)
    stock = tools.invoke(ToolCall(id="stock", name="list_stock", arguments={}))
    print([(row["sku"], row["needed"]) for row in stock["value"]])
    good = tools.invoke(
        ToolCall(id="draft", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 6})
    )
    print(json.dumps(good, sort_keys=True))
    bad = tools.invoke(
        ToolCall(id="bad", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": True})
    )
    print(json.dumps(bad, sort_keys=True))


if __name__ == "__main__":
    main()
