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
    lesson_id: shop-tools
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch02-b-constrained-decoding-exercise
    self_contained_runtime: true
    source_basis: chapter-2-manuscript
    source_unit: ch02-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch02-b
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

# Chapter 2, Unit B: See what constrained decoding does to a distribution

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-26**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch02/profrod-sovereign-agent-ch02-b-constrained-decoding-exercise.ipynb) Runs on Google Colab as it ships today (Python 3.13), or on any local Python 3.12+ kernel. It needs nothing beyond Python's standard library, and it makes no network call.

This is the second of Chapter 2's two practical units. Unit A built typed tools that refuse malformed requests. This unit looks at the other side: how a server makes a model's request well formed in the first place, and what that does to the answer.

A colleague says: "With a schema enforced, the model samples from its own distribution, just restricted to valid answers." You will build token-by-token constrained decoding on models small enough to enumerate exactly, and measure how far that claim is from the truth. Then you will write the arithmetic of retrying unconstrained output instead.

By the end you should be able to:

1. Explain constrained decoding as masking disallowed tokens and renormalizing the rest, one step at a time.
2. Compute the exact distribution that masking produces, and compare it with the model conditioned on validity.
3. Check an exact calculation against simulation, and use a case with no gap as a negative control.
4. Compute the chance that retried unconstrained output is valid, and compare the two strategies.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what masking does to the trap model | Written prediction |
| 10–30 | Masked softmax, conditioning and the trap model | Worked outputs and handoff |
| 30–60 | Construct `masked` and pass the visible cases | Learner code and grade table |
| 60–70 | Measure the gap as the trap strengthens, against rejection sampling | Distance table and negative control |
| 70–85 | Changed-constraint task: retrying unconstrained output | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |

These times are planning estimates, not measured completion times. Run All only checks that the notebook executes; the unfinished student functions deliberately report NEEDS_WORK. Keep your first attempt before you open the answers.


## Run the self-contained setup

The unit needs only Python's standard library. A **toy model** here is a dictionary from a prefix (a tuple of tokens) to the next token's probabilities; `END` finishes a sequence. The collapsed cell supplies:

- `trap_model(t)`: writes "a" first with probability 0.9 and "b" with 0.1. After "a" it writes the invalid "x" with probability `t` and the valid "y" otherwise; after "b" it always writes "y". The valid answers are "ay" and "by";
- `sequences(model)`, every complete sequence with its probability, and `conditioned(model, valid)`, the model restricted to valid sequences and renormalized;
- `rejection_sample(model, valid, kept, seed)`: sample complete sequences, keep only valid ones, return their frequencies;
- `total_variation(p, q)`.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch02-b`.

<details><summary>Supplied setup: toy models, conditioning and rejection sampling</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import os
import random
import sys
import tempfile
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch02-course-"))

END = "$"
VALID = {("a", "y"), ("b", "y")}


def trap_model(t):
    return {
        (): {"a": 0.9, "b": 0.1},
        ("a",): {"x": t, "y": 1 - t},
        ("b",): {"y": 1.0},
        ("a", "x"): {END: 1.0},
        ("a", "y"): {END: 1.0},
        ("b", "y"): {END: 1.0},
    }


def is_valid(sequence):
    return sequence in VALID


def can_become_valid(prefix):
    return any(v[: len(prefix)] == prefix for v in VALID)


def sequences(model, prefix=()):
    out = {}
    for token, p in model[prefix].items():
        if token == END:
            out[prefix] = out.get(prefix, 0.0) + p
        else:
            for sequence, q in sequences(model, prefix + (token,)).items():
                out[sequence] = out.get(sequence, 0.0) + p * q
    return out


def conditioned(model, valid):
    everything = sequences(model)
    total = sum(p for s, p in everything.items() if valid(s))
    return {s: p / total for s, p in everything.items() if valid(s)}


def rejection_sample(model, valid, kept, seed):
    rng = random.Random(seed)
    counts, draws = {}, 0
    while sum(counts.values()) < kept:
        prefix = ()
        while True:
            tokens, weights = zip(*model[prefix].items(), strict=True)
            token = rng.choices(tokens, weights)[0]
            if token == END:
                break
            prefix = prefix + (token,)
        draws += 1
        if valid(prefix):
            counts[prefix] = counts.get(prefix, 0) + 1
    return {s: c / kept for s, c in counts.items()}, draws


def total_variation(p, q):
    return sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q)) / 2


def rounded(distribution):
    return {"".join(s): round(p, 4) for s, p in sorted(distribution.items())}


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch02-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

In `trap_model(0.99)`, almost every "a" is followed by the invalid "x". Before you run anything, write down:

- the probability of "ay" among valid answers, if the model were conditioned on validity;
- the probability of "ay" under token-by-token masking.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write P(ay) conditioned on validity, and P(ay) under masking.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Masking one step

A server enforcing a schema tracks where the partial answer is in the grammar and, at each step, allows only the tokens that could still lead to a valid answer. Every other logit becomes $-\infty$; softmax gives those tokens zero, and the allowed ones keep their relative odds:

$$
q_i = \frac{p_i\,\mathbf{1}[i \in A]}{\sum_{j \in A} p_j}.
$$

Predict the masked distribution before you run the cell.

```python tags=["foundation", "worked-example"]
intro_probs = {"a": 0.5, "b": 0.3, "c": 0.2}
intro_allowed = {"b", "c"}
intro_total = sum(p for t, p in intro_probs.items() if t in intro_allowed)
print({t: round(p / intro_total, 4) for t, p in intro_probs.items() if t in intro_allowed})
```

### Conditioning is a different operation

Conditioning on validity asks for the whole-sequence probability, restricted to valid sequences:

$$
p(x \mid x \text{ valid}) = \frac{p(x)\,\mathbf{1}[x \text{ valid}]}{P(\text{valid})}.
$$

For `trap_model(t)`, $p(\text{ay}) = 0.9(1 - t)$ and $p(\text{by}) = 0.1$, so conditioning gives $P(\text{ay}) = \frac{0.9(1-t)}{0.9(1-t) + 0.1}$. Masking decides the first token before it can see that "a" rarely ends well. Compute both by hand for $t = 0.99$, then build the masked distribution in general.

```python tags=["foundation", "worked-example"]
print("conditioned, t = 0.99:", rounded(conditioned(trap_model(0.99), is_valid)))
```

## Choose an explicit starting point

This unit starts from Unit A's work. To use your own, replace `None` with the path to your `practical-work/ch02-a/ch02-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import hashlib
import shutil

