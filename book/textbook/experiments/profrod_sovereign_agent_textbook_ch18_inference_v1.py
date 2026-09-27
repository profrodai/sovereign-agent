# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 18 experiment: where the time in a model call goes, measured on a local server.

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch18_inference_v1.py \
      --out ch18-inference-receipt.json

For each installed model (served by Ollama on localhost) it reads the architecture from the model
file and measures, from the server's own per-phase timings:
  - prefill rate (prompt tokens per second) at three prompt lengths;
  - decode rate (output tokens per second) after a short and after a long prompt;
  - the memory bandwidth each decode rate implies, since each step reads every weight once;
  - the key-value cache's size per token and at the full context, from the architecture.
For qwen2.5:1.5b it also measures thirty requests of Chapter 15's request-interpretation task
(latency percentiles and where the time goes) and one, two and four concurrent requests.
Each prompt starts with a fresh nonce, so the server cannot reuse a cached prefix. One warmup
call per model loads it; the warmup is recorded, not hidden.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import platform
import runpy
import statistics
import subprocess
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
ECON = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch18_inference_economics_learner.py")
)
REQUESTS = runpy.run_path(
    str(ROOT / "book/textbook/experiments/profrod_sovereign_agent_textbook_ch15_request_eval_v1.py")
)
MODELS = ("qwen2.5:0.5b", "qwen3:0.6b", "qwen2.5:1.5b")
CONTEXT = 8192
NOTE = (
    "Vanilla is running low: two tubs left in the freezer. Order six tubs before the weekend. "
    "The supplier delivers on Tuesday morning and needs orders before Monday evening. "
)


def api(path, body):
    request = Request(
        f"http://127.0.0.1:11434{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=300) as response:
        return json.loads(response.read())


def get(path):
    with urlopen(f"http://127.0.0.1:11434{path}", timeout=30) as response:
        return json.loads(response.read())


def installed_bytes():
    return {m["name"]: m["size"] for m in get("/api/tags")["models"]}


def architecture(model, file_bytes):
    info = api("/api/show", {"model": model})["model_info"]
    arch = info["general.architecture"]
    heads = info[f"{arch}.attention.head_count"]
    head_dim = info.get(f"{arch}.attention.key_length") or info[f"{arch}.embedding_length"] // heads
    layers, kv_heads = info[f"{arch}.block_count"], info[f"{arch}.attention.head_count_kv"]
    context = info[f"{arch}.context_length"]
    per_token = ECON["kv_cache_bytes"](layers, kv_heads, head_dim, 1)
    return {
        "architecture": arch,
        "parameters": info["general.parameter_count"],
        "file_bytes": file_bytes,
        "bytes_per_parameter": round(file_bytes / info["general.parameter_count"], 3),
        "layers": layers,
        "attention_heads": heads,
        "kv_heads": kv_heads,
        "head_dim": head_dim,
        "context_length": context,
        "kv_bytes_per_token_f16": per_token,
        "kv_bytes_full_context_f16": per_token * context,
        "kv_bytes_per_token_without_gqa": ECON["kv_cache_bytes"](layers, heads, head_dim, 1),
    }


def generate(model, prompt, predict):
    reply = api(
        "/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": predict, "num_ctx": CONTEXT},
        },
    )
    return {key: reply.get(key) for key in TIMINGS}


TIMINGS = (
    "total_duration",
    "load_duration",
    "prompt_eval_count",
    "prompt_eval_duration",
    "eval_count",
    "eval_duration",
)


