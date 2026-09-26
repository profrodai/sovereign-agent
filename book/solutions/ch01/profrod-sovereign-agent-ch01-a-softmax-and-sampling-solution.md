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
    lesson_id: first-model-call
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch01-a-softmax-and-sampling-solution
    self_contained_runtime: true
    source_basis: chapter-1-manuscript
    source_unit: ch01-a
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch01-a
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

# Chapter 1, Unit A: Build softmax and a sampler from scratch

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-26**

This is the worked edition of Chapter 1, Unit A. It contains:

- complete answers;
- the instructor explanation;
- holdout cases that the student edition does not show.

Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, using only the standard library.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict what temperature does to a distribution | Written prediction |
| 10–30 | Tokens, logits and entropy, as worked examples | Observed outputs |
| 30–60 | Construct `softmax` and `sample`, and pass the visible cases | Learner code and grade table |
| 60–70 | Generate Lucy's notes and measure entropy against temperature | Measured table |
| 70–85 | Changed-constraint task: min-p sampling | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell below creates your work folder and supplies the parts of Chapter 1 you are not building today:

- **Lucy's notes,** a small training corpus and a few held-out notes.
- **A byte-pair encoder,** which learns tokens from the notes.
- **A bigram model,** which gives a logit for every token that could follow the previous one.
- **An entropy function.**

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch01-a`.

<details><summary>Supplied setup: corpus, tokenizer, model and entropy</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import math
import os
import random
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch01-course-"))

SHOP_NOTES = """\
Vanilla is running low: two tubs left in the freezer.
Chocolate is plentiful: eleven tubs in the freezer.
Strawberry has almost gone: one tub left in the freezer.
Order six tubs of vanilla before the weekend.
The supplier delivers vanilla on Tuesday morning.
A tub of vanilla costs 250 cents; a tub of chocolate costs 300 cents.
A tub of strawberry costs 275 cents.
Check the freezer before the shop opens at nine.
The morning brief lists every tub in the freezer.
Vanilla sold eight scoops before noon.
Chocolate sold five scoops before noon.
Strawberry sold three scoops before noon.
Order four tubs of strawberry before the weekend.
Do not order chocolate this week.
The supplier needs orders before Monday evening.
Lucy approves every order before the supplier sees it.
The brief says what is low and what to order.
Two tubs of vanilla is below the target of eight tubs.
One tub of strawberry is below the target of five tubs.
Eleven tubs of chocolate is above the target of six tubs.
"""
HELD_OUT_NOTES = """\
Vanilla is running low: three tubs left in the freezer.
Order five tubs of vanilla before Tuesday morning.
Strawberry sold four scoops before noon.
"""
PRETOKEN = re.compile(r" ?[A-Za-z]+| ?[0-9]+| ?[^\sA-Za-z0-9]+|\s+")


def pretokens(text):
    return [piece.encode("utf-8") for piece in PRETOKEN.findall(text)]


def merge_pair(symbols, pair):
    merged, i = [], 0
    while i < len(symbols):
        if i + 1 < len(symbols) and (symbols[i], symbols[i + 1]) == pair:
            merged.append(symbols[i] + symbols[i + 1])
            i += 2
        else:
            merged.append(symbols[i])
            i += 1
    return merged


def train_bpe(text, merges):
    """Learn up to `merges` merges: repeatedly join the most frequent adjacent pair."""
    words = Counter(pretokens(text))
    split = {word: [bytes([b]) for b in word] for word in words}
    learned = []
    for _ in range(merges):
        pairs = Counter()
        for word, count in words.items():
            for pair in zip(split[word], split[word][1:], strict=False):
                pairs[pair] += count
        if not pairs:
            break
        best = min(pairs, key=lambda pair: (-pairs[pair], pair))
        if pairs[best] < 2:
            break
        learned.append(best)
        for word in split:
            split[word] = merge_pair(split[word], best)
    return learned


def encode(text, merges):
    tokens = []
    for word in pretokens(text):
        symbols = [bytes([b]) for b in word]
        for pair in merges:
            symbols = merge_pair(symbols, pair)
        tokens.extend(symbols)
    return tokens


def decode(tokens, errors="strict"):
    return b"".join(tokens).decode("utf-8", errors)


class BigramModel:
    """P(next token | previous token) from counts with add-alpha smoothing."""

    def __init__(self, tokens, merges, alpha=0.001):
        self.vocabulary = tuple(bytes([b]) for b in range(256)) + tuple(a + b for a, b in merges)
        self.alpha = alpha
        self.counts = defaultdict(Counter)
        for previous, following in zip(tokens, tokens[1:], strict=False):
            self.counts[previous][following] += 1

    def logits(self, previous):
        row = self.counts.get(previous, Counter())
        return [math.log(row[token] + self.alpha) for token in self.vocabulary]


def entropy_bits(probabilities):
    return -sum(p * math.log2(p) for p in probabilities if p > 0) + 0.0


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch01-a"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

A model gives the tokens that could follow "." these scores (logits): 5.0 for a newline, 1.0 for a space, and 0.0 for each of 350 other tokens.

Before you run anything, write down:

- the probability of the newline at temperature 1;
- what happens to that probability at temperature 0.5 and at temperature 2;
- whether any token can ever have probability exactly zero.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write the newline's probability at T = 1, 0.5 and 2, and whether any is zero.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Text becomes tokens

A model reads integers, each naming an entry in a vocabulary, never letters. The supplied **byte-pair encoder** starts from the 256 possible bytes, so any text can be encoded. It then repeatedly merges the most frequent adjacent pair in Lucy's notes into a new token. Predict how "Order six tubs of vanilla" splits after 100 merges: which words become single tokens, and which stay in pieces?

```python tags=["foundation", "worked-example"]
intro_merges = train_bpe(SHOP_NOTES, 100)
intro_tokens = encode("Order six tubs of vanilla.", intro_merges)
print(len(intro_merges), "merges")
print([token.decode() for token in intro_tokens])
print(decode(intro_tokens) == "Order six tubs of vanilla.")
```

Frequent words (" tubs", " of", " vanilla") became single tokens, each with its leading space. "Six" appears once in the notes and stays three characters. Tokens are what you pay for, and what fill a model's context window. A word the tokenizer rarely saw costs more tokens.

### A model gives every token a score

A language model maps the tokens so far to one **logit** per vocabulary entry. The supplied bigram model looks only at the previous token. Its logit for each candidate is the logarithm of how often the candidate followed that token in the notes, plus a small constant $\alpha$. Predict which tokens score highest after " of".

```python tags=["foundation", "worked-example"]
intro_model = BigramModel(encode(SHOP_NOTES, intro_merges), intro_merges)
intro_logits = intro_model.logits(b" of")
intro_best = sorted(range(len(intro_logits)), key=lambda i: -intro_logits[i])[:3]
print(len(intro_model.vocabulary), "logits, one per token")
for intro_index in intro_best:
    print(repr(intro_model.vocabulary[intro_index].decode()), round(intro_logits[intro_index], 3))
