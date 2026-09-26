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
    lesson_id: agent-loop
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch03-b-reliability-and-retries-solution
    self_contained_runtime: true
    source_basis: chapter-3-manuscript
    source_unit: ch03-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch03-b
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

# Chapter 3, Unit B: Test a reliability claim against simulation

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-26**

This is the worked edition of Chapter 3, Unit B. It contains:

- complete answers;
- the instructor explanation;
- holdout cases that the student edition does not show.

Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, using only the standard library.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what recovery does to a 20-step task | Written prediction |
| 10–30 | Compounding, half-life and the recovery chain | Worked outputs and handoff |
| 30–60 | Construct `success_with_recovery` and pass the visible cases | Learner code and grade table |
| 60–70 | Test your formula against a simulated agent | z-score table and negative control |
| 70–85 | Changed-constraint task: are retries independent? | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell supplies two simulators. Each is a stand-in for a model whose true rates you set, so that every formula can be checked against the truth:

- `simulate_on_track` runs an agent step by step. On track, a step keeps it on track with probability `p`; off track, a step brings it back with probability `r`.
- `simulate_retries` attempts tasks repeatedly. A fraction `hard` of tasks can never be solved; the rest are solved with probability `q` per attempt.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch03-b`.

<details><summary>Supplied setup: the two simulators</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import math
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
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch03-course-"))


def simulate_on_track(p, r, n, runs, seed):
    """Run `runs` agents for n steps from on track; return how many end on track."""
    rng = random.Random(seed)
    ended_on_track = 0
    for _ in range(runs):
        on_track = True
        for _ in range(n):
            on_track = rng.random() < (p if on_track else r)
        ended_on_track += on_track
    return ended_on_track


def simulate_retries(q, hard, instances, attempts, seed):
    """Attempt each task until it succeeds or `attempts` run out; one list of outcomes per task."""
    rng = random.Random(seed)
    outcomes = []
    for _ in range(instances):
        is_hard = rng.random() < hard
        tries = []
        while len(tries) < attempts and not any(tries):
            tries.append(not is_hard and rng.random() < q)
        outcomes.append(tries)
    return outcomes


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch03-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

Lucy's loop shows every tool refusal to the model, so a step that goes wrong can be repaired on the next step. Suppose each step stays on track 95% of the time, and a step taken while off track gets back on track 30% of the time.

Before you run anything, write down:

- the probability that a 20-step task ends on track, compared with the colleague's 36%;
- what happens to that probability as the task grows to 50, then 500, steps.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write your estimate for 20 steps, and what happens as the task grows.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Reliability compounds

If each of $n$ steps succeeds independently with probability $p$, and the task needs all of them, the task succeeds with probability $p^{n}$. The number of steps after which success falls to one half is the **half-life**: solving $p^{n} = \tfrac12$ gives $n_{1/2} = \ln 2 / (-\ln p) \approx 0.69 / (1 - p)$. Predict the half-life at 95% and at 99% before you run the cell.

```python tags=["foundation", "worked-example"]
for intro_p in (0.99, 0.95, 0.90):
    intro_row = [round(intro_p**intro_n, 3) for intro_n in (1, 5, 10, 20, 50)]
    intro_half_life = math.log(2) / -math.log(intro_p)
    print(intro_p, intro_row, "half-life", round(intro_half_life, 1), "steps")
```

**Halving the error rate doubles the length of task an agent can do.** That is why per-step error, not headline accuracy, decides whether an agent can do long work.

### Recovery is a two-state Markov chain

The colleague's $p^{n}$ assumes one error ends the task. In Lucy's loop it does not. Model the loop with two states:

- **on track:** the next step stays on track with probability $p$;
- **off track:** the next step recovers with probability $r$.

Let $a_k$ be the probability of being on track after $k$ steps, with $a_0 = 1$. Being on track after step $k+1$ happens in two ways: on track and staying, or off track and recovering. So

$$
a_{k+1} = p\,a_k + r\,(1 - a_k) = r + (p - r)\,a_k.
$$

The cell below iterates this recurrence directly. It is slow and exact, and you will use it to check the closed form you are about to derive.

```python tags=["foundation", "worked-example"]
def on_track_by_recurrence(p, r, n):
    probability = 1.0
    for _ in range(n):
        probability = r + (p - r) * probability
    return probability