COURSE_INPUT = COURSE_WORK / "ch02-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_source = (
        "def draft_order(sku, quantity):\n    ...  # Supplied reference: Unit A's tool.\n"
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
```

Unit A's tools refuse a malformed request after it arrives. Constrained decoding stops the malformed request from being written. You need both: the server can guarantee the form, and only your tools can check the meaning.

## Main practical: construct, connect and challenge

## 1. Construct `masked`

`masked(model, valid, viable, prefix=())` must return the distribution over complete sequences that token-by-token masking produces:

- at each prefix, keep `END` only if `valid(prefix)`, and keep another token only if `viable(prefix + (token,))`;
- renormalize the kept tokens' probabilities, and recurse into each kept token;
- raise `ValueError` when no token can be kept, rather than dividing by zero.

The starter below is the colleague's belief: it returns the model conditioned on validity. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch02-masked"]
def masked(model, valid, viable, prefix=()):
    """The distribution that token-by-token constrained decoding produces."""
    return conditioned(model, valid)
```

<details><summary>Hint 1 — one step, then recurse</summary>

Handle one prefix: filter its next-token probabilities, renormalize, and for each kept token either finish (`END`) or call `masked` on the longer prefix, multiplying the probabilities.

</details>

<details><summary>Hint 2 — the two tests</summary>

Finishing needs the sequence so far to be valid; continuing needs the longer prefix to be able to become valid. A prefix like `("a",)` can become valid but is not valid itself.

</details>