print("exp of the top logit:", round(math.exp(intro_logits[intro_best[0]]), 3))
```

$e^{1.099} \approx 3$: " vanilla" followed " of" three times. Logits are scores, not probabilities. They do not sum to one, and only their differences matter.

### From scores to probabilities: softmax

We want probabilities that are positive, sum to one, and treat a logit difference as a log-odds: $\log(p_i / p_j) = z_i - z_j$. The last requirement forces $p_i \propto e^{z_i}$, and the second fixes the constant:

$$
p_i \;=\; \frac{e^{z_i / T}}{\sum_j e^{z_j / T}},
$$

with a **temperature** $T$ that divides every logit. Adding the same constant to every logit changes nothing, because it cancels between the numerator and denominator. Implementations use that fact to subtract the largest logit first, so no exponential overflows. As $T \to 0$, all probability moves to the largest logit (**greedy decoding**); as $T \to \infty$ the distribution becomes uniform.

### How spread out: entropy

The **entropy** $H = -\sum_i p_i \log_2 p_i$ is the average surprise of one draw, in bits. Predict the entropy of a fair coin and of a fair four-sided die.

```python tags=["foundation", "worked-example"]
print("coin:", entropy_bits([0.5, 0.5]), "bits")
print("die:", entropy_bits([0.25] * 4), "bits")
print("certain:", entropy_bits([1.0, 0.0]), "bits")
```

The chapter proves that raising the temperature never lowers entropy, and at exactly what rate:

$$
\frac{dH}{dT} \;=\; \frac{\mathrm{Var}_p(z)}{T^3}\ \text{nats per unit temperature},
$$

where $\mathrm{Var}_p(z)$ is the variance of the logits under the current distribution. You will check this on your own softmax.

**Retrieval check:** in your own words, explain a token versus a character, a logit versus a probability, and why a model's distribution never assigns exactly zero to anything.

## Main practical: construct, connect and challenge

## 1. Construct `softmax` and `sample`

`softmax(logits, temperature=1.0)` receives a list of floats. It must:

- return a list of probabilities of the same length that sums to one;
- subtract the largest logit before exponentiating, so logits like 1000 do not overflow;
- at `temperature == 0`, put probability 1 on the first largest logit and 0 elsewhere;
- otherwise divide each logit by the temperature;
- not change its input.

`sample(probabilities, rng)` receives probabilities and a `random.Random`. It must return index `i` with probability `probabilities[i]`, and never an index whose probability is zero. Use inverse transform sampling: draw `u = rng.random()` and return the first index whose running total exceeds `u`.

The starters below work for small logits only, and sample uniformly. Run the visible cases, then repair both.

```python tags=["exercise", "learner-owned", "ch01-softmax"]
def softmax(logits, temperature=1.0):
    """Probabilities from logits at a temperature."""
    if temperature == 0:
        best = max(range(len(logits)), key=lambda i: logits[i])
        return [1.0 if i == best else 0.0 for i in range(len(logits))]
    top = max(logits)
    weights = [math.exp((z - top) / temperature) for z in logits]
    total = sum(weights)
    return [w / total for w in weights]


