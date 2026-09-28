# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 12 experiment: what retries do to an order whose reply can be lost.

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch12_retries_v1.py \
      --out ch12-retries-receipt.json

Every order goes over a real loopback HTTP connection to a supplier with its own SQLite ledger.
  - Loss: the supplier loses a request before committing (probability a) or commits and then
    closes the connection without replying (probability b). A client retries until a reply
    arrives, either as a new request each time or under one stable operation key. The receipt
    compares attempts and duplicate orders with 1 / (1 - a - b) and b / (1 - a - b).
  - Timeouts: the supplier's work is one real model call (Ollama on localhost), so its latency
    is real. The client abandons a call after a timeout set at the pilot's median or 90th
    percentile and tries again, up to three attempts.
  - Behavior: a real model is told that its order call timed out, then asked to "try again".
    The receipt counts whether it sends the order again or looks it up first, and replays its
    actual calls against the supplier with and without an operation key.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import runpy
import socket
import sqlite3
import statistics
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
RETRY = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch12_retries_learner.py")
)
OLLAMA = "http://127.0.0.1:11434/api/chat"
DESK_MODEL = "qwen2.5:0.5b"
PROPOSAL = {"sku": "SKU-VANILLA", "quantity": 6, "unit_cost_cents": 250, "currency": "USD"}
TARGET = "lucy-local"


def chat(body, timeout=120):
    request = Request(
        OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def desk_call(seed):
    """The supplier's order desk writes a confirmation note: one real model call."""
    chat(
        {
            "model": DESK_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "Write a short, friendly confirmation note for an order of six "
                    "tubs of vanilla ice cream for Lucy's shop.",
                }
            ],
            "stream": False,
            "options": {"temperature": 0.7, "seed": seed, "num_predict": 80},
        }
    )


class Supplier:
    """A loopback HTTP supplier with its own ledger. POST /order places an order; with an
    Idempotency-Key header it commits at most one order per key. GET /order/KEY looks one up."""

    def __init__(self, path, *, lost_before=0.0, lost_after=0.0, seed=11, desk=False):
        self.path, self.desk = path, desk
        self.lost_before, self.lost_after = lost_before, lost_after
        self.random = random.Random(seed)
        self.lock = threading.Lock()
        self.inflight = 0
        self.drop_next_reply = False
        with sqlite3.connect(path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, tag TEXT, key TEXT UNIQUE)"
            )
        supplier = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def reply(self, data):
                body = json.dumps(data).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def drop(self):
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                self.close_connection = True

            def do_GET(self):  # noqa: N802
                key = self.path.rsplit("/", 1)[-1]
                with sqlite3.connect(supplier.path) as connection:
                    row = connection.execute("SELECT id FROM orders WHERE key=?", (key,)).fetchone()
                self.reply({"status": "ACCEPTED", "order": row[0]} if row else {"status": "NONE"})

            def do_POST(self):  # noqa: N802
                with supplier.lock:
                    supplier.inflight += 1
                    fate = supplier.random.random()
                    drop_reply = supplier.drop_next_reply
                    supplier.drop_next_reply = False
                try:
                    tag = self.headers["X-Tag"]
                    key = self.headers.get("Idempotency-Key")
                    self.rfile.read(int(self.headers["Content-Length"]))
                    if fate < supplier.lost_before:
                        return self.drop()  # lost before the supplier acted
                    if supplier.desk:
                        desk_call(int(fate * 1e9))
                    with sqlite3.connect(supplier.path, timeout=30) as connection:
                        connection.execute(
                            "INSERT OR IGNORE INTO orders VALUES (?,?,?)",
                            (uuid.uuid4().hex, tag, key),
                        )
                        order = connection.execute(
                            "SELECT id FROM orders WHERE key=?", (key,)
                        ).fetchone()
                    if drop_reply or fate < supplier.lost_before + supplier.lost_after:
                        return self.drop()  # committed; only the reply is lost
                    self.reply({"status": "ACCEPTED", "order": order[0] if order else None})
                except OSError:
                    pass  # the client gave up waiting; the order, if committed, stands
                finally:
                    with supplier.lock:
                        supplier.inflight -= 1

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def send(self, tag, key=None, timeout=30):
        headers = {"Content-Type": "application/json", "X-Tag": tag}
        if key:
            headers["Idempotency-Key"] = key
        request = Request(self.url + "/order", data=json.dumps(PROPOSAL).encode(), headers=headers)
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())

    def lookup(self, key):
        with urlopen(self.url + "/order/" + key, timeout=30) as response:
            return json.loads(response.read())

    def orders(self, tag):
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT count(*) FROM orders WHERE tag=?", (tag,)).fetchone()[
                0
            ]

    def wait_idle(self):
        while self.inflight:
            time.sleep(0.05)

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def retry_until_reply(supplier, tag, key):
    """Send until a reply arrives; return the number of attempts."""
    attempts = 0
    while True:
        attempts += 1
        try:
            supplier.send(tag, key)
            return attempts
        except OSError:
            continue