for intro_r in (0.0, 0.3, 0.8):
    print(intro_r, [round(on_track_by_recurrence(0.95, intro_r, n), 3) for n in (1, 10, 20, 50)])
```

With $r = 0$ the recurrence gives back $p^{n}$. With any $r > 0$, the probability stops falling toward zero and levels off. Find that level: it is the **fixed point** $\pi$ with $\pi = r + (p - r)\,\pi$. Then notice that the distance from it shrinks by the same factor every step, $a_{k+1} - \pi = (p - r)(a_k - \pi)$. Those two facts give the closed form you will construct.

## Choose an explicit starting point

This unit starts from Unit A's bounded transcript. To use your own, replace `None` with the path to your `practical-work/ch03-a/ch03-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import shutil

COURSE_INPUT = COURSE_WORK / "ch03-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_handoff = {
        "status": "COMPLETED",
        "model_calls": 3,
        "tool_calls": 3,
        "estimated_cents": 6,
        "answer": "Supplied reference: Unit A's authored three-turn transcript.",
        "messages": [],
    }
    COURSE_INPUT.write_text(json.dumps(reference_handoff, indent=2, sort_keys=True) + "\n")
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
```

```python tags=["setup", "handoff-consumer"]
handoff = json.loads(COURSE_INPUT.read_text(encoding="utf-8"))
handoff_status = "VERIFIED" if handoff.get("status") == "COMPLETED" else "INVALID"
unit_a_steps = handoff.get("model_calls", 0)
print("UNIT_A_HANDOFF", handoff_status)
print("Unit A's loop finished in", unit_a_steps, "model calls")
```

Unit A's loop reached its answer in the number of model calls printed above. Each call is a step in the sense of this chapter. At 95% per step, with no recovery, a run of that length would finish on track with probability $0.95^{n}$. Keep that number; the connection below extends it.

## Main practical: construct, connect and challenge

## 1. Construct `success_with_recovery`

`success_with_recovery(p, r, n)` must return $a_n$, the probability of being on track after `n` steps from on track, in closed form:

$$
a_n = \pi + (1 - \pi)(p - r)^{n}, \qquad \pi = \frac{r}{1 - p + r}.
$$

It must also:

- raise `ValueError` when `p` or `r` lies outside $[0, 1]$, or `n` is negative;
- handle the one case where the formula divides by zero. Work out which case that is, and what the answer must be there.

The starter below returns the colleague's number instead. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch03-success-with-recovery"]
def success_with_recovery(p, r, n):
    """Probability of being on track after n steps, starting on track."""
    if not (0 <= p <= 1 and 0 <= r <= 1) or n < 0:
        raise ValueError("p and r must be probabilities, and n at least 0")
    if p == 1 and r == 0:
        return 1.0
    stationary = r / (1 - p + r)
    return stationary + (1 - stationary) * (p - r) ** n
```

<details><summary>Hint 1 — the fixed point</summary>

Solve $\pi = r + (p - r)\pi$ for $\pi$: collect the $\pi$ terms to get $\pi(1 - p + r) = r$.

</details>

<details><summary>Hint 2 — the division by zero</summary>

$1 - p + r = 0$ only when $p = 1$ and $r = 0$: a step that never fails. An agent that starts on track then stays on track forever, so the answer is 1 for every $n$.

</details>