def sample(probabilities, rng):
    """One index, drawn with the given probabilities."""
    u, running = rng.random(), 0.0
    for index, probability in enumerate(probabilities):
        running += probability
        if u < running:
            return index
    return max(index for index, probability in enumerate(probabilities) if probability > 0)
```

<details><summary>Hint 1 — overflow</summary>

`math.exp(1000)` raises `OverflowError`. Subtract `max(logits)` from every logit first: the largest becomes 0, `exp(0) = 1`, and every probability is unchanged.

</details>

<details><summary>Hint 2 — temperature zero</summary>

Dividing by zero is not the limit. Handle `temperature == 0` before any division: find the index of the first largest logit and return a one-hot list.

</details>

<details><summary>Hint 3 — the sampler</summary>

Walk the probabilities, adding each to a running total, and return the first index where `u < running`. Rounding can leave the final total a hair below one, so if the loop ends without returning, return the last index with nonzero probability.

</details>

```python tags=["assessment", "visible"]
import copy


def chi_square_z(sampler, probabilities, draws=20_000, seed=3):
    """How far a sampler's counts are from expected, in standard deviations of chi-square."""
    rng, counts = random.Random(seed), [0] * len(probabilities)
    for _ in range(draws):
        counts[sampler(probabilities, rng)] += 1
    kept = [(p, c) for p, c in zip(probabilities, counts, strict=True) if p > 0]
    if any(c for p, c in zip(probabilities, counts, strict=True) if p == 0):
        return math.inf
    chi = sum((c - draws * p) ** 2 / (draws * p) for p, c in kept)
    freedom = len(kept) - 1
    return (chi - freedom) / math.sqrt(2 * freedom)


def close(a, b):
    return all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b, strict=True))


SKEWED = [0.5, 0.25, 0.125, 0.0625, 0.0625]
VISIBLE_CASES = [
    ("probabilities sum to one", lambda: math.isclose(sum(softmax([2.0, 1.0, 0.0])), 1.0)),
    (
        "a shift changes nothing",
        lambda: close(softmax([2.0, 1.0, 0.0]), softmax([102.0, 101.0, 100.0])),
    ),
    ("large logits stay finite", lambda: math.isclose(sum(softmax([1000.0, 999.0])), 1.0)),
    ("temperature 0 is greedy", lambda: softmax([1.0, 3.0, 3.0, 0.0], 0) == [0.0, 1.0, 0.0, 0.0]),
    (
        "lower temperature sharpens",
        lambda: max(softmax([2.0, 1.0, 0.0], 0.5)) > max(softmax([2.0, 1.0, 0.0], 1.0)),
    ),
    ("the sampler follows the distribution", lambda: abs(chi_square_z(sample, SKEWED)) < 3),
    (
        "never a zero-probability index",
        lambda: {sample([0.0, 1.0, 0.0], random.Random(s)) for s in range(200)} == {1},
    ),
    ("does not change its input", lambda: unchanged_after_softmax([2.0, 1.0, 0.0])),
]


