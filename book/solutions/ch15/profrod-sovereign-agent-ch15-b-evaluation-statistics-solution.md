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
    instructor: true
    lesson_id: evaluation
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch15-b-evaluation-statistics-solution
    self_contained_runtime: true
    source_basis: chapter-15-manuscript
    source_unit: ch15-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch15-b
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

# Chapter 15, Unit B: Put error bars on an evaluation

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-26**

This is the worked edition of Chapter 15, Unit B. It contains:

- complete answers;
- the instructor explanation;
- holdout cases that the student edition does not show.

Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, using only the standard library.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what 16 of 16 can and cannot establish | Written prediction |
| 10–30 | Standard error, Wald, and your Unit A baseline on 200 cases | Worked outputs and handoff |
| 30–60 | Construct `wilson_interval` and pass the visible cases | Learner code and grade table |
| 60–70 | Check your interval's exact coverage against Wald's | Coverage table and negative control |
| 70–85 | Changed-constraint task: McNemar's paired test | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell supplies four tools:

- `wald_interval`: the textbook interval, the one you will test and replace;
- `exact_coverage`: the probability that an interval contains the true pass rate, computed exactly from the binomial distribution;
- `generate_cases`: random stock cases, each with an independently computed expected answer;
- `simulate_pair`: paired results for two candidates with pass rates and a disagreement rate you choose.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch15-b`.

<details><summary>Supplied setup: intervals, coverage and simulators</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import math
import os
import random
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch15-course-"))

Z95 = 1.959963984540054  # leaves 2.5% of a standard normal distribution in each tail


@dataclass(frozen=True)
class Case:
    name: str
    split: str
    # SKU, physical stock, reserved stock, threshold, unit price in cents.
    stock: tuple
    expected: tuple
    prompt: str = "Prepare a replenishment draft from current stock."


def wald_interval(successes, trials, z=Z95):
    """p-hat plus or minus z standard errors, with the error estimated at p-hat."""
    phat = successes / trials
    half = z * math.sqrt(phat * (1 - phat) / trials)
    return (max(0.0, phat - half), min(1.0, phat + half))


def exact_coverage(interval, p, trials):
    """P(interval contains p): sum the binomial probability of every outcome whose interval does."""
    total = 0.0
    for successes in range(trials + 1):
        low, high = interval(successes, trials)
        if low <= p <= high:
            total += math.comb(trials, successes) * p**successes * (1 - p) ** (trials - successes)
    return total


def generate_cases(count, seed):
    """Random catalogs; each expected draft is computed here, independently of any candidate."""
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        rows = []
        for sku in rng.sample(["V", "S", "C", "M", "P", "L"], rng.randint(0, 4)):
            physical = rng.randint(0, 12)
            rows.append((sku, physical, rng.randint(0, physical), rng.randint(0, 12), 250))
        expected = tuple(
            (sku, target - (physical - reserved))
            for sku, physical, reserved, target, _ in rows
            if target > physical - reserved
        )
        cases.append(Case(f"generated-{index}", "generated", tuple(rows), expected))
    return cases


def simulate_pair(cases, p_first, p_second, discordant, seed):
    """Paired pass/fail results for two candidates on the same cases.

    Each case falls into one of four cells: both pass, only the first, only the second, neither.
    The first and second pass rates, and the share of cases on which they disagree, set the cells.
    """
    only_first = (discordant + p_first - p_second) / 2
    only_second = (discordant - p_first + p_second) / 2
    both = p_first - only_first
    if min(only_first, only_second, both, 1 - both - discordant) < 0:
        raise ValueError("these rates cannot occur together")
    rng = random.Random(seed)
    first, second = [], []
    for _ in range(cases):
        u = rng.random()
        first.append(u < both + only_first)
        second.append(u < both or both + only_first <= u < both + discordant)
    return first, second


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch15-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

The agent passed 16 of 16 evaluation cases. Before you run anything, write down:

- the lowest true pass rate you think is still consistent with that result;
- how many clean runs you would need before claiming a failure rate below 1%.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write the lowest pass rate consistent with 16/16, and the runs needed for 1%.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### A pass rate is an estimate

Treat each case as a trial that passes with an unknown probability $p$. After $n$ trials with $k$ passes, the estimate is $\hat p = k/n$, and its **standard error** is $\sqrt{p(1-p)/n}$: the typical distance between $\hat p$ and $p$ across repeated suites of $n$ cases.

The **Wald interval** plugs $\hat p$ in for the unknown $p$ and reports $\hat p \pm 1.96\,\text{SE}$. Predict what it reports for 16 of 16 before you run the cell.

```python tags=["foundation", "worked-example"]
for intro_k, intro_n in ((16, 16), (15, 16), (8, 16)):
    intro_low, intro_high = wald_interval(intro_k, intro_n)
    print(f"{intro_k}/{intro_n}: Wald [{intro_low:.3f}, {intro_high:.3f}]")
