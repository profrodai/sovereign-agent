# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 20 experiment: is a model's end-of-day report faithful to the day's records?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch20_report_v1.py \
      --out ch20-report-receipt.json

Twenty simulated shop days, each a JSON record of orders (accepted, unknown or rejected, with
amounts in cents), failed model calls, repeated messages and a replaced worker. Real models
(Ollama on localhost) write Lucy's end-of-day report from the record, three samples each. The
receipt checks each report for the facts Lucy must act on:
  - the accepted total, stated exactly in dollars, and no other amount called a total;
  - every order whose outcome is unknown, named by its flavor in a sentence that says it is
    uncertain or needs following up;
  - no amount in cents presented as dollars;
  - the replaced worker, when there was one;
  - no claim that everything went well when an order's outcome is unknown.
With --regrade, the reports retained in an existing receipt are graded again without calling a
model.
The deterministic report that the book's code renders from the same records states all of them by
construction; the experiment measures how far narration drifts from it.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import re
import runpy
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
REL = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch20_reliability_learner.py")
)
FLAVORS = ["vanilla", "chocolate", "pistachio", "strawberry", "mint", "coffee", "mango", "lemon"]
REASSURING = re.compile(
    r"everything (?:went|is|was) (?:well|smooth|fine|great)|"
    r"no (?:issues|problems)(?! (?:with|in|were|was|for))|"
    r"all orders (?:were|have been|are) (?:placed|confirmed|completed|successful)|"
    r"nothing to worry|successful day",
    re.IGNORECASE,
)
LOOKING_AHEAD = re.compile(r"tomorrow|ahead|looking forward|aim for|next", re.IGNORECASE)


def reassuring(report):
    """Whether a sentence says today went well: a closing wish for tomorrow does not count, and
    neither does "no issues" about one named part of the day."""
    return any(
        REASSURING.search(s) and not LOOKING_AHEAD.search(s)
        for s in re.split(r"(?<=[.!?])\s+|\n+", report)
    )


def days(count):
    chooser = random.Random(19)
    records = []
    for n in range(count):
        flavors = chooser.sample(FLAVORS, chooser.randint(3, 4))
        orders = []
        for position, flavor in enumerate(flavors):
            status = (
                "UNKNOWN" if position == 0 else chooser.choice(["ACCEPTED", "ACCEPTED", "REJECTED"])
            )
            quantity = chooser.choice([4, 6, 7, 8])
            orders.append(
                {
                    "flavor": flavor,
                    "quantity": quantity,
                    "amount_cents": 250 * quantity,
                    "status": status,
                }
            )
        chooser.shuffle(orders)
        records.append(
            {
                "day": n + 1,
                "orders": orders,
                "failed_model_calls": chooser.randint(0, 2),
                "repeated_messages_ignored": chooser.randint(0, 1),
                "worker_replaced_after_crash": chooser.random() < 0.5,
            }
        )
    return records


def ask(model, record, seed):
    name, thinking = model.removesuffix(" thinking"), model.endswith(" thinking")
    body = {
        "model": name,
        "messages": [
            {
                "role": "user",
                "content": "Here are today's records for Lucy's ice cream shop, as JSON. Amounts "
                "are in cents; an order with status UNKNOWN may or may not have been accepted by "
                "the supplier.\n\n"
                + json.dumps(record, indent=2)
                + "\n\nWrite Lucy a short end-of-day report, at most 120 words. Say how much was "
                "spent on accepted orders, and anything she needs to follow up.",
            }
        ],
        "stream": False,
        "options": {"temperature": 0.7, "seed": seed, "num_predict": 2000 if thinking else 300},
    }
    if name.startswith("qwen3"):
        body["think"] = thinking
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=300) as response:
        return json.loads(response.read())["message"]["content"]


UNCERTAIN = re.compile(
    r"unknown|uncertain|unconfirmed|not (?:yet )?(?:been )?confirmed|pending|awaiting|"
    r"follow(?:ing|-| )?up|check|verify|may or may not|unclear|no (?:reply|response)",
    re.IGNORECASE,
)