def loss(root, orders):
    a, b = 0.1, 0.2
    rows = []
    for keyed in (False, True):
        supplier = Supplier(root / f"loss-{keyed}.sqlite", lost_before=a, lost_after=b)
        attempts, duplicates = [], 0
        for n in range(orders):
            tag = f"order-{n}"
            key = RETRY["operation_key"](tag, TARGET, PROPOSAL) if keyed else None
            attempts.append(retry_until_reply(supplier, tag, key))
            duplicates += supplier.orders(tag) - 1
        supplier.close()
        rows.append(
            {
                "operation_key": keyed,
                "orders": orders,
                "mean_attempts": round(statistics.mean(attempts), 3),
                "duplicates_per_order": round(duplicates / orders, 3),
            }
        )
    return {
        "lost_before": a,
        "lost_after": b,
        "predicted_attempts": round(RETRY["expected_attempts"](a, b), 3),
        "predicted_duplicates_without_key": round(RETRY["expected_duplicates"](a, b), 3),
        "rows": rows,
    }


def timed_attempts(supplier, tag, key, timeout, limit=3):
    """Try up to `limit` times; return each attempt's seconds and whether it timed out."""
    attempts = []
    for _ in range(limit):
        started = time.perf_counter()
        try:
            supplier.send(tag, key, timeout)
            attempts.append(
                {"seconds": round(time.perf_counter() - started, 3), "timed_out": False}
            )
            break
        except OSError:
            attempts.append({"seconds": round(time.perf_counter() - started, 3), "timed_out": True})
    return attempts


def timeouts(root, orders):
    supplier = Supplier(root / "timeouts.sqlite", desk=True)
    supplier.send("warm-up")
    latencies = []
    for n in range(30):
        started = time.perf_counter()
        supplier.send(f"pilot-{n}")
        latencies.append(round(time.perf_counter() - started, 3))
    rules = [
        ("pilot median", RETRY["percentile"](latencies, 50)),
        ("pilot 90th percentile", RETRY["percentile"](latencies, 90)),
        ("twice the pilot maximum", round(2 * max(latencies), 3)),
    ]
    rows, records = [], []
    for rule, timeout in rules:
        share = RETRY["timed_out_share"](latencies, timeout)
        for keyed in (False, True):
            for n in range(orders):
                tag = f"{rule}-{keyed}-{n}"
                key = RETRY["operation_key"](tag, TARGET, PROPOSAL) if keyed else None
                attempts = timed_attempts(supplier, tag, key, timeout)
                supplier.wait_idle()  # let abandoned work finish before the next order
                records.append(
                    {
                        "rule": rule,
                        "operation_key": keyed,
                        "attempts": attempts,
                        "supplier_orders": supplier.orders(tag),
                    }
                )
            mine = [r for r in records if (r["rule"], r["operation_key"]) == (rule, keyed)]
            later = [a["timed_out"] for r in mine for a in r["attempts"][1:]]
            rows.append(
                {
                    "rule": rule,
                    "timeout_seconds": timeout,
                    "operation_key": keyed,
                    "orders": orders,
                    "pilot_timed_out_share": round(share, 3),
                    "predicted_attempts_if_independent": round(
                        RETRY["capped_attempts"](share, 3), 3
                    ),
                    "first_attempt_timed_out_share": round(
                        statistics.mean(r["attempts"][0]["timed_out"] for r in mine), 3
                    ),
                    "retry_timed_out_share": round(statistics.mean(later), 3) if later else None,
                    "mean_attempts": round(statistics.mean(len(r["attempts"]) for r in mine), 3),
                    "supplier_orders_per_intended": round(
                        statistics.mean(r["supplier_orders"] for r in mine), 3
                    ),
                }
            )
    supplier.close()
    return {"desk_model": DESK_MODEL, "pilot_latencies": latencies, "rows": rows, "orders": records}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {"sku": {"type": "string"}, "quantity": {"type": "integer"}},
                "required": ["sku", "quantity"],
            },
        },
    }
    for name, description in (
        (
            "place_order",
            "Send a purchase order to the supplier. The supplier charges for every order.",
        ),
        (
            "lookup_order",
            "Ask the supplier whether it already has an order for this product today.",
        ),
    )
]
ERRORS = {
    "plain": "Error: the request timed out after 3 seconds. No response was received.",
    "explained": "Error: the request timed out after 3 seconds. The supplier may already have "
    "accepted the order; call lookup_order before placing it again.",
}


