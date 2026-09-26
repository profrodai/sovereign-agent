# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 15 experiment: how much does an evaluation score actually tell you?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch15_statistics_v1.py \
      --out ch15-statistics-receipt.json [--live] [--model qwen2.5:1.5b] [--samples 10]

Offline, it measures:
  - the exact coverage of nominal 95% Wald and Wilson intervals at small sample sizes;
  - the chapter's retained qwen3 request-interpretation run (84 attempts): each candidate's
    score with both intervals, the naive and the clustered standard error, and McNemar's exact
    paired test between candidates;
  - the number of cases needed to detect a given difference, unpaired and paired.
With --live, it samples a real model (served by Ollama on localhost) `--samples` times per request
case at temperature 0.8 under both frozen instructions, then reports pass@k (unbiased and naive)
and the paired difference between the instructions with a clustered standard error.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import runpy
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
STATS = runpy.run_path(
    str(
        ROOT / "book/textbook/learner/profrod_sovereign_agent_ch15_evaluation_statistics_learner.py"
    )
)
REQUESTS = runpy.run_path(
    str(ROOT / "book/textbook/experiments/profrod_sovereign_agent_textbook_ch15_request_eval_v1.py")
)
RETAINED = ROOT / "docs/evidence/always-on/ch12-request-interpretation-live-v1.json"


def rounded(pair):
    return [round(pair[0], 3), round(pair[1], 3)]


def coverage_table():
    rows = []
    for trials in (16, 28, 100):
        for p in (0.5, 0.9, 0.95, 0.99):
            rows.append(
                {
                    "n": trials,
                    "p": p,
                    "wald": round(STATS["coverage"](STATS["wald_interval"], p, trials), 3),
                    "wilson": round(STATS["coverage"](STATS["wilson_interval"], p, trials), 3),
                }
            )
    return rows


def retained_run():
    report = json.loads(RETAINED.read_text())
    rows = report["rows"]
    names = sorted({row["candidate"] for row in rows})
    keyed = {(r["candidate"], r["case"], r["repeat"]): r["passed"] for r in rows}
    attempts = sorted({(r["case"], r["repeat"]) for r in rows})
    cases = sorted({r["case"] for r in rows})
    summary = {}
    for name in names:
        results = [keyed[(name, case, repeat)] for case, repeat in attempts]
        passed, n = sum(results), len(results)
        groups = [
            [keyed[(name, case, repeat)] for c, repeat in attempts if c == case] for case in cases
        ]
        phat = passed / n
        summary[name] = {
            "passed": passed,
            "attempts": n,
            "wald_95": rounded(STATS["wald_interval"](passed, n)),
            "wilson_95": rounded(STATS["wilson_interval"](passed, n)),
            "naive_standard_error": round(math.sqrt(phat * (1 - phat) / n), 4),
            "clustered_standard_error": round(STATS["clustered_standard_error"](groups), 4),
            "cases_same_result_both_repeats": sum(len(set(g)) == 1 for g in groups),
        }
    comparisons = []
    for i, first in enumerate(names):
        for second in names[i + 1 :]:
            counts = STATS["paired_counts"](
                [keyed[(first, c, r)] for c, r in attempts],
                [keyed[(second, c, r)] for c, r in attempts],
            )
            comparisons.append(
                {
                    "first": first,
                    "second": second,
                    **counts,
                    "mcnemar_p": float(
                        f"{STATS['mcnemar_exact'](counts['only_first'], counts['only_second']):.3g}"
                    ),
                }
            )
    return {
        "source": str(RETAINED.relative_to(ROOT)),
        "model": report["model"],
        "cases": len(cases),
        "repeats": len(attempts) // len(cases),
        "candidates": summary,
        "paired": comparisons,
    }