```

At 16 of 16 the estimated standard error is zero, and Wald claims certainty: the interval is the single point 1. Sixteen runs cannot show that an agent never fails.

**The rule of three** gives a quick check. If the true failure rate were $3/n$, the chance of $n$ clean runs would be $(1 - 3/n)^n \approx e^{-3} \approx 0.05$. So after $n$ clean runs, failure rates above about $3/n$ are ruled out at 95%, and those below it are not. For sixteen runs, that is about 19%.

### Invert the test instead of plugging in

The better question is: for which values of $p$ would the observed $\hat p$ lie within $z$ standard errors, with the standard error computed **at that $p$**, not at $\hat p$?

$$
|\hat p - p| \le z\sqrt{\frac{p(1-p)}{n}}.
$$

Square both sides. The result is a quadratic inequality in $p$, and its two roots bound the **Wilson interval**:

$$
\frac{\hat p + \frac{z^2}{2n}}{1 + \frac{z^2}{n}} \;\pm\; \frac{z}{1 + \frac{z^2}{n}}\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}.
$$

At 16 of 16 the square root is still positive, so the interval has width.

## Choose an explicit starting point

This unit starts from Unit A's baseline. To use your own, replace `None` with the path to your `practical-work/ch15-a/ch15-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import hashlib
import shutil

COURSE_INPUT = COURSE_WORK / "ch15-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_source = '''
def baseline(case: Case) -> list[tuple[str, int]]:
    """Supplied reference: Unit A's baseline."""
    return [
        (sku, threshold - stock + reserved)
        for sku, stock, reserved, threshold, _ in case.stock
        if stock - reserved < threshold
    ]
