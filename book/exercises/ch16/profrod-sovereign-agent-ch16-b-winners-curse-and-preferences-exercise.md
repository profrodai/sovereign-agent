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
    lesson_id: improvement
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch16-b-winners-curse-and-preferences-exercise
    self_contained_runtime: true
    source_basis: chapter-16-manuscript
    source_unit: ch16-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch16-b
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

# Chapter 16, Unit B: Predict the winner's curse, then learn from preferences

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-26**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch16/profrod-sovereign-agent-ch16-b-winners-curse-and-preferences-exercise.ipynb) Runs on Google Colab as it ships today (Python 3.13), or on any local Python 3.12+ kernel. It needs nothing beyond Python's standard library, and it makes no network call.

This is the second of Chapter 16's two practical units. Unit A activated a skill only after an evaluation passed. This unit asks how much a passing score can be trusted when it was chosen for being the best.

A colleague tried sixteen versions of Lucy's opening procedure on a thirty-case evaluation, kept the best, and reported its score as "what we can expect in production". You will predict how much that score is inflated, from first principles, and check the prediction against simulation. Then you will build the gradient that turns pairwise preferences into ratings, the core of reward modeling.

By the end you should be able to:

1. Derive the expected maximum of $k$ normal draws, and use it to predict the winner's curse.
2. Check a prediction against simulation, with a single candidate as the negative control.
3. Derive the Bradley–Terry likelihood gradient as wins minus expected wins.
4. Explain why a score chosen for being highest must be re-measured on data the choice never saw.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict the inflation of the colleague's reported score | Written prediction |
| 10–30 | The maximum of $k$ draws, and selection as a maximum | Worked outputs and handoff |
| 30–60 | Construct `expected_max_normal` and pass the visible cases | Learner code and grade table |
| 60–70 | Predict the winner's curse and check it against simulation | Prediction table and negative control |
| 70–85 | Changed-constraint task: the Bradley–Terry gradient | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |

These times are planning estimates, not measured completion times. Run All only checks that the notebook executes; the unfinished student functions deliberately report NEEDS_WORK. Keep your first attempt before you open the answers.


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell supplies:

- `STANDARD`, a standard normal distribution with `.pdf` and `.cdf`;
- `simulate_selection(true_rates, cases, trials, seed)`: scores every candidate on `cases` pass/fail cases, keeps the best, and returns the chosen candidate's average measured score, its average true rate, and their difference, the **optimism**;
- `bradley_terry(r_i, r_j)`, the probability that $i$ is preferred to $j$, and `log_likelihood(comparisons, ratings)`.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch16-b`.

<details><summary>Supplied setup: selection simulator and Bradley–Terry</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import math
import os
import random
import sys
import tempfile
from pathlib import Path
from statistics import NormalDist

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch16-course-"))

STANDARD = NormalDist()


def simulate_selection(true_rates, cases, trials, seed):
    rng = random.Random(seed)
    measured_total = true_total = 0.0
    for _ in range(trials):
        scores = [sum(rng.random() < p for _ in range(cases)) / cases for p in true_rates]
        best = max(range(len(scores)), key=lambda i: (scores[i], -i))
        measured_total += scores[best]
        true_total += true_rates[best]
    return {
        "measured": measured_total / trials,
        "true": true_total / trials,
        "optimism": (measured_total - true_total) / trials,
    }


def bradley_terry(r_i, r_j):
    return 1 / (1 + math.exp(-(r_i - r_j)))


def log_likelihood(comparisons, ratings):
    return sum(math.log(bradley_terry(ratings[w], ratings[loser])) for w, loser in comparisons)


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch16-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

The colleague's sixteen candidates may all be equally good, passing each case half the time. Each scored on thirty cases. Before you run anything, write down:

- the score you expect the best of them to report;
- how that inflation would change with three hundred cases.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write the best candidate's expected score, and how it changes at 300 cases.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Selection is a maximum

A candidate's measured pass rate on $n$ cases is its true rate $p$ plus noise with standard deviation $\sigma = \sqrt{p(1-p)/n}$. Keeping the best of $k$ equally good candidates keeps the largest of $k$ noisy draws. So its measured score exceeds its true rate by about

$$
\text{optimism} \approx \sigma \cdot \mathbb{E}\Bigl[\max_{1 \le i \le k} Z_i\Bigr], \qquad Z_i \sim \mathcal{N}(0, 1).
$$

The maximum of $k$ independent standard normals is at most $x$ exactly when all $k$ are, with probability $\Phi(x)^k$. Differentiating gives its density, $k\,\varphi(x)\,\Phi(x)^{k-1}$. Its mean is the integral of $x$ times that density.

Predict how the largest of $k$ draws grows before you run the simulation.

```python tags=["foundation", "worked-example"]
intro_rng = random.Random(4)
for intro_k in (1, 2, 4, 16):
    intro_draws = [max(intro_rng.gauss(0, 1) for _ in range(intro_k)) for _ in range(20_000)]
    print(intro_k, "draws: average maximum", round(sum(intro_draws) / len(intro_draws), 2))