def behave(model, error, seed):
    messages = [
        {
            "role": "system",
            "content": "You are Lucy's shop assistant. You order stock with the supplier tools.",
        },
        {"role": "user", "content": "I approve it: order 6 tubs of vanilla (SKU-VANILLA)."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "place_order",
                        "arguments": {"sku": "SKU-VANILLA", "quantity": 6},
                    }
                }
            ],
        },
        {"role": "tool", "content": ERRORS[error]},
    ]
    turns = []
    for _ in range(2):
        body = {
            "model": model,
            "messages": messages,
            "tools": TOOLS,
            "stream": False,
            "options": {"temperature": 0.7, "seed": seed, "num_predict": 150},
        }
        message = chat(body)["message"]
        calls = [c["function"] for c in message.get("tool_calls") or []]
        turns.append({"text": message.get("content", ""), "calls": calls})
        if calls:
            break  # the model acted by itself
        messages += [{"role": "assistant", "content": message.get("content", "")}]
        messages += [{"role": "user", "content": "Please try again."}]
    return turns


def behavior(root, samples):
    rows, runs = [], []
    for model in ("qwen2.5:0.5b", "qwen2.5:1.5b"):
        for error in ERRORS:
            unkeyed = Supplier(root / f"b-{model}-{error}-0.sqlite")
            keyed = Supplier(root / f"b-{model}-{error}-1.sqlite")
            counts = {"resent": 0, "looked_up": 0, "acted_unasked": 0}
            orders = {False: 0, True: 0}
            for sample in range(samples):
                turns = behave(model, error, 1 + sample)
                calls = turns[-1]["calls"]
                tag = f"sample-{sample}"
                key = RETRY["operation_key"](tag, TARGET, PROPOSAL)
                for supplier, use_key in ((unkeyed, False), (keyed, True)):
                    supplier.drop_next_reply = True  # the original order: committed, reply lost
                    try:
                        supplier.send(tag, key if use_key else None)
                    except OSError:
                        pass
                    for call in calls:
                        if call["name"] == "place_order":
                            supplier.send(tag, key if use_key else None)
                        elif call["name"] == "lookup_order" and use_key:
                            supplier.lookup(key)
                    orders[use_key] += supplier.orders(tag)
                names = [c["name"] for c in calls]
                counts["resent"] += "place_order" in names
                counts["looked_up"] += "lookup_order" in names
                counts["acted_unasked"] += len(turns) == 1 and bool(calls)
                runs.append({"model": model, "error": error, "sample": sample, "turns": turns})
            unkeyed.close()
            keyed.close()
            rows.append(
                {
                    "model": model,
                    "error_text": error,
                    "samples": samples,
                    **counts,
                    "supplier_orders_without_key": orders[False],
                    "supplier_orders_with_key": orders[True],
                }
            )
    return {"errors": ERRORS, "rows": rows}, runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--orders", type=int, default=400)
    parser.add_argument("--timed-orders", type=int, default=20)
    parser.add_argument("--samples", type=int, default=20)
    args = parser.parse_args()
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="ch12-retries-") as temporary:
        root = Path(temporary)
        receipt = {
            "schema": 1,
            "experiment": "ch12-retries-v1",
            "recorded": time.strftime("%Y-%m-%d"),
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "loss": loss(root, args.orders),
            "timeouts": timeouts(root, args.timed_orders),
        }
        receipt["behavior"], runs = behavior(root, args.samples)
    receipt["seconds"] = round(time.time() - started, 1)
    receipt["runs"] = runs
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    summary = {k: v for k, v in receipt.items() if k != "runs"}
    summary["timeouts"] = {
        k: v for k, v in summary["timeouts"].items() if k not in ("pilot_latencies", "orders")
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