def unchanged_after_softmax(logits):
    kept = list(logits)
    softmax(logits, 0.5)
    return logits == kept


def grade(cases):
    rows = []
    for label, check in cases:
        try:
            observed = "PASS" if check() else "FAIL"
        except Exception as error:
            observed = f"FAIL ({type(error).__name__})"
        rows.append({"case": label, "status": observed})
    return rows


visible_results = grade(VISIBLE_CASES)
VISIBLE_PASSED = all(row["status"] == "PASS" for row in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 2. Connect: generate Lucy's notes, and measure temperature

Once the visible cases pass, the cell below uses *your* functions:

- it generates ten tokens after a newline at temperatures 0, 0.7 and 1.5;
- it measures the entropy of the distribution after "." at five temperatures, and compares the derived $dH/dT$ with a numerical derivative of your softmax.

Before running it, predict which temperature produces text no note contains, and at which temperature the entropy rises fastest.

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:
    shop_merges = train_bpe(SHOP_NOTES, 100)
    shop_model = BigramModel(encode(SHOP_NOTES, shop_merges), shop_merges)
    generations = {}
    for temperature in (0, 0.7, 1.5):
        rng = random.Random(7)
        tokens = [b"\n"]
        for _ in range(10):
            probabilities = softmax(shop_model.logits(tokens[-1]), temperature)
            tokens.append(shop_model.vocabulary[sample(probabilities, rng)])
        generations[str(temperature)] = decode(tokens[1:], errors="replace")
    after_period = shop_model.logits(b".")
    table = []
    for temperature in (0.5, 1.0, 1.5, 2.0):
        p = softmax(after_period, temperature)
        mean = sum(pi * z for pi, z in zip(p, after_period, strict=True))
        variance = sum(pi * (z - mean) ** 2 for pi, z in zip(p, after_period, strict=True))
        derived = variance / temperature**3 / math.log(2)
        step = 1e-5
        numeric = (
            entropy_bits(softmax(after_period, temperature + step))
            - entropy_bits(softmax(after_period, temperature - step))
        ) / (2 * step)
        table.append([temperature, round(entropy_bits(p), 4), round(derived, 4), round(numeric, 4)])
    connected = {"generations": generations, "entropy_table": table}
    for temperature, text in generations.items():
        print(temperature, repr(text))
    print("T, entropy bits, dH/dT derived, dH/dT numerical")
    for row in table:
        print(row)
    assert all(math.isclose(row[2], row[3], rel_tol=1e-3, abs_tol=1e-4) for row in table)
else:
    print("CONNECTION_NOT_READY — repair softmax and sample, then run again.")
```

Trace one row of the table. Which quantity in the derivation, $\mathrm{Var}_p(z)$ or $T^3$, makes the entropy rise slowly at $T = 0.5$ and fast at $T = 1.5$? Which line of generated text would you trust as a note Lucy wrote, and what does that say about choosing a temperature for her brief?

## 3. Save the handoff

Unit B starts from this unit's tokenizer. The handoff records the merges you trained (as hexadecimal pairs) and the table you measured.

```python tags=["handoff"]
ARTIFACT_PATH = Path("ch01-unit-a-handoff-v1.json")
artifact_status = "NOT_WRITTEN"
if connected is not None:
    handoff = {
        "unit": "ch01-a",
        "status": "COMPLETED",
        "merges": [[a.hex(), b.hex()] for a, b in shop_merges],
        "alpha": shop_model.alpha,
        "entropy_table": connected["entropy_table"],
    }
    ARTIFACT_PATH.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact_status = "WRITTEN"
    print(ARTIFACT_PATH)
else:
    print("HANDOFF_NOT_WRITTEN")
```

## Exit ticket

Answer three questions:

- Why does subtracting the largest logit change no probability?
- Why is testing a sampler by looking at a few outputs not a test?
- What does temperature 0 trade away, and what does it not guarantee when a real model runs on real hardware?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch01-a",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": artifact_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: min-p sampling

**Allow fifteen minutes:** three to predict, eight to implement and trace, and four for a case of your own.

Top-p keeps the most likely tokens until their total reaches $p$. A newer rule, **min-p**, keeps every token whose probability is at least a fraction of the top token's:

$$
\text{keep } i \iff p_i \;\ge\; r \cdot \max_j p_j,
$$

and renormalizes the kept probabilities to sum to one. When the model is confident, min-p cuts the tail hard; when it is unsure, it keeps many options.

Implement `transfer_min_p(probabilities, ratio)`:

- return a new list of the same length, with dropped tokens at 0;
- keep tokens tied with the threshold;
- do not change the input.

The driver copies the inputs and checks that they come back unchanged.

<details><summary>Hint — the threshold moves</summary>
Compute the threshold from the largest probability first, then keep and renormalize. With `ratio = 0`, every token with nonzero probability is kept.
</details>

```python tags=["exercise", "transfer-owned"]
def transfer_min_p(probabilities, ratio):
    threshold = ratio * max(probabilities)
    kept = [p if p >= threshold and p > 0 else 0.0 for p in probabilities]
    total = sum(kept)
    return [p / total for p in kept]
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("ratio 0 keeps every possible token", [[0.5, 0.3, 0.2, 0.0], 0.0], [0.5, 0.3, 0.2, 0.0]),
    ("ratio 1 keeps only the top token", [[0.5, 0.3, 0.2], 1.0], [1.0, 0.0, 0.0]),
    ("half the top probability", [[0.5, 0.3, 0.2], 0.5], [0.625, 0.375, 0.0]),
    ("a tie with the threshold is kept", [[0.4, 0.2, 0.2, 0.2], 0.5], [0.4, 0.2, 0.2, 0.2]),
    ("ties at the top are both kept", [[0.45, 0.45, 0.1], 1.0], [0.5, 0.5, 0.0]),
]


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        try:
            result = candidate(*supplied)
            actual = [round(p, 6) for p in result]
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


