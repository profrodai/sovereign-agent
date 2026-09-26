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
    resource_id: profrod-sovereign-agent-ch01-b-misleading-model-comparison-solution
    self_contained_runtime: true
    source_basis: chapter-1-manuscript
    source_unit: ch01-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch01-b
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

# Chapter 1, Unit B: Diagnose a misleading model comparison

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-26**

This is the worked edition of Chapter 1, Unit B. It contains:

- complete answers;
- the instructor explanation;
- holdout cases that the student edition does not show.

Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, using only the standard library.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict which tokenizer the colleague should have chosen | Written prediction |
| 10–30 | Likelihood, cross-entropy and the colleague's comparison | Worked outputs and handoff |
| 30–60 | Construct `bits_per_character` and pass the visible cases | Learner code and grade table |
| 60–70 | Choose a tokenizer fairly, including Unit A's | Measured table |
| 70–85 | Changed-constraint task: bits per character from a real model | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell supplies Lucy's notes, the byte-pair encoder, the bigram model, and a correct `softmax`: everything Unit A built or used.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch01-b`.

<details><summary>Supplied setup: corpus, tokenizer, model and softmax</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import math
import os
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


def softmax(logits, temperature=1.0):
    top = max(logits)
    weights = [math.exp((z - top) / temperature) for z in logits]
    total = sum(weights)
    return [w / total for w in weights]


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch01-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

Your colleague trained the same bigram model on Lucy's notes with four tokenizers: 0, 50, 100 and 200 requested merges (the last stops at 134, when no pair repeats). They chose the tokenizer whose model had the lowest perplexity per token on the training notes.

Before you run anything, write down:

- which tokenizer you expect that rule to choose;
- whether you expect the same tokenizer to be best on notes the model never saw.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write which tokenizer the colleague's rule picks, and which wins on new notes.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Likelihood and cross-entropy

A model assigns a probability to a whole text by multiplying, token by token, the probability it gave each token after the one before:

$$
P(t_1, \dots, t_n) = \prod_{k=2}^{n} P(t_k \mid t_{k-1}).
$$

The average negative base-2 logarithm of those probabilities is the model's **cross-entropy** on the text: the bits it needs per token.

$$
\mathcal{H} = -\frac{1}{n-1} \sum_{k=2}^{n} \log_2 P(t_k \mid t_{k-1}).
$$

**Perplexity** is $2^{\mathcal{H}}$, the number of equally likely tokens the model is, on average, torn between. Training a language model means minimizing cross-entropy on its training text. For a bigram model, counting is that minimization, done exactly.

### The colleague's comparison, reproduced

The cell below implements the colleague's rule: per-token perplexity on the training notes. Predict its choice before you run it.

```python tags=["foundation", "worked-example"]
def colleague_perplexity(model, tokens):
    index = {token: i for i, token in enumerate(model.vocabulary)}
    bits = 0.0
    for previous, following in zip(tokens, tokens[1:], strict=False):
        bits -= math.log2(softmax(model.logits(previous))[index[following]])
    return 2 ** (bits / (len(tokens) - 1))


intro_rows = []
for requested in (0, 50, 100, 200):
    intro_merges = train_bpe(SHOP_NOTES, requested)
    intro_tokens = encode(SHOP_NOTES, intro_merges)
    intro_model = BigramModel(intro_tokens, intro_merges)
    intro_rows.append(
        (len(intro_merges), round(colleague_perplexity(intro_model, intro_tokens), 3))
    )
for merges_used, perplexity in intro_rows:
    print(merges_used, "merges: training perplexity per token", perplexity)
print("colleague chooses", min(intro_rows, key=lambda row: row[1])[0], "merges")
```

Two things are wrong with this comparison.

- **Per-token numbers compare different tasks.** With no merges, a token is one character; with 134, it averages 3.2 characters. Predicting a bigger unit is harder per prediction and easier per character, so per-token perplexity rewards or punishes the tokenizer, not the model. The fair unit is **bits per character**: total bits divided by the length of the text.
- **Training text rewards memorization.** A model can always fit its own training text better. The last merges turn whole phrases of the notes into single tokens, which helps on those notes and nowhere else. Only held-out text ranks models honestly.

## Choose an explicit starting point

This unit starts from Unit A's tokenizer. To use your own, replace `None` with the path to your `practical-work/ch01-a/ch01-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import shutil

