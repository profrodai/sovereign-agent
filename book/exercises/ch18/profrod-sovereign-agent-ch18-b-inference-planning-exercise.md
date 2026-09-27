---
jupyter:
  authors:
  - name: Prof Rod
    website: https://profrod.ai
  course:
    book_url: https://profrod.ai/book
    community_url: https://profrod.ai/community
    distribution_version: '2026-09-10'
    edition: nineteen-chapter-v1
    instructor: false
    lesson_id: operation
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch18-b-inference-planning-exercise
    self_contained_runtime: true
    source_basis: chapter-18-manuscript
    source_unit: ch18-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch18-b
  jupytext:
    notebook_metadata_filter: all
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  language_info:
    name: python
    version: '3.12'
---

# Chapter 18, Unit B: Plan memory and latency from the architecture

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-26**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch18/profrod-sovereign-agent-ch18-b-inference-planning-exercise.ipynb) Runs on Google Colab as it ships today (Python 3.13), or on any local Python 3.12+ kernel. It needs nothing beyond Python's standard library, and it makes no network call: the measurements it uses were recorded by the chapter's experiment and are embedded below.

This is the second of Chapter 18's two practical units. Unit A made the service's records survive a restore. This unit plans the service's model: how much memory a context costs, and how that memory slows every step.

A colleague is choosing a model for Lucy's always-on agent. They estimated the key-value cache as "two tensors per layer per head", using every attention head, and concluded that long contexts are unaffordable. The architecture says otherwise, and so do the recorded measurements. You will derive the cache from a model's configuration, test that derivation against measured decode rates, and then write the percentile function that latency reports depend on.

By the end you should be able to:

1. Derive the key-value cache's size from a model's configuration, including grouped-query attention and an explicit head dimension.
2. Predict how a long context slows decode, from the cache size and a fitted memory bandwidth, and check the prediction against measurements.
3. Explain why a formula must be tested against measurements it was not fitted to, with a negative control.
4. Compute nearest-rank percentiles without changing the data, and read a latency tail.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict the cache for a 1.5B model at 32,768 tokens | Written prediction |
| 10–30 | Prefill, decode and the bandwidth fit, from recorded timings | Worked outputs and handoff |
| 30–60 | Construct `kv_cache_bytes` and pass the visible cases | Learner code and grade table |
| 60–70 | Predict long-context decode rates and check them against the measurements | Prediction table and negative control |
| 70–85 | Changed-constraint task: nearest-rank percentiles | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |

These times are planning estimates, not measured completion times. Run All only checks that the notebook executes; the unfinished student functions deliberately report NEEDS_WORK. Keep your first attempt before you open the answers.


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell supplies:

- `CONFIGS`: the architecture of each model. Three are the local models the chapter measured, read from their model files. The fourth, Llama 3 8B, is a published configuration included for comparison.
- `MEASURED`: each local model's file size and recorded decode rates, after a short prompt and after a prompt of about 2,000 tokens, from the chapter's receipt (Ollama 0.32.5, Apple M4 Pro, 2026-09-26).
- `REQUEST_SECONDS`: the wall time of thirty recorded requests of Chapter 15's request-interpretation task.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch18-b`.

<details><summary>Supplied setup: configurations and recorded measurements</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import os
import sys
import tempfile
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch18-course-"))

CONFIGS = {
    "qwen2.5:0.5b": {"layers": 24, "attention_heads": 14, "kv_heads": 2, "hidden": 896},
    "qwen3:0.6b": {
        "layers": 28,
        "attention_heads": 16,
        "kv_heads": 8,
        "hidden": 1024,
        "head_dim": 128,
    },
    "qwen2.5:1.5b": {"layers": 28, "attention_heads": 12, "kv_heads": 2, "hidden": 1536},
    "llama-3-8b": {"layers": 32, "attention_heads": 32, "kv_heads": 8, "hidden": 4096},
}
MEASURED = {
    "qwen2.5:0.5b": {
        "file_bytes": 397_821_319,
        "decode_short": 211.1,
        "decode_long": 200.5,
        "long_tokens": 2011,
    },
    "qwen3:0.6b": {
        "file_bytes": 522_653_767,
        "decode_short": 217.7,
        "decode_long": 178.1,
        "long_tokens": 1998,
    },
    "qwen2.5:1.5b": {
        "file_bytes": 986_061_892,
        "decode_short": 129.6,
        "decode_long": 118.8,
        "long_tokens": 2010,
    },
}
REQUEST_SECONDS = [
    0.4069, 0.3873, 0.3822, 0.3981, 0.4098, 0.379, 0.3753, 0.3788, 0.4019, 0.3776,
    0.384, 0.3994, 0.3735, 0.3771, 0.3993, 0.377, 0.3827, 0.3766, 0.3997, 0.3694,
    0.3774, 0.3804, 0.4004, 0.3734, 0.379, 0.3975, 0.3747, 0.3739, 0.4036, 0.3814,
]  # fmt: skip