```python tags=["assessment", "visible"]
import copy


def outcome(call):
    try:
        return round(call(), 6)
    except Exception as error:
        return type(error).__name__


VISIBLE_CASES = [
    ("no recovery is p to the n", lambda: success_with_recovery(0.9, 0.0, 3), 0.729),
    ("one step is p", lambda: success_with_recovery(0.95, 0.3, 1), 0.95),
    ("zero steps: still on track", lambda: success_with_recovery(0.9, 0.5, 0), 1.0),
    (
        "a long task settles at the fixed point",
        lambda: success_with_recovery(0.95, 0.3, 50),
        round(0.3 / 0.35, 6),
    ),
    ("a perfect step never fails", lambda: success_with_recovery(1.0, 0.0, 10), 1.0),
    ("a probability above one", lambda: success_with_recovery(1.2, 0.0, 3), "ValueError"),
    ("a negative step count", lambda: success_with_recovery(0.9, 0.3, -1), "ValueError"),
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

## 2. Connect: test your formula against a simulated agent

Passing seven hand-picked cases is not evidence that a formula describes a process. The cell below runs 20,000 simulated agents for each setting and compares the share that ended on track, $\hat a$, with your formula's $a$. If the formula is right, $\hat a$ differs from $a$ only by sampling noise, with standard error $\sqrt{a(1 - a)/N}$. The **z-score** $z = (\hat a - a)/\text{SE}$ measures the difference in those units; $|z| > 4$ would happen by chance less than once in ten thousand.

A test that cannot fail proves nothing. So the cell also runs a **negative control**: the colleague's $p^{n}$, which ignores recovery. The test must reject it wherever $r > 0$.

Predict the largest $|z|$ for your formula, and for the colleague's.

```python tags=["integration", "learner-path"]
connected = None
SETTINGS = [(0.95, 0.0, 20), (0.95, 0.3, 20), (0.9, 0.3, 10), (0.9, 0.6, 5), (0.8, 0.5, 30)]
RUNS = 20_000


def z_score(observed_share, predicted, runs):
    return (observed_share - predicted) / math.sqrt(predicted * (1 - predicted) / runs)


if VISIBLE_PASSED:
    table = []
    for index, (p, r, n) in enumerate(SETTINGS):
        share = simulate_on_track(p, r, n, RUNS, seed=1000 + index) / RUNS
        table.append(
            {
                "p": p,
                "r": r,
                "n": n,
                "simulated": round(share, 4),
                "formula": round(success_with_recovery(p, r, n), 4),
                "z_formula": round(z_score(share, success_with_recovery(p, r, n), RUNS), 2),
                "colleague_p_to_n": round(p**n, 4),
                "z_colleague": round(z_score(share, p**n, RUNS), 1),
            }
        )
    formula_fits = all(abs(row["z_formula"]) < 4 for row in table)
    control_rejected = any(abs(row["z_colleague"]) > 4 for row in table if row["r"] > 0)
    connected = {
        "table": table,
        "formula_fits": formula_fits,
        "negative_control_rejected": control_rejected,
        "unit_a_run_on_track": round(success_with_recovery(0.95, 0.3, unit_a_steps), 4),
    }
    for row in table:
        print(row)
    print("formula consistent with simulation:", formula_fits)
    print("negative control rejected:", control_rejected)
    print(
        f"Unit A's {unit_a_steps}-call run: {0.95**unit_a_steps:.4f} without recovery,",
        f"{connected['unit_a_run_on_track']} with r = 0.3",
    )
else:
    print("CONNECTION_NOT_READY — repair success_with_recovery, then run again.")
```

Read the $r = 0$ row: there the colleague's formula and yours agree, and both fit. Everywhere else the colleague's is rejected by 77 standard errors or more. The rate $r$ is not a property of the model alone. It is set by the loop: a tool that returns a clear refusal, shown to the model, raises it; a failure the model never sees keeps it at zero.

## Exit ticket

Answer three questions:

- Why does success with recovery level off at $\pi$ instead of falling to zero?
- What in Lucy's loop sets $r$, and what change to a tool would lower it to zero?
- Why must a test of a formula include a case the test should reject?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch03-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: are retries independent?

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

The colleague's second number, 74% within three attempts, assumes that attempts are independent: a failed attempt is followed by a success with the same probability as the first attempt. If some tasks are hard for this model, that is false. The failed attempts are concentrated on the hard tasks, and retrying them succeeds less often.

You can measure this from retry data. Implement `retry_after_failure(outcomes)`:

- `outcomes` has one list per task: the result of each attempt in order, `True` for success, stopping at the first success;
- among the tasks whose first attempt failed **and** that have a second attempt, return the share whose second attempt succeeded;
- raise `ValueError` for an empty list, for a task with no attempts, for an attempt recorded after a success, or when no task has a failed first attempt followed by a second;
- do not change the input.

Under independence the result equals the first-attempt success rate. Well below it means a hard fraction.

<details><summary>Hint — which tasks count</summary>
A task like <code>[False]</code> failed once and was never retried: it tells you nothing about retries, so it is left out of both the numerator and the denominator.
</details>

```python tags=["exercise", "transfer-owned"]
def retry_after_failure(outcomes):
    if not outcomes:
        raise ValueError("no tasks")
    for tries in outcomes:
        if not tries or any(tries[:-1]):
            raise ValueError("each task needs attempts that stop at the first success")
    retried = [tries[1] for tries in outcomes if len(tries) >= 2]
    if not retried:
        raise ValueError("no task was retried after a failure")
    return sum(retried) / len(retried)
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("one of two retries succeeds", [[[True], [False, True], [False, False]]], 0.5),
    ("every retry succeeds", [[[False, True], [False, True], [True], [True]]], 1.0),
    ("no retry succeeds", [[[False, False, True], [False, False]]], 0.0),
    ("an empty list is refused", [[]], {"raises": "ValueError"}),
    ("an attempt after a success is refused", [[[True, False]]], {"raises": "ValueError"}),
    ("nothing was retried", [[[True], [False]]], {"raises": "ValueError"}),
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