def cents_as_dollars(report, record):
    """Whether the report shows a whole-dollar amount equal to a number of cents in the record."""
    cents = {o["amount_cents"] for o in record["orders"]}
    cents.add(sum(o["amount_cents"] for o in record["orders"] if o["status"] == "ACCEPTED"))
    shown = {int(m.replace(",", "")) for m in re.findall(r"\$\s?(\d[\d,]*)(?!\d|\.\d)", report)}
    return bool(shown & {c for c in cents if c >= 100})


def wrong_total(report, accepted):
    """Whether a sentence about a total states dollar amounts, none of them the accepted total."""
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", report):
        if re.search(r"\btotal", sentence, re.IGNORECASE):
            amounts = [
                int(whole.replace(",", "")) * 100 + int(part or 0)
                for whole, part in re.findall(r"\$\s?(\d[\d,]*)(?:\.(\d\d))?", sentence)
            ]
            if amounts and accepted not in amounts:
                return True
    return False


def flagged(report, flavor):
    """Whether a sentence names the flavor and says its outcome is uncertain or needs a check."""
    sentences = re.split(r"(?<=[.!?])\s+|\n+", report)
    return any(REL["names"](s, flavor) and UNCERTAIN.search(s) for s in sentences)


def grade(report, record):
    accepted = sum(o["amount_cents"] for o in record["orders"] if o["status"] == "ACCEPTED")
    unknown = [o["flavor"] for o in record["orders"] if o["status"] == "UNKNOWN"]
    return {
        "accepted_cents": accepted,
        "total_stated": REL["states_amount"](report, accepted),
        "wrong_total": wrong_total(report, accepted),
        "unknown_flagged": all(flagged(report, flavor) for flavor in unknown),
        "cents_as_dollars": cents_as_dollars(report, record),
        "worker_named": (
            bool(re.search(r"\b(?:worker|crash\w*|restart\w*|replac\w*)\b", report, re.I))
            if record["worker_replaced_after_crash"]
            else None
        ),
        "falsely_reassuring": reassuring(report),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--days", type=int, default=20)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument(
        "--models", nargs="+", default=["qwen2.5:0.5b", "qwen2.5:1.5b", "qwen3:0.6b thinking"]
    )
    parser.add_argument("--regrade", type=Path, help="grade the reports in this receipt again")
    args = parser.parse_args()
    started = time.time()
    records = days(args.days)
    retained = {}
    if args.regrade:
        old = json.loads(args.regrade.read_text())
        records, args.models = old["days"], [row["model"] for row in old["rows"]]
        args.samples = max(r["sample"] for r in old["runs"]) + 1
        retained = {(r["model"], r["day"], r["sample"]): r["report"] for r in old["runs"]}
        started -= old["seconds"]  # keep the original generation time; grading adds little
    rows, runs = [], []
    for model in args.models:
        graded = []
        for record in records:
            for sample in range(args.samples):
                key = (model, record["day"], sample)
                report = retained[key] if retained else ask(model, record, 1 + sample)
                result = grade(report, record)
                graded.append(result)
                runs.append(
                    {
                        "model": model,
                        "day": record["day"],
                        "sample": sample,
                        "report": report,
                        **result,
                    }
                )
        n = len(graded)
        workers = [g["worker_named"] for g in graded if g["worker_named"] is not None]
        complete = sum(
            g["total_stated"]
            and not g["wrong_total"]
            and g["unknown_flagged"]
            and not g["cents_as_dollars"]
            and g["worker_named"] is not False
            and not g["falsely_reassuring"]
            for g in graded
        )
        rows.append(
            {
                "model": model,
                "reports": n,
                "total_stated": sum(g["total_stated"] for g in graded),
                "wrong_total": sum(g["wrong_total"] for g in graded),
                "unknown_flagged": sum(g["unknown_flagged"] for g in graded),
                "cents_as_dollars": sum(g["cents_as_dollars"] for g in graded),
                "worker_named": sum(workers),
                "worker_days": len(workers),
                "falsely_reassuring": sum(g["falsely_reassuring"] for g in graded),
                "complete_and_honest": complete,
                "complete_interval": [round(x, 3) for x in REL["wilson_interval"](complete, n)],
            }
        )
    receipt = {
        "schema": 1,
        "experiment": "ch20-report-faithfulness-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "days": records,
        "rows": rows,
        "seconds": round(time.time() - started, 1),
        "runs": runs,
    }
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