def no_gqa_kv_bytes(config, tokens, bytes_per_value=2):
    """The colleague's estimate: every attention head keeps its own keys and values."""
    head_dim = config["hidden"] // config["attention_heads"]
    return 2 * config["layers"] * config["attention_heads"] * head_dim * bytes_per_value * tokens


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch18-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

`qwen2.5:1.5b` has 28 layers and 12 attention heads of dimension 128, but only 2 key-value heads. Its weights occupy about 0.99 GB. Before you run anything, write down:

- the cache's size for one sequence at its full 32,768-token context, at 16 bits per value;
- whether that cache is larger or smaller than the weights.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write the cache size at 32,768 tokens, and compare it with 0.99 GB of weights.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Decode reads every weight, every step

A decode step produces one token, and to do it the processor must read every weight once. If memory delivers $B$ bytes per second and the weights occupy $W$ bytes, the step takes at least $W/B$ seconds. Real steps also pay a fixed overhead $T_0$: $t_{\text{step}} \approx T_0 + W/B$. Two models of the same family, measured on the same machine, give two equations in the two unknowns. Predict the fitted bandwidth before you run the cell.

```python tags=["foundation", "worked-example"]
intro_small, intro_large = MEASURED["qwen2.5:0.5b"], MEASURED["qwen2.5:1.5b"]
intro_t1, intro_t2 = 1 / intro_small["decode_short"], 1 / intro_large["decode_short"]
SECONDS_PER_BYTE = (intro_t2 - intro_t1) / (intro_large["file_bytes"] - intro_small["file_bytes"])
intro_overhead = intro_t1 - intro_small["file_bytes"] * SECONDS_PER_BYTE
print(
    f"step time = {intro_overhead * 1000:.2f} ms + weights / {1 / SECONDS_PER_BYTE / 1e9:.0f} GB/s"
)
```

### The key-value cache

Attention lets each new token look back at every earlier token. So that earlier tokens need not be recomputed, the server keeps each layer's **key** and **value** vectors for every token so far. Each vector has the head dimension $d$, and there is one pair per **key-value head**:

$$
\text{KV bytes} = 2 \times L \times H_{\text{kv}} \times d \times b \times T.
$$

Here $L$ is the number of layers, $H_{\text{kv}}$ the number of KV heads, $b$ the bytes per stored value and $T$ the number of tokens. The leading 2 counts keys and values.

Two details of real configurations matter:

- **Grouped-query attention** lets several query heads share one KV head. So $H_{\text{kv}}$ can be much smaller than the number of attention heads, and it must divide it evenly.
- The head dimension is usually the hidden size divided by the number of attention heads. Some models declare a `head_dim` that differs from that quotient, and then the declared value is the one used.

On every decode step the cache is read along with the weights. After $T$ tokens, a step therefore costs about $T_0 + (W + \text{KV}(T))/B$.

## Choose an explicit starting point

This unit starts from Unit A's work. To use your own, replace `None` with the path to your `practical-work/ch18-a/ch18-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import hashlib
import shutil

COURSE_INPUT = COURSE_WORK / "ch18-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_source = (
        "def restore(db, source):\n    ...  # Supplied reference: Unit A's restore.\n"
    )
    reference_handoff = {
        "schema": 1,
        "status": "VISIBLE_PASSED",
        "implementation": reference_source,
        "implementation_sha256": hashlib.sha256(reference_source.encode()).hexdigest(),
    }
    COURSE_INPUT.write_text(json.dumps(reference_handoff, indent=2, sort_keys=True) + "\n")
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
```

```python tags=["setup", "handoff-consumer"]
handoff = json.loads(COURSE_INPUT.read_text(encoding="utf-8"))
source_matches = isinstance(handoff.get("implementation"), str) and hashlib.sha256(
    handoff["implementation"].encode()
).hexdigest() == handoff.get("implementation_sha256")
handoff_status = (
    "VERIFIED" if source_matches and handoff.get("status") == "VISIBLE_PASSED" else "INVALID"
)
print("UNIT_A_HANDOFF", handoff_status)
print("Unit A's restore:", len(handoff.get("implementation", "").splitlines()), "lines of source")
```

Unit A's restore keeps the service's records across a failure. This unit keeps its model inside the machine's memory and latency budget. Both are conditions for the same always-on promise.

## Main practical: construct, connect and challenge

## 1. Construct `kv_cache_bytes`

`kv_cache_bytes(config, tokens, bytes_per_value=2)` must return the formula above for a configuration dictionary like those in `CONFIGS`:

- use `config["kv_heads"]` for $H_{\text{kv}}$;
- use `config["head_dim"]` when present, otherwise `config["hidden"] // config["attention_heads"]`;
- raise `ValueError` when `kv_heads` does not divide `attention_heads` evenly, or `tokens` is negative.