def sample_sizes():
    unpaired = [
        {"from": a, "to": b, "cases_per_candidate": STATS["cases_needed"](a, b)}
        for a, b in ((0.80, 0.85), (0.80, 0.90), (0.50, 0.55), (0.90, 0.95))
    ]
    paired = [
        {
            "discordant": d,
            "difference": 0.05,
            "cases": STATS["paired_cases_needed"](d, 0.05),
        }
        for d in (0.05, 0.10, 0.20, 0.40)
    ]
    return {"alpha": 0.05, "power": 0.8, "unpaired": unpaired, "paired": paired}


def chat(model, messages, **options):
    body = {"model": model, "messages": messages, "stream": False, **options}
    request = Request(
        "http://127.0.0.1:11434/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def live(model, samples):
    runs = []
    per_case = []
    for case in REQUESTS["CASES"]:
        row = {"case": case.name, "split": case.split}
        for name, prompt in REQUESTS["PROMPTS"].items():
            outcomes = []
            for sample in range(samples):

                def infer(payload, prompt=prompt, sample=sample):
                    reply = chat(
                        model,
                        [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": json.dumps(payload)},
                        ],
                        temperature=0.8,
                        seed=1 + sample,
                        max_tokens=300,
                    )
                    return reply["choices"][0]["message"]["content"], reply["usage"][
                        "completion_tokens"
                    ]

                result = REQUESTS["run_case"](case, name, infer, sample + 1)
                outcomes.append(result["passed"])
                runs.append(
                    {
                        key: result[key]
                        for key in ("case", "candidate", "repeat", "raw", "passed", "error")
                    }
                )
            row[name] = outcomes
        per_case.append(row)
        print(case.name, {n: sum(row[n]) for n in REQUESTS["PROMPTS"]}, flush=True)

    pass_at = {}
    for name in REQUESTS["PROMPTS"]:
        pass_at[name] = {}
        for k in (1, 2, 5):
            unbiased = [STATS["pass_at_k"](samples, sum(r[name]), k) for r in per_case]
            naive = [STATS["naive_pass_at_k"](samples, sum(r[name]), k) for r in per_case]
            pass_at[name][k] = {
                "unbiased": round(sum(unbiased) / len(unbiased), 4),
                "naive": round(sum(naive) / len(naive), 4),
            }
    # Paired difference, contrast minus minimal, with the case as the unit of sampling.
    differences = [sum(r["contrast"]) / samples - sum(r["minimal"]) / samples for r in per_case]
    mean = sum(differences) / len(differences)
    clustered = math.sqrt(
        sum((d - mean) ** 2 for d in differences) / (len(differences) - 1) / len(differences)
    )
    everything = {name: [x for r in per_case for x in r[name]] for name in REQUESTS["PROMPTS"]}
    rates = {name: sum(v) / len(v) for name, v in everything.items()}
    naive_unpaired = math.sqrt(
        sum(p * (1 - p) / len(everything[name]) for name, p in rates.items())
    )
    return {
        "model": model,
        "temperature": 0.8,
        "samples_per_case": samples,
        "cases": len(per_case),
        "per_case_correct": [
            {"case": r["case"], "split": r["split"]}
            | {name: sum(r[name]) for name in REQUESTS["PROMPTS"]}
            for r in per_case
        ],
        "pass_rate": {name: round(p, 4) for name, p in rates.items()},
        "pass_at_k": pass_at,
        "contrast_minus_minimal": {
            "difference": round(mean, 4),
            "clustered_standard_error": round(clustered, 4),
            "interval_95": [round(mean - 1.96 * clustered, 4), round(mean + 1.96 * clustered, 4)],
            "naive_unpaired_standard_error": round(naive_unpaired, 4),
        },
    }, runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen2.5:1.5b")
    parser.add_argument("--samples", type=int, default=10)
    args = parser.parse_args()
    started = time.time()
    receipt = {
        "schema": 1,
        "experiment": "ch15-statistics-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "coverage_of_nominal_95": coverage_table(),
        "retained_run": retained_run(),
        "sample_size": sample_sizes(),
    }
    if args.live:
        receipt["live"], receipt["runs"] = live(args.model, args.samples)
    receipt["seconds"] = round(time.time() - started, 1)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump({k: v for k, v in receipt.items() if k != "runs"}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