COURSE_INPUT = COURSE_WORK / "ch01-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_handoff = {
        "unit": "ch01-a",
        "status": "COMPLETED",
        "merges": [[a.hex(), b.hex()] for a, b in train_bpe(SHOP_NOTES, 100)],
        "alpha": 0.001,
        "entropy_table": [],
    }
    COURSE_INPUT.write_text(json.dumps(reference_handoff, indent=2, sort_keys=True) + "\n")
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
```

```python tags=["setup", "handoff-consumer"]
handoff = json.loads(COURSE_INPUT.read_text(encoding="utf-8"))
handoff_status = "VERIFIED" if handoff.get("status") == "COMPLETED" else "INVALID"
unit_a_merges = [(bytes.fromhex(a), bytes.fromhex(b)) for a, b in handoff["merges"]]
unit_a_alpha = handoff["alpha"]
print("UNIT_A_HANDOFF", handoff_status)
print("Unit A tokenizer:", len(unit_a_merges), "merges, alpha", unit_a_alpha)
```

## Main practical: construct, connect and challenge

## 1. Construct `bits_per_character`

`bits_per_character(model, merges, text)` must:

- encode `text` with `merges`;
- sum $-\log_2 P(t_k \mid t_{k-1})$ over every consecutive pair of tokens, using the model's logits and the supplied `softmax`;
- divide the total by the number of **characters** in `text`, not the number of tokens;
- raise `ValueError` when the text encodes to fewer than two tokens, because there is nothing to predict.

The starter below computes the colleague's quantity instead. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch01-bits-per-character"]
def bits_per_character(model, merges, text):
    """Average bits the model needs per character of text."""
    tokens = encode(text, merges)
    if len(tokens) < 2:
        raise ValueError("need at least two tokens to predict one")
    index = {token: i for i, token in enumerate(model.vocabulary)}
    bits = 0.0
    for previous, following in zip(tokens, tokens[1:], strict=False):
        bits -= math.log2(softmax(model.logits(previous))[index[following]])
    return bits / len(text)
```

<details><summary>Hint 1 — the denominator</summary>

The numerator is the same total number of bits either way. Only the denominator changes: `len(text)` characters, not `len(tokens) - 1` predictions.

</details>

<details><summary>Hint 2 — the edge case</summary>

A single token has no successor, so there are no predictions and no bits. Refuse it with `ValueError` rather than dividing zero bits by a length and reporting a perfect score.

</details>

```python tags=["assessment", "visible"]
import copy


class FixedModel:
    """A stub model with the same logits after every token: answers you can work out by hand."""

    def __init__(self, vocabulary, logits):
        self.vocabulary, self._logits = tuple(vocabulary), list(logits)

    def logits(self, previous):
        return list(self._logits)


def outcome(call):
    try:
        return round(call(), 6)
    except Exception as error:
        return type(error).__name__


AB = FixedModel([b"a", b"b"], [0.0, 0.0])
SKEW = FixedModel([b"a", b"b"], [math.log(3), 0.0])
MERGED = FixedModel([b"a", b"b", b"ab"], [0.0, 0.0, 0.0])
VISIBLE_CASES = [
    ("fair coin, four characters", lambda: bits_per_character(AB, [], "abab"), 0.75),
    ("a likely then unlikely token", lambda: bits_per_character(SKEW, [], "ab"), 1.0),
    (
        "merged tokens, characters not tokens",
        lambda: bits_per_character(MERGED, [(b"a", b"b")], "abab"),
        round(math.log2(3) / 4, 6),
    ),
    ("one token predicts nothing", lambda: bits_per_character(AB, [], "a"), "ValueError"),
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

## 2. Connect: choose a tokenizer fairly, including Unit A's

Once the visible cases pass, the cell below scores every candidate tokenizer, including the one from your Unit A handoff. For each it reports bits per character on the training notes and on the held-out notes, and it chooses by held-out bits per character.

Predict the choice, and predict which candidate the training column would have chosen.

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:
    candidates = {f"{n} requested merges": train_bpe(SHOP_NOTES, n) for n in (0, 50, 200)}
    candidates["Unit A tokenizer"] = unit_a_merges
    table = []
    for name, merges in candidates.items():
        model = BigramModel(encode(SHOP_NOTES, merges), merges, alpha=unit_a_alpha)
        table.append(
            {
                "tokenizer": name,
                "merges": len(merges),
                "train_bits_per_character": round(bits_per_character(model, merges, SHOP_NOTES), 3),
                "held_out_bits_per_character": round(
                    bits_per_character(model, merges, HELD_OUT_NOTES), 3
                ),
            }
        )
    fair = min(table, key=lambda row: row["held_out_bits_per_character"])
    by_training = min(table, key=lambda row: row["train_bits_per_character"])
    connected = {
        "table": table,
        "fair_choice": fair["tokenizer"],
        "training_choice": by_training["tokenizer"],
    }
    for row in table:
        print(row)
    print("choose by held-out bits per character:", fair["tokenizer"])
    print("training bits per character would choose:", by_training["tokenizer"])
else:
    print("CONNECTION_NOT_READY — repair bits_per_character, then run again.")
```