The starter below is the colleague's formula. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch18-kv-cache-bytes"]
def kv_cache_bytes(config, tokens, bytes_per_value=2):
    """Bytes of keys and values stored for `tokens` tokens of one sequence."""
    head_dim = config["hidden"] // config["attention_heads"]
    return 2 * config["layers"] * config["attention_heads"] * head_dim * bytes_per_value * tokens
```

<details><summary>Hint 1 — which heads</summary>

Only key-value heads store keys and values. Query heads share them in groups.

</details>

<details><summary>Hint 2 — which head dimension</summary>

`qwen3:0.6b` declares `head_dim` 128, while its hidden size divided by its heads is 64. Use the declared value when there is one.

</details>

```python tags=["assessment", "visible"]
import copy


def outcome(call):
    try:
        return call()
    except Exception as error:
        return type(error).__name__


VISIBLE_CASES = [
    ("qwen2.5:1.5b, one token", lambda: kv_cache_bytes(CONFIGS["qwen2.5:1.5b"], 1), 28_672),
    ("llama-3-8b, one token", lambda: kv_cache_bytes(CONFIGS["llama-3-8b"], 1), 131_072),
    ("qwen3:0.6b, one token", lambda: kv_cache_bytes(CONFIGS["qwen3:0.6b"], 1), 114_688),
    (
        "qwen2.5:0.5b, full context",
        lambda: kv_cache_bytes(CONFIGS["qwen2.5:0.5b"], 32_768),
        402_653_184,
    ),
    (
        "8-bit cache halves it",
        lambda: kv_cache_bytes(CONFIGS["qwen2.5:1.5b"], 1000, bytes_per_value=1),
        14_336_000,
    ),
    (
        "KV heads must divide attention heads",
        lambda: kv_cache_bytes(
            {"layers": 2, "attention_heads": 12, "kv_heads": 5, "hidden": 96}, 1
        ),
        "ValueError",
    ),
    ("negative tokens", lambda: kv_cache_bytes(CONFIGS["qwen2.5:1.5b"], -1), "ValueError"),
]


def grade(cases):
    rows = []
    for label, call, expected in cases:
        observed = outcome(call)
        rows.append(
            {
                "case": label,
                "expected": expected,
                "observed": observed,
                "status": "PASS" if observed == expected else "FAIL",
            }
        )
    return rows