```python tags=["assessment", "visible"]
import copy


def outcome(call):
    try:
        return rounded(call())
    except Exception as error:
        return type(error).__name__


THREE_STEP = {
    (): {"p": 0.5, "q": 0.5},
    ("p",): {"r": 0.8, "s": 0.2},
    ("q",): {"r": 1.0},
    ("p", "r"): {"t": 0.5, "u": 0.5},
    ("p", "s"): {"t": 1.0},
    ("q", "r"): {"t": 1.0},
    ("p", "r", "t"): {END: 1.0},
    ("p", "r", "u"): {END: 1.0},
    ("p", "s", "t"): {END: 1.0},
    ("q", "r", "t"): {END: 1.0},
}
THREE_VALID = {("p", "r", "t"), ("p", "s", "t"), ("q", "r", "t")}


def three_viable(prefix):
    return any(v[: len(prefix)] == prefix for v in THREE_VALID)


VISIBLE_CASES = [
    (
        "the trap model",
        lambda: masked(trap_model(0.99), is_valid, can_become_valid),
        {"ay": 0.9, "by": 0.1},
    ),
    (
        "no trap: masking and conditioning agree",
        lambda: masked(trap_model(0.0), is_valid, can_become_valid),
        {"ay": 0.9, "by": 0.1},
    ),
    (
        "three steps",
        lambda: masked(THREE_STEP, lambda s: s in THREE_VALID, three_viable),
        {"prt": 0.5 * 0.8, "pst": 0.5 * 0.2, "qrt": 0.5},
    ),
    (
        "a viability test that lies reaches a dead end",
        lambda: masked(trap_model(1.0), is_valid, lambda prefix: True),
        "ValueError",
    ),
]


def grade(cases):
    rows = []
    for label, call, expected in cases:
        observed = outcome(call)
        if isinstance(expected, dict):
            expected = {k: round(v, 4) for k, v in expected.items()}
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

## 2. Connect: measure the gap as the trap strengthens

The cell below strengthens the trap, $t = 0, 0.5, 0.9, 0.99$. For each $t$ it computes your masked distribution, the conditioned distribution, and a rejection-sampling estimate: sample whole sequences and keep only valid ones. Rejection sampling is an independent check that conditioning is what "restricted to valid answers" means, and it counts how many samples each kept answer cost.

Two requirements:

- Rejection sampling must agree with conditioning within 0.01 at every $t$.
- The **negative control**: at $t = 0$ there is no trap, and the gap between masking and conditioning must be zero. A measurement that shows a gap there is broken.

Predict how the gap grows with $t$.

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:
    table = []
    for t in (0.0, 0.5, 0.9, 0.99):
        model = trap_model(t)
        mask_q = masked(model, is_valid, can_become_valid)
        cond_p = conditioned(model, is_valid)
        sampled, draws = rejection_sample(model, is_valid, kept=20_000, seed=int(t * 100))
        table.append(
            {
                "t": t,
                "masked_ay": round(mask_q[("a", "y")], 4),
                "conditioned_ay": round(cond_p[("a", "y")], 4),
                "rejection_ay": round(sampled.get(("a", "y"), 0.0), 4),
                "draws_per_kept": round(draws / 20_000, 2),
                "total_variation": round(total_variation(mask_q, cond_p), 4),
            }
        )
    sampling_agrees = all(abs(r["rejection_ay"] - r["conditioned_ay"]) < 0.01 for r in table)
    control_zero = table[0]["total_variation"] == 0.0
    connected = {
        "table": table,
        "sampling_agrees": sampling_agrees,
        "negative_control_zero": control_zero,
    }
    for row in table:
        print(row)
    print("rejection sampling matches conditioning:", sampling_agrees)
    print("no gap without a trap:", control_zero)
else:
    print("CONNECTION_NOT_READY — repair masked, then run again.")
```

Masking puts 0.9 on "ay" whatever $t$ is, because it commits to "a" before it can see what follows. Conditioning moves probability to "by" as "a" becomes a worse bet. Rejection sampling follows conditioning, at a cost: at $t = 0.99$ it draws about nine sequences for every one it keeps. This is the trade the chapter describes. Masking is cheap and distorts the distribution; conditioning is faithful and costs $1/P(\text{valid})$ samples per answer.

## Exit ticket

Answer three questions:

- Why does masking put the same probability on "ay" whatever $t$ is?
- Rejection sampling at $t = 0.99$ drew about nine sequences per kept one. Derive that number from $P(\text{valid})$.
- Why must the connection include a model with no trap?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch02-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: retry instead of constraining

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

Without constrained decoding, a client can retry until the answer parses. If each of $n$ tokens independently breaks the format with probability $\epsilon$, one attempt is valid with probability $(1 - \epsilon)^n$. With $k$ independent attempts, at least one is valid with probability

$$
1 - \bigl(1 - (1 - \epsilon)^n\bigr)^k.
$$

Implement `valid_within(per_token_error, tokens, attempts)`:

- return the probability above;
- raise `ValueError` when `per_token_error` lies outside $[0, 1]$, `tokens` is negative, or `attempts` is below 1;
- do not change anything outside the function.

<details><summary>Hint — build it from one attempt</summary>
Compute one attempt's validity first, then the chance that all <code>attempts</code> fail, then its complement.
</details>

```python tags=["exercise", "transfer-owned"]
def valid_within(per_token_error, tokens, attempts):
    raise NotImplementedError("One attempt is valid with (1 - e) ** n; combine attempts")
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("one attempt of 100 tokens", [0.01, 100, 1], round(0.99**100, 6)),
    ("three attempts of 100 tokens", [0.01, 100, 3], round(1 - (1 - 0.99**100) ** 3, 6)),
    ("no errors", [0.0, 500, 1], 1.0),
    ("every token errs", [1.0, 1, 5], 0.0),
    ("zero tokens are always valid", [0.5, 0, 1], 1.0),
    ("a negative error rate is refused", [-0.1, 10, 1], {"raises": "ValueError"}),
    ("zero attempts are refused", [0.1, 10, 0], {"raises": "ValueError"}),
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


transfer_observations = run_transfer(valid_within, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case with an expected value you worked out by hand, and rerun the driver. Then compare the strategies for a 500-token structured answer with a one-in-a-hundred token error rate: how many retries reach 99% validity, and what do they cost in tokens? The chapter measured a real model whose every prompt-only failure was a code fence around good JSON. Explain why that failure is not independent across retries, and what that does to your formula.


## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

These toy models are small enough to enumerate. A real grammar has thousands of allowed tokens per step, and the size of its distortion depends on the model and the schema; the chapter's measurement shows it happens, not how much it matters in general.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch02-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch02-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch02-b",
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