Trace the two choices. Which row does training favor, and by how much does it lose on held-out notes? Where did the extra merges' advantage on training text go? Write the one sentence you would send your colleague.

## Exit ticket

Answer three questions:

- Why can two models with different tokenizers not be compared by per-token perplexity?
- Why does the training column always favor the tokenizer with the most merges?
- What would you need, beyond three held-out notes, before trusting the choice for Lucy's real model?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch01-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: bits per character from a real model

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

A real model's API can return, for every token it generated or scored, the natural logarithm of its probability (`logprobs`). You have no access to its weights, only these numbers and the text. Compute the same fair measure from them.

Implement `transfer_bits_per_character(log_probabilities, text)`:

- `log_probabilities` is a list of natural-log probabilities, one per scored token;
- return $-\sum \ell_k / \ln 2$ divided by the number of characters in `text`;
- raise `ValueError` for an empty list, or for any value above 0 (a probability above one);
- do not change the input.

The driver compares your result, rounded to six places, with values worked out by hand.

<details><summary>Hint — units</summary>
Natural logs measure nats. Divide by $\ln 2 \approx 0.6931$ to get bits, then divide by characters. A log-probability of exactly 0 is allowed: probability one.
</details>

```python tags=["exercise", "transfer-owned"]
def transfer_bits_per_character(log_probabilities, text):
    if not log_probabilities or any(value > 0 for value in log_probabilities):
        raise ValueError("need natural-log probabilities, each at most 0")
    return -sum(log_probabilities) / math.log(2) / len(text)
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("one certain token", [[0.0], "ok"], 0.0),
    ("two coin flips over four characters", [[math.log(0.5), math.log(0.5)], "abcd"], 0.5),
    ("a quarter-probability token", [[math.log(0.25)], "xy"], 1.0),
    ("an empty list is refused", [[], "text"], {"raises": "ValueError"}),
    ("a positive log-probability is refused", [[0.1], "text"], {"raises": "ValueError"}),
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


transfer_observations = run_transfer(transfer_bits_per_character, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case with an expected value you worked out by hand, and rerun the driver. Then take the chapter's live receipt: 49 answer tokens with a total log-probability of −49.9 nats, and an answer of about 250 characters. Compute its bits per character, and compare it with the bigram model's held-out figure. Explain why that comparison is still not fair: the texts differ.


## Instructor explanation and additional transfer cases

Three misconceptions come up.

**"Lower perplexity is better, full stop."** Only on the same text, with the same tokenizer. Across tokenizers, compare bits per character or per byte. Across texts, compare nothing.

**"The training column is a noisy estimate of the held-out column."** It is a biased one. A model is fitted to its training text, so training loss is systematically optimistic, and more so for more flexible models. That is why every training run reports a validation loss.

**"Three held-out notes are enough."** They are enough to show the mechanism, not to choose a production tokenizer. The spread of held-out bits across many held-out samples would tell you whether the difference between 100 and 134 merges is real. Chapter 15 builds that statistics.

The cases below add a long text and a mix of certain and uncertain tokens.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    ("certain and uncertain tokens", [[0.0, math.log(0.5), 0.0], "abcdefgh"], 0.125),
    ("a long text dilutes the same bits", [[math.log(0.5)] * 4, "x" * 100], 0.04),
]
instructor_observations = run_transfer(transfer_bits_per_character, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
holdout_model = BigramModel(encode(SHOP_NOTES, unit_a_merges), unit_a_merges, alpha=unit_a_alpha)
holdout_tokens = encode(HELD_OUT_NOTES, unit_a_merges)
holdout_index = {token: i for i, token in enumerate(holdout_model.vocabulary)}
holdout_bits = -sum(
    math.log2(softmax(holdout_model.logits(p))[holdout_index[f]])
    for p, f in zip(holdout_tokens, holdout_tokens[1:], strict=False)
)
assert math.isclose(
    bits_per_character(holdout_model, unit_a_merges, HELD_OUT_NOTES),
    holdout_bits / len(HELD_OUT_NOTES),
)
assert connected is not None and connected["fair_choice"] != connected["training_choice"]
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch01-b"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

This unit ranked tokenizers on three held-out notes. It did not measure how much that ranking would vary with a different held-out sample.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch01-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch01-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch01-b",
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