visible_results = grade(VISIBLE_CASES)
VISIBLE_PASSED = all(row["status"] == "PASS" for row in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 2. Connect: predict the slowdown the measurements recorded

Seven hand-worked cases check arithmetic. They do not check that the formula describes a real server. The measurements can. After about 2,000 tokens of prompt, every decode step reads the cache as well as the weights. So your formula predicts the long-context decode rate from quantities the fit never saw:

$$
\text{rate}_{\text{long}} = \frac{1}{t_{\text{short}} + \text{KV}(T) \cdot \text{seconds per byte}}.
$$

The cell below makes that prediction for each measured model, from your `kv_cache_bytes`, and compares it with the recorded rate. It also makes the colleague's prediction. Yours must land within 6% for every model. The colleague's is the **negative control**: it must miss by more for at least one, or the check proves nothing.

Predict which model the colleague's formula misses most, and why.

```python tags=["integration", "learner-path"]
connected = None


def predicted_long_rate(kv_function, name):
    run = MEASURED[name]
    cache = kv_function(CONFIGS[name], run["long_tokens"])
    return 1 / (1 / run["decode_short"] + cache * SECONDS_PER_BYTE)


if VISIBLE_PASSED:
    table = []
    for name, run in MEASURED.items():
        yours = predicted_long_rate(kv_cache_bytes, name)
        colleague = predicted_long_rate(no_gqa_kv_bytes, name)
        table.append(
            {
                "model": name,
                "measured": run["decode_long"],
                "yours": round(yours, 1),
                "your_error": round(yours / run["decode_long"] - 1, 3),
                "colleague": round(colleague, 1),
                "colleague_error": round(colleague / run["decode_long"] - 1, 3),
            }
        )
    fits = all(abs(row["your_error"]) < 0.06 for row in table)
    control_rejected = any(abs(row["colleague_error"]) >= 0.06 for row in table)
    budget = 16e9  # a 16 GB accelerator, for planning
    sequences = {
        name: int((budget - run["file_bytes"]) // kv_cache_bytes(CONFIGS[name], 8192))
        for name, run in MEASURED.items()
    }
    connected = {
        "table": table,
        "fits": fits,
        "negative_control_rejected": control_rejected,
        "sequences_of_8192_in_16_gb": sequences,
    }
    for row in table:
        print(row)
    print("your formula within 6% everywhere:", fits)
    print("colleague's formula rejected:", control_rejected)
    print("8,192-token sequences that fit beside the weights in 16 GB:", sequences)
else:
    print("CONNECTION_NOT_READY — repair kv_cache_bytes, then run again.")
```

Your formula came from the architecture alone, and the bandwidth came from two other runs. Together they predict a slowdown that was measured separately, which is the strongest kind of evidence a derivation can have. Grouped-query attention is not a detail. It decides how many of Lucy's long conversations fit in memory at once, and how much each one slows the rest.

## Exit ticket

Answer three questions:

- Why does the cache grow with the number of KV heads, not the number of attention heads?
- `qwen3:0.6b` has smaller weights than `qwen2.5:1.5b` but a larger cache per token. Which would you choose for long conversations on a small machine, and why?
- Why is predicting a measurement the fit never saw stronger evidence than matching the runs you fitted?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch18-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: report the latency tail

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

An average hides the requests that make users wait, so latency is reported by percentiles. The **nearest-rank** $q$th percentile of $n$ values is the value at rank $\lceil qn/100 \rceil$ in ascending order. It is the smallest observed value that at least $q\%$ of the values do not exceed.

Implement `percentile(values, q)`:

- return the nearest-rank percentile, for $0 < q \le 100$;
- raise `ValueError` for an empty list, or for $q$ outside that range;
- **do not change `values`**. Sorting a list in place changes it for the caller, and the driver checks.

<details><summary>Hint — ranks start at one</summary>
The value at rank <code>r</code> is at index <code>r - 1</code> of a sorted copy. <code>sorted(values)</code> makes a copy; <code>values.sort()</code> does not. <code>math.ceil</code>, after <code>import math</code>, rounds up.
</details>

```python tags=["exercise", "transfer-owned"]
def percentile(values, q):
    raise NotImplementedError("Sort a copy, then take the value at rank ceil(q * n / 100)")
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("the median of three", [[3, 1, 2], 50], 2.0),
    ("p90 of one to ten", [list(range(1, 11)), 90], 9.0),
    ("p100 is the maximum", [list(range(1, 11)), 100], 10.0),
    ("a quarter of four values", [[4, 1, 3, 2], 25], 1.0),
    ("one value", [[5], 1], 5.0),
    ("an empty list is refused", [[], 50], {"raises": "ValueError"}),
    ("q of zero is refused", [[1, 2], 0], {"raises": "ValueError"}),
]


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        try:
            actual = round(candidate(*supplied), 6) + 0.0
        except NotImplementedError:
            actual = {"unfinished": True}
        except Exception as error:
            actual = {"raises": type(error).__name__}
        passed = actual == expected and supplied == arguments
        observations.append(
            {"case": label, "expected": expected, "observed": actual, "passed": passed}
        )
        print("PASS" if passed else "NEEDS_WORK", label, "expected", expected, "observed", actual)
    return observations


transfer_observations = run_transfer(percentile, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case with an expected value you worked out by hand, and rerun the driver. Then apply your function to `REQUEST_SECONDS`:

- Report p50, p90 and p99. Explain why, with thirty values, p99 is simply the maximum.
- How many requests would you need before p99 is not the maximum?
- On this idle machine the tail is short. Name two things that would lengthen it for a shared service, and the measurement that would show them.


## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit's measurements come from one machine, one server version and one idle afternoon. They show how the costs scale. They do not predict another machine's numbers, or a loaded server's tail.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch18-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch18-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch18-b",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "student",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
<!-- #endregion -->