def prompt_of(words):
    """A prompt of about `words` words that no earlier request shares a prefix with."""
    text = NOTE * (words // len(NOTE.split()) + 1)
    return f"Note {uuid.uuid4().hex}. " + " ".join(text.split()[:words])


def rate(count, nanoseconds):
    return count / (nanoseconds / 1e9)


def measure_model(model, file_bytes, runs):
    shape = architecture(model, file_bytes)
    warmup = generate(model, prompt_of(20), 8)
    runs.append({"model": model, "kind": "warmup", **warmup})
    prefill = []
    for words in (80, 400, 1600):
        observed = []
        for _ in range(3):
            row = generate(model, prompt_of(words), 1)
            runs.append({"model": model, "kind": f"prefill-{words}", **row})
            observed.append(rate(row["prompt_eval_count"], row["prompt_eval_duration"]))
        prefill.append(
            {
                "prompt_tokens": row["prompt_eval_count"],
                "tokens_per_second": round(statistics.median(observed), 1),
            }
        )
    decode = {}
    for label, words in (("short_prompt", 20), ("long_prompt", 1600)):
        observed = []
        for _ in range(5):
            row = generate(model, prompt_of(words) + "\nNow write a long story.", 128)
            runs.append({"model": model, "kind": f"decode-{label}", **row})
            observed.append(rate(row["eval_count"], row["eval_duration"]))
        decode[label] = round(statistics.median(observed), 1)
    implied = decode["short_prompt"] * file_bytes
    return {
        **shape,
        "warmup_load_seconds": round(warmup["load_duration"] / 1e9, 3),
        "prefill": prefill,
        "decode_tokens_per_second": decode,
        "implied_weight_read_gb_per_second": round(implied / 1e9, 1),
        "flops_per_output_token": ECON["flops_per_token"](shape["parameters"]),
    }


def request_task(model, runs, count=30):
    system = REQUESTS["PROMPTS"]["contrast"]
    rows = []
    for index in range(count):
        case = REQUESTS["CASES"][index % len(REQUESTS["CASES"])]
        payload = json.dumps(REQUESTS["candidate_input"](case))
        started = time.perf_counter()
        reply = api(
            "/api/chat",
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": f"Request {uuid.uuid4().hex}.\n{system}"},
                    {"role": "user", "content": payload},
                ],
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "num_predict": 300, "num_ctx": CONTEXT},
            },
        )
        wall = time.perf_counter() - started
        row = {key: reply.get(key) for key in TIMINGS} | {"wall_seconds": wall}
        runs.append({"model": model, "kind": "request-task", "case": case.name, **row})
        rows.append(row)
    walls = [r["wall_seconds"] for r in rows]
    prefill = sum(r["prompt_eval_duration"] for r in rows) / 1e9
    decode = sum(r["eval_duration"] for r in rows) / 1e9
    return {
        "requests": count,
        "mean_prompt_tokens": round(statistics.mean(r["prompt_eval_count"] for r in rows), 1),
        "mean_output_tokens": round(statistics.mean(r["eval_count"] for r in rows), 1),
        "wall_seconds": {
            "p50": round(ECON["percentile"](walls, 50), 3),
            "p90": round(ECON["percentile"](walls, 90), 3),
            "max": round(max(walls), 3),
            "mean": round(statistics.mean(walls), 3),
        },
        "share_of_time": {
            "prefill": round(prefill / sum(walls), 3),
            "decode": round(decode / sum(walls), 3),
            "other": round(1 - (prefill + decode) / sum(walls), 3),
        },
    }


def concurrent_decode(model, runs):
    results = []
    for parallel in (1, 2, 4):
        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(parallel) as pool:
            rows = list(
                pool.map(
                    lambda _: generate(model, prompt_of(20) + "\nNow write a long story.", 64),
                    range(parallel),
                )
            )
        wall = time.perf_counter() - started
        for row in rows:
            runs.append({"model": model, "kind": f"concurrent-{parallel}", **row})
        tokens = sum(r["eval_count"] for r in rows)
        results.append(
            {
                "concurrent_requests": parallel,
                "output_tokens": tokens,
                "wall_seconds": round(wall, 3),
                "aggregate_tokens_per_second": round(tokens / wall, 1),
                "per_request_decode_tokens_per_second": round(
                    statistics.median(rate(r["eval_count"], r["eval_duration"]) for r in rows), 1
                ),
            }
        )
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    sizes = installed_bytes()
    runs = []
    chip = subprocess.run(
        ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True
    ).stdout.strip()
    receipt = {
        "schema": 1,
        "experiment": "ch18-inference-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "chip": chip or None,
        "server": "ollama " + get("/api/version")["version"],
        "context_tokens": CONTEXT,
        "models": {model: measure_model(model, sizes[model], runs) for model in MODELS},
    }
    receipt["request_task_qwen2.5:1.5b"] = request_task("qwen2.5:1.5b", runs)
    receipt["concurrency_qwen2.5:1.5b"] = concurrent_decode("qwen2.5:1.5b", runs)
    receipt["seconds"] = round(time.time() - started, 1)
    receipt["runs"] = runs
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "runs"}, indent=2))


if __name__ == "__main__":
    main()