transfer_observations = run_transfer(transfer_min_p, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add one case with an expected result you worked out by hand, and rerun the driver. Then apply your min-p with ratio 0.1 to the shop model's distribution after "." at temperature 2. How many tokens does it keep, compared with top-p at 0.9? Explain which rule you would choose for Lucy's brief, and why.


## Instructor explanation and additional transfer cases

Three misconceptions come up.

**"Softmax is just normalizing."** Dividing logits by their sum fails for negative logits and ignores that logits are log-odds. The exponential is what makes a difference of scores a ratio of probabilities.

**"Temperature 0 means the model is deterministic."** In this notebook it does, because the arithmetic is fixed. On a real server, batching and parallel reductions reorder floating-point additions, so two greedy runs can differ. The chapter records exactly that.

**"The sampler looks right."** A uniform sampler produces plausible-looking text too. Only a statistical test over many draws, with a negative control that must fail, separates a correct sampler from a plausible one.

The cases below add a distribution with exact zeros and a flat distribution.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    ("zeros stay zero", [[0.0, 0.8, 0.0, 0.2], 0.2], [0.0, 0.8, 0.0, 0.2]),
    ("a flat distribution keeps everything", [[0.25, 0.25, 0.25, 0.25], 0.9], [0.25] * 4),
]
instructor_observations = run_transfer(transfer_min_p, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
holdout_distribution = softmax([3.0, 2.0, 2.0, 0.0, -1.0], 1.3)
assert math.isclose(sum(holdout_distribution), 1.0)
assert abs(chi_square_z(sample, holdout_distribution, seed=11)) < 3


def holdout_broken(probabilities, rng):
    return min(len(probabilities) - 1, sample(probabilities, rng) + 1)


assert chi_square_z(holdout_broken, holdout_distribution, seed=11) > 50
assert softmax([-1000.0, -1000.0, -999.0], 0) == [0.0, 0.0, 1.0]
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch01-a"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit sampled from a model you can read completely. It did not run a real language model; Chapter 1's experiment does that, with its receipt.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch01-a",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch01-a-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch01-a",
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