transfer_observations = run_transfer(retry_after_failure, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case with an expected value you worked out by hand, and rerun the driver. Then apply your function to data:

- `simulate_retries(0.6, 0.0, 4000, 4, seed=11)`: no hard tasks. Compare the retry rate with the first-attempt rate.
- `simulate_retries(0.6, 0.3, 4000, 4, seed=11)`: 30% hard. Predict the retry rate before you run it. Of the tasks that fail first, what share are hard?
- The chapter's measured run: 40 tasks at temperature 0.8, 14 solved on the first attempt, and 4 of the other 26 solved on the second. Compare 4/26 with 14/40.

Explain which reliability number the colleague should have reported, and how they could have measured it.


## Instructor explanation and additional transfer cases

Three misconceptions come up.

**"95% per step means 36% over 20 steps, full stop."** Only if one error ends the task. With recovery, success levels off at $\pi = r/(1 - p + r)$, which is 86% at $p = 0.95, r = 0.3$. The difference between the two numbers is made by the loop, not the model. That is the practical content of this unit: make errors visible and recoverable.

**"The simulation agreed, so the formula is proven."** The simulation shows the formula describes *the simulator*. The simulator's steps are identical and memoryless; a real agent's are not. The chapter's measured run found errors concentrated in one step, the final sum, whose difficulty grows with $n$. A formula can be exactly right about its model and wrong about the world. Measure where the errors are before choosing the model.

**"More retries always converge to 100%."** Only with no hard tasks. With a hard fraction $h$, success within $k$ attempts converges to $1 - h$. The retry-after-failure rate is how you see $h$ in data. On the simulated 30%-hard tasks it falls to 0.28, against 0.43 first time: of the 57% that fail first, about half are hard.

The cases below add a task that failed once without a retry, and a mixture.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    ("a task never retried is left out", [[[False], [False], [False, True]]], 1.0),
    ("a mixture", [[[False, True], [False, False, False], [False, False], [True]]], 0.333333),
]
instructor_observations = run_transfer(retry_after_failure, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
for holdout_p, holdout_r, holdout_n in [
    (0.7, 0.2, 7),
    (0.99, 0.01, 100),
    (0.5, 0.5, 3),
    (0.0, 1.0, 4),
]:
    assert math.isclose(
        success_with_recovery(holdout_p, holdout_r, holdout_n),
        on_track_by_recurrence(holdout_p, holdout_r, holdout_n),
        abs_tol=1e-12,
    )
assert connected is not None and connected["formula_fits"]
assert connected["negative_control_rejected"]
independent = simulate_retries(0.6, 0.0, 4000, 4, seed=11)
with_hard = simulate_retries(0.6, 0.3, 4000, 4, seed=11)
first_independent = sum(tries[0] for tries in independent) / len(independent)
first_with_hard = sum(tries[0] for tries in with_hard) / len(with_hard)
print(
    "no hard tasks: first",
    round(first_independent, 3),
    "retry",
    round(retry_after_failure(independent), 3),
)
print(
    "30% hard: first", round(first_with_hard, 3), "retry", round(retry_after_failure(with_hard), 3)
)
assert abs(retry_after_failure(independent) - first_independent) < 0.04
assert retry_after_failure(with_hard) < first_with_hard - 0.08
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch03-b"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit checked formulas against simulators with memoryless, identical steps. It did not show that a real model's steps behave that way; the chapter's measured run shows they may not.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch03-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch03-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch03-b",
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