```

## Choose an explicit starting point

This unit starts from Unit A's work. To use your own, replace `None` with the path to your `practical-work/ch16-a/ch16-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import hashlib
import shutil

COURSE_INPUT = COURSE_WORK / "ch16-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_source = "def change_skill(db, candidate):\n    ...  # Supplied reference.\n"
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

Unit A activates a candidate only after it passes. This unit asks what "passes" means when the candidate was chosen because it scored highest.

## Main practical: construct, connect and challenge

## 1. Construct `expected_max_normal`

`expected_max_normal(k, grid=4000)` must return $\mathbb{E}[\max_{i \le k} Z_i]$ by numerical integration of $x\,k\,\varphi(x)\,\Phi(x)^{k-1}$ from $-8$ to $8$, with the trapezoidal rule on `grid` equal steps. It must raise `ValueError` when `k` is below 1.

The starter below is the large-$k$ approximation $\sqrt{2 \ln k}$. It is right for $k = 1$ and badly wrong for the small $k$ an evaluation meets. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch16-expected-max"]
def expected_max_normal(k, grid=4000):
    """Mean of the largest of k independent standard normal draws."""
    return math.sqrt(2 * math.log(k))
```

<details><summary>Hint 1 — the trapezoidal rule</summary>

Sum the integrand at every grid point, giving the two end points half weight, and multiply by the step width.

</details>

<details><summary>Hint 2 — two exact answers to check against</summary>

For $k = 2$ the answer is $1/\sqrt{\pi}$, and for $k = 3$ it is $3/(2\sqrt{\pi})$. Both come from integrating by parts.

</details>

```python tags=["assessment", "visible"]
import copy


def outcome(call):
    try:
        return round(call(), 4) + 0.0
    except Exception as error:
        return type(error).__name__