'''
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
unit_a_namespace = {"Case": Case}
if handoff_status == "VERIFIED":
    exec(handoff["implementation"], unit_a_namespace)
unit_a_baseline = unit_a_namespace.get("baseline")

GENERATED = generate_cases(200, seed=15)
unit_a_passed = 0
if unit_a_baseline is not None:
    unit_a_passed = sum(
        sorted(unit_a_baseline(case)) == sorted(case.expected) for case in GENERATED
    )
print("Unit A's baseline on 200 generated cases:", unit_a_passed, "/ 200")
```

Your Unit A baseline is a deterministic calculation, and it passed the generated cases printed above. Once your Wilson interval works, the connection below asks what those 200 clean runs can claim.

## Main practical: construct, connect and challenge

## 1. Construct `wilson_interval`

`wilson_interval(successes, trials, z=Z95)` must return the pair `(low, high)` given by the formula above. It must also:

- clip the pair to $[0, 1]$;
- raise `ValueError` when `trials` is not positive, or `successes` lies outside `0..trials`.

The starter below returns the Wald interval instead. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch15-wilson-interval"]
def wilson_interval(successes, trials, z=Z95):
    """95% interval for a pass rate: every p consistent with the observed rate."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("need trials > 0 and 0 <= successes <= trials")
    phat = successes / trials
    denominator = 1 + z * z / trials
    center = (phat + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(phat * (1 - phat) / trials + z * z / (4 * trials * trials)) / denominator
    return (max(0.0, center - half), min(1.0, center + half))
```

<details><summary>Hint 1 — the two pieces</summary>

Compute the center and the half-width separately. Both share the denominator $1 + z^2/n$.

</details>

<details><summary>Hint 2 — the refusals</summary>

Check the arguments before dividing. Zero trials would divide by zero; more successes than trials would make $\hat p(1 - \hat p)$ negative.

</details>

```python tags=["assessment", "visible"]
import copy


def outcome(call):
    try:
        return tuple(round(x, 3) + 0.0 for x in call())
    except Exception as error:
        return type(error).__name__


VISIBLE_CASES = [
    ("sixteen of sixteen", lambda: wilson_interval(16, 16), (0.806, 1.0)),
    ("twenty-six of twenty-eight", lambda: wilson_interval(26, 28), (0.774, 0.98)),
    ("none of ten", lambda: wilson_interval(0, 10), (0.0, 0.278)),
    ("half of ten is symmetric", lambda: wilson_interval(5, 10), (0.237, 0.763)),
    ("no trials", lambda: wilson_interval(0, 0), "ValueError"),
    ("more successes than trials", lambda: wilson_interval(11, 10), "ValueError"),
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

## 2. Connect: does your interval keep its promise?

A "95% interval" promises to contain the true pass rate 95% of the time. That promise can be checked exactly. For a true rate $p$ and $n$ cases, every outcome $k$ has binomial probability $\binom{n}{k}p^k(1-p)^{n-k}$. Sum it over the outcomes whose interval contains $p$:

$$
\text{coverage}(p, n) = \sum_{k=0}^{n} \binom{n}{k} p^{k}(1-p)^{n-k}\,\mathbf{1}\bigl[p \in \text{CI}(k)\bigr].
$$

The cell below computes the exact coverage of your interval and of Wald's for a 16-case suite. Your interval must stay above 0.92 wherever $p \le 0.95$. Wald is the **negative control**: the check must reject it, or the check proves nothing.

It then applies your interval to Unit A's 200 generated cases.

Predict Wald's coverage for an agent whose true pass rate is 95%.

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:
    table = []
    for p in (0.5, 0.9, 0.95, 0.99):
        table.append(
            {
                "p": p,
                "yours": round(exact_coverage(wilson_interval, p, 16), 3),
                "wald": round(exact_coverage(wald_interval, p, 16), 3),
            }
        )
    keeps_promise = all(row["yours"] > 0.92 for row in table if row["p"] <= 0.95)
    control_rejected = any(row["wald"] < 0.9 for row in table if row["p"] <= 0.95)
    unit_a_low, unit_a_high = wilson_interval(unit_a_passed, len(GENERATED))
    connected = {
        "coverage_n16": table,
        "keeps_promise": keeps_promise,
        "negative_control_rejected": control_rejected,
        "unit_a_interval": [round(unit_a_low, 4), round(unit_a_high, 4)],
    }
    for row in table:
        print(row)
    print("your interval keeps its promise:", keeps_promise)
    print("Wald rejected:", control_rejected)
    print(
        f"Unit A baseline, {unit_a_passed}/{len(GENERATED)}:",
        f"pass rate between {unit_a_low:.4f} and {unit_a_high:.4f}",
    )
else:
    print("CONNECTION_NOT_READY — repair wilson_interval, then run again.")
```

Read the $p = 0.95$ row. The Wald interval that claims 95% contains the truth only about half the time, for exactly the kind of agent we most want to measure. Now read the $p = 0.99$ row: at sixteen cases, no interval can be precise about a 1% failure rate, and even yours falls short there. The remedy is more cases, not a cleverer formula.

The last line is your Unit A baseline. Two hundred clean runs of a deterministic calculation still bound its pass rate only above about 98%, not at 100%. A finite suite can show that a failure is rare. It cannot show that failure is impossible.

## Exit ticket

Answer three questions:

- Why does the Wald interval collapse at 16 of 16, and what does the Wilson interval do differently?
- The agent was tried twice on each of fourteen cases, for 28 attempts. Why is 28 the wrong $n$ for the interval?
- Why must a check of an interval's coverage include an interval that it rejects?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch15-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: compare two candidates on the same cases

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

The colleague's second claim compared a new prompt, 12 of 14, with the old one, 10 of 14, on the same fourteen cases. Subtracting the two scores throws away the pairing. Cases that both prompts pass, or both fail, say nothing about which is better. The evidence is in the **discordant** cases: $b$ where only the first passes, and $c$ where only the second does.

If the two candidates were equally good, each discordant case would favor either one with probability one half. So the smaller of $b$ and $c$ is the lower tail of a Binomial$(b + c, \tfrac12)$, and the exact two-sided p-value is

$$
P = \min\!\Bigl(1,\; 2\sum_{i=0}^{\min(b,c)} \binom{b+c}{i}\, 2^{-(b+c)}\Bigr).
$$

This is **McNemar's exact test**. Implement `mcnemar(first, second)`:

- `first` and `second` are lists of booleans, one per case, in the same order;
- return the p-value above, and 1.0 when there are no discordant cases;
- raise `ValueError` when the lists are empty or have different lengths;
- do not change the inputs.

<details><summary>Hint — the counts</summary>
<code>b</code> counts positions where <code>first</code> is true and <code>second</code> is false; <code>c</code> the reverse. <code>math.comb(m, i)</code> is the binomial coefficient.
</details>

```python tags=["exercise", "transfer-owned"]
def mcnemar(first, second):
    if not first or len(first) != len(second):
        raise ValueError("need two nonempty result lists of the same length")
    b = sum(x and not y for x, y in zip(first, second, strict=True))
    c = sum(y and not x for x, y in zip(first, second, strict=True))
    if b + c == 0:
        return 1.0
    tail = sum(math.comb(b + c, i) for i in range(min(b, c) + 1))
    return min(1.0, 2 * tail / 2 ** (b + c))
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("one disagreement each way", [[True, True, False, False], [True, False, False, True]], 1.0),
    ("six to nothing", [[True] * 6, [False] * 6], 0.03125),
    ("agreement carries no evidence", [[True, True, False], [True, True, False]], 1.0),
    ("seven to one", [[True] * 7 + [False], [False] * 7 + [True]], round(9 / 128, 6)),
    ("different lengths are refused", [[True], [True, False]], {"raises": "ValueError"}),
    ("no cases are refused", [[], []], {"raises": "ValueError"}),
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


transfer_observations = run_transfer(mcnemar, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case with an expected value you worked out by hand, and rerun the driver. Then test the colleague's claim and size the experiment that could settle it:

- The two prompts disagreed on four cases: the new one alone passed three, and the old one alone passed one. Compute McNemar's p-value. Is a 14-point difference on fourteen cases evidence?
- Use `simulate_pair(14, 0.85, 0.80, 0.10, seed)` for 200 seeds, and count how often your `mcnemar` returns $p < 0.05$. That share is the test's **power** on fourteen cases. Repeat with 312 cases.

Explain what a fourteen-case suite is good for, and what it is not.


## Instructor explanation and additional transfer cases

Three misconceptions come up.

**"16 of 16 means 100%."** It means the failure rate is probably below about 19%. Error bars are widest, relative to what is left to improve, exactly when a system looks perfect. That is why careful evaluations report intervals on near-saturated benchmarks.

**"12 of 14 against 10 of 14 is a 14-point improvement."** The candidates disagree on only four cases, and three to one gives $p = 0.625$. Pairing is still the right analysis. It is more powerful than comparing two independent scores, because the shared difficulty of each case cancels. But there is almost nothing here to analyze. The holdout below simulates a real five-point improvement with 10% disagreement: in 200 suites of fourteen cases, McNemar never detected it, and at 312 cases, the size Chapter 15's formula gives for 80% power, it detected it 78% of the time.

**"Repeat each case to get a bigger n."** Repeats measure a model's variability on one case; they do not add cases. In the chapter's retained run, all fourteen cases gave the same result on both repeats, so 28 attempts carried the information of fourteen.

The cases below check that concordant cases change nothing, and that the direction of the difference does not matter.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    ("added agreement changes nothing", [[True] * 26, [False] * 6 + [True] * 20], 0.03125),
    ("direction does not matter", [[False] * 6, [True] * 6], 0.03125),
]
instructor_observations = run_transfer(mcnemar, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
import itertools

for holdout_k, holdout_n in ((3, 10), (26, 28), (1, 50)):
    for holdout_p in wilson_interval(holdout_k, holdout_n):
        assert math.isclose(
            abs(holdout_k / holdout_n - holdout_p),
            Z95 * math.sqrt(holdout_p * (1 - holdout_p) / holdout_n),
            rel_tol=1e-9,
        )
assert connected is not None and connected["keeps_promise"]
assert connected["negative_control_rejected"]
for holdout_b, holdout_c in ((1, 7), (0, 5), (4, 6)):
    holdout_m = holdout_b + holdout_c
    extreme = sum(
        min(sum(signs), holdout_m - sum(signs)) <= min(holdout_b, holdout_c)
        for signs in itertools.product((0, 1), repeat=holdout_m)
    )
    assert math.isclose(
        mcnemar([True] * holdout_b + [False] * holdout_c, [False] * holdout_b + [True] * holdout_c),
        min(1.0, extreme / 2**holdout_m),
    )
power = {}
for holdout_cases in (14, 312):
    detected = sum(
        mcnemar(*simulate_pair(holdout_cases, 0.85, 0.80, 0.10, seed)) < 0.05 for seed in range(200)
    )
    power[holdout_cases] = detected / 200
print("power to detect 85% against 80%, 10% disagreement:", power)
assert power[14] < 0.1 and power[312] > 0.7
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch15-b"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit's intervals assume independent cases drawn from the population you care about. A suite of hand-written cases is not a random sample of Lucy's future requests, and no interval corrects for that.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch15-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch15-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch15-b",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "instructor",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
<!-- #endregion -->