VISIBLE_CASES = [
    ("one draw has mean zero", lambda: expected_max_normal(1), 0.0),
    ("two draws: 1 / sqrt(pi)", lambda: expected_max_normal(2), round(1 / math.sqrt(math.pi), 4)),
    (
        "three draws: 3 / (2 sqrt(pi))",
        lambda: expected_max_normal(3),
        round(3 / (2 * math.sqrt(math.pi)), 4),
    ),
    ("zero draws are refused", lambda: expected_max_normal(0), "ValueError"),
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

## 2. Connect: predict the colleague's inflation, then simulate it

The cell below predicts the optimism of the best of sixteen equally good candidates as $\sigma \cdot \mathbb{E}[\max_{16}]$, from your function, at 30, 100 and 300 cases. It then simulates the colleague's procedure 4,000 times at each size.

Two requirements:

- At 100 and 300 cases, the prediction must be within 0.02 of the simulation. At 30 the scores are coarse (steps of 1/30), and the normal approximation is looser.
- The **negative control**: with one candidate there is no selection. Both the prediction and the simulated optimism must be about zero.

Predict the optimism at 30 cases.

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:
    table = []
    for cases in (30, 100, 300):
        sigma = math.sqrt(0.5 * 0.5 / cases)
        predicted = sigma * expected_max_normal(16)
        simulated = simulate_selection([0.5] * 16, cases, 4000, seed=cases)["optimism"]
        table.append(
            {
                "cases": cases,
                "predicted": round(predicted, 3),
                "simulated": round(simulated, 3),
                "reported_score": round(0.5 + simulated, 3),
            }
        )
    close = all(abs(r["predicted"] - r["simulated"]) < 0.02 for r in table if r["cases"] >= 100)
    single = simulate_selection([0.5], 100, 4000, seed=1)["optimism"]
    control = abs(expected_max_normal(1)) < 1e-9 and abs(single) < 0.01
    connected = {"table": table, "prediction_matches": close, "negative_control_zero": control}
    for row in table:
        print(row)
    print("prediction within 0.02 at 100 and 300 cases:", close)
    print("one candidate, no optimism:", control, round(single, 4))
else:
    print("CONNECTION_NOT_READY — repair expected_max_normal, then run again.")
```

The colleague's thirty-case winner reports a score of about 0.66 for candidates that are all 0.5. At three hundred cases the inflation is still about five points. More cases shrink the curse as $1/\sqrt{n}$, and more candidates grow it as $\mathbb{E}[\max_k]$; nothing but a fresh holdout removes it.

## Exit ticket

Answer three questions:

- Why does keeping the best of sixteen equal candidates produce a score above their shared true rate?
- Which way does the inflation move with more cases, and with more candidates?
- What must the colleague do before calling the winner's score "what we can expect"?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch16-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: the Bradley–Terry gradient

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

For open-ended outputs, labs collect preferences: of two answers, which is better? Bradley–Terry gives each item a rating $r_i$ and models $P(i \succ j) = \sigma(r_i - r_j)$. For (winner, loser) pairs, the log likelihood is $\sum \log \sigma(r_w - r_\ell)$, and its derivative for item $i$ is

$$
\frac{\partial \log L}{\partial r_i} = \sum_{\text{comparisons with } i} \bigl(\mathbf{1}[i \text{ won}] - P(i \text{ wins})\bigr),
$$

actual wins minus expected wins. A reward model is trained on exactly this signal.

Implement `bt_gradient(comparisons, ratings)`:

- `comparisons` is a list of `(winner, loser)` index pairs; `ratings` a list of floats;
- return the gradient as a list, one entry per rating;
- raise `ValueError` for an index outside the ratings, or an item compared with itself;
- do not change the inputs.

<details><summary>Hint — each comparison touches two items</summary>
For a pair with winner <code>w</code> and loser <code>l</code>, let <code>p</code> be the probability that <code>w</code> wins. The winner gains <code>1 - p</code>; the loser loses the same amount.
</details>

```python tags=["exercise", "transfer-owned"]
def bt_gradient(comparisons, ratings):
    raise NotImplementedError("For each pair, add wins minus expected wins to both items")
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("one win between equals", [[(0, 1)], [0.0, 0.0]], [0.5, -0.5]),
    ("one win each way", [[(0, 1), (1, 0)], [0.0, 0.0]], [0.0, 0.0]),
    ("an expected win teaches less", [[(0, 1)], [math.log(3), 0.0]], [0.25, -0.25]),
    ("three items", [[(0, 1), (0, 2), (2, 1)], [0.0, 0.0, 0.0]], [1.0, -1.0, 0.0]),
    ("an item without a rating is refused", [[(0, 3)], [0.0, 0.0]], {"raises": "ValueError"}),
    ("an item against itself is refused", [[(1, 1)], [0.0, 0.0]], {"raises": "ValueError"}),
]


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        try:
            actual = [round(x, 6) + 0.0 for x in candidate(*supplied)]
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


transfer_observations = run_transfer(bt_gradient, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case with an expected value you worked out by hand, and rerun the driver. Then fit ratings: start from zeros, repeatedly add a small multiple of your gradient, and re-center to mean zero. Use preferences sampled from ratings you choose, and check that the fit recovers them. Finally, explain what a preference grader that always favors the longer answer would teach a model trained against it.


## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

These simulations assume equally good candidates and independent cases. Real candidates differ, and when one is truly much better the curse is smaller; the chapter's measured prompt search is an example.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch16-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch16-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch16-b",
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
