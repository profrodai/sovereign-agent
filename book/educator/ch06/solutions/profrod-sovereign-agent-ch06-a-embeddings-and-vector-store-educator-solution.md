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
    lesson_id: embeddings
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch06-a-embeddings-and-vector-store-solution
    self_contained_runtime: true
    source_basis: chapter-6-manuscript
    source_unit: ch06-a
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch06-a
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

# Chapter 6, Unit A: Build embeddings and a vector store

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-27**

This is the worked edition of Chapter 6, Unit A. It contains:

- complete answers;
- the instructor explanation;
- holdout cases that the student edition does not show.

Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, using only the standard library.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict similarity from word indexes | Written prediction |
| 10–35 | One-hot vectors, the lookup, a training step, pooling and distances, as worked examples | Observed outputs |
| 35–60 | Construct `search` and pass the visible cases | Learner code and grade table |
| 60–70 | Build Lucy's index and search it, including a changed rule | Independent observation |
| 70–85 | Changed-constraint task: fuse two rankings | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell below creates your work folder and defines the supplied parts of the unit:

- **Lucy's twelve notes**, and a tokenizer that lowercases words and drops small words such as "the".
- **Vector arithmetic:** `one_hot`, `matvec`, `dot`, `norm`, `normalize` and `cosine`.
- **Skip-gram training:** `training_pairs`, and `train`, which learns two numbers per word from which words appear near each other. It is seeded, so every run gives the same vectors.
- **`note_vector`**, which averages a note's word vectors and normalizes the result, and **`build_index`**, which turns notes into index rows.

Run setup on every fresh kernel. Your saved work lives in `practical-work/ch06-a`. Restarting a kernel clears variables, not saved files.

<details><summary>Supplied setup, notes, arithmetic and training</summary>

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
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch06-course-"))

NOTES = [
    "mango sorbet is dairy-free and vegan",
    "oat vanilla is dairy-free and vegan",
    "vegan customers ask for sorbet",
    "dairy-free customers ask for oat vanilla",
    "vanilla scoop in a waffle cone",
    "chocolate scoop in a waffle cone",
    "strawberry scoop in a sugar cone",
    "kids want a chocolate cone",
    "the supplier delivers tubs on monday",
    "the supplier sends the invoice on friday",
    "pay the supplier invoice in cents",
    "order more tubs from the supplier",
]
NOTE_IDS = [f"n{i + 1}" for i in range(len(NOTES))]
STOP = {
    "a",
    "an",
    "the",
    "is",
    "and",
    "in",
    "on",
    "for",
    "of",
    "from",
    "more",
    "ask",
    "want",
    "with",
}


def tokenize(text):
    """Lowercase words; a hyphen stays inside a word (dairy-free); small words are dropped."""
    words = "".join(c if c.isalpha() or c == "-" else " " for c in text.lower()).split()
    return [w for w in words if w not in STOP]


def build_vocab(notes):
    return sorted({w for note in notes for w in tokenize(note)})


def one_hot(word, vocab):
    if word not in vocab:
        raise ValueError(f"unknown word: {word!r}")
    return [1 if w == word else 0 for w in vocab]


def matvec(matrix, vector):
    """A matrix (a list of rows) times a column vector."""
    return [sum(m * v for m, v in zip(row, vector, strict=True)) for row in matrix]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(v):
    return math.sqrt(dot(v, v))


def normalize(v):
    length = norm(v)
    if length == 0:
        raise ValueError("cannot normalize a zero vector")
    return [x / length for x in v]


def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def training_pairs(notes, window=2):
    """(center, neighbor) pairs: words within `window` positions of each other in one note."""
    pairs = []
    for note in notes:
        words = tokenize(note)
        for i, center in enumerate(words):
            for j in range(max(0, i - window), min(len(words), i + window + 1)):
                if j != i:
                    pairs.append((center, words[j]))
    return pairs


def train(notes, dim=2, window=2, negatives=3, epochs=120, rate=0.05, seed=7, keep=(0, 5, 120)):
    """Skip-gram with negative sampling. Returns the vocabulary, the embeddings, snapshots of the
    embeddings and context vectors after the epochs in `keep`, and the loss per pair per epoch."""
    chooser = random.Random(seed)
    vocab = build_vocab(notes)
    embedding = {w: [chooser.uniform(-0.5, 0.5) for _ in range(dim)] for w in vocab}
    contexts = {w: [0.0] * dim for w in vocab}
    pairs = training_pairs(notes, window)
    snapshots = {
        0: ({w: list(v) for w, v in embedding.items()}, {w: list(v) for w, v in contexts.items()})
    }
    losses = []
    for epoch in range(1, epochs + 1):
        chooser.shuffle(pairs)
        total = 0.0
        for center, neighbor in pairs:
            samples = [(neighbor, 1)] + [(chooser.choice(vocab), 0) for _ in range(negatives)]
            grad = [0.0] * dim
            for word, label in samples:
                if label == 0 and word == neighbor:
                    continue
                p = sigmoid(dot(embedding[center], contexts[word]))
                total += -math.log(p if label else 1 - p)
                g = p - label
                for k in range(dim):
                    grad[k] += g * contexts[word][k]
                    contexts[word][k] -= rate * g * embedding[center][k]
            for k in range(dim):
                embedding[center][k] -= rate * grad[k]
        losses.append(total / len(pairs))
        if epoch in keep:
            snapshots[epoch] = (
                {w: list(v) for w, v in embedding.items()},
                {w: list(v) for w, v in contexts.items()},
            )
    return vocab, embedding, snapshots, losses


def note_vector(text, embedding):
    """Mean pooling of the known words' vectors, then normalization to length one."""
    words = [w for w in tokenize(text) if w in embedding]
    if not words:
        raise ValueError(f"no known words in {text!r}")
    dim = len(next(iter(embedding.values())))
    return normalize([sum(embedding[w][k] for w in words) / len(words) for k in range(dim)])


def build_index(notes, ids, embedding, model):
    """One index row per note: its id, text, the model that made its vector, the vector, and
    whether it is the current version of its note."""
    return [
        {"id": i, "text": t, "model": model, "vector": note_vector(t, embedding), "current": True}
        for i, t in zip(ids, notes, strict=True)
    ]


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch06-a"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

Number Lucy's words in alphabetical order. "vanilla" gets one number, "vegan" the next, and "chocolate" a much smaller one. Before you run anything below, write down:

- whether "vanilla" is closer to "vegan" or to "chocolate", judged by those numbers;
- whether that closeness says anything about ice cream.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write which word is closer to vanilla by index, and whether it means anything.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### A word's index is not its meaning

The numbers come from spelling. A one-hot vector removes the accident: every word gets a vector of zeros with a single 1, and any two different words have a dot product of zero. Predict the three dot products.

```python tags=["foundation", "worked-example"]
vocab = build_vocab(NOTES)
print(len(vocab), "words:", " ".join(vocab))
for word in ("chocolate", "vanilla", "vegan"):
    print(f"{word:>10} -> index {vocab.index(word)}")
mini = ["chocolate", "vanilla", "vegan"]
for a in mini:
    for b in mini:
        if a < b:
            print(f"one_hot({a}) . one_hot({b}) =", dot(one_hot(a, mini), one_hot(b, mini)))
```

### The embedding lookup is a matrix product

An embedding table has one column per word. Multiplying it by a one-hot vector returns that word's column. Predict the output before you run it.

```python tags=["foundation", "worked-example"]
table = [[0.9, 0.1, 0.8], [0.2, 0.7, 0.3]]  # columns: chocolate, vanilla, vegan
print(matvec(table, one_hot("vegan", mini)))
```

### One real training step

Skip-gram pairs each word with its neighbors. For a real pair, training pushes the logistic function of their dot product toward 1; for a randomly drawn word, toward 0. The error is simply the probability minus the target, and each vector moves by that error times the other vector.

The cell below takes the state of the real run after five epochs and applies one step to "vegan", with its real neighbor "sorbet" and the random word "invoice". Predict whether "vegan" turns toward "sorbet".

```python tags=["foundation", "worked-example"]
vocab, embedding, snapshots, losses = train(NOTES)
before, contexts = snapshots[5]
vegan = before["vegan"]
gradient = [0.0, 0.0]
for word, label in (("sorbet", 1), ("invoice", 0)):
    p = sigmoid(dot(vegan, contexts[word]))
    error = p - label
    print(f"{word:>8}: probability {p:.2f}, target {label}, error {error:+.2f}")
    for k in range(2):
        gradient[k] += error * contexts[word][k]
after = [x - 0.05 * g for x, g in zip(vegan, gradient, strict=True)]
toward_before = cosine(vegan, contexts["sorbet"])
toward_after = cosine(after, contexts["sorbet"])
print(f"cosine to sorbet's context: {toward_before:.3f} -> {toward_after:.3f}")
print(f"loss per pair: {losses[0]:.3f} after epoch 1, {losses[-1]:.3f} after epoch {len(losses)}")
```

### Pool words into notes, and compare three distances

A note's vector is the average of its word vectors, normalized to length one. For unit vectors, squared distance is $2 - 2 \cos$, so cosine, dot product and distance give the same ranking. Predict which note is nearest to "oat vanilla" under each.

```python tags=["foundation", "worked-example"]
query = note_vector("oat vanilla", embedding)
rows = [(i, note_vector(t, embedding)) for i, t in zip(NOTE_IDS, NOTES, strict=True)]
by_cosine = max(rows, key=lambda r: cosine(query, r[1]))[0]
by_dot = max(rows, key=lambda r: dot(query, r[1]))[0]
by_distance = min(rows, key=lambda r: sum((x - y) ** 2 for x, y in zip(query, r[1], strict=True)))[
    0
]
print("nearest by cosine, dot and distance:", by_cosine, by_dot, by_distance)
print(
    "squared distance = 2 - 2 cos:",
    round(sum((x - y) ** 2 for x, y in zip(query, rows[0][1], strict=True)), 6),
    round(2 - 2 * cosine(query, rows[0][1]), 6),
)
```

```python tags=["setup"]
index = build_index(NOTES, NOTE_IDS, embedding, "scratch-2d")
print(len(index), "rows; first:", {k: v for k, v in index[0].items() if k != "vector"})
```

## 2. Construct `search`

`search(index, query, k)` receives the index (a list of rows like the one above), a `query` dictionary with a `model` name and a `vector`, and an integer `k`. It must:

- **refuse** with `ValueError` when any current row's model differs from the query's, or its vector has another length: vectors from different models live in unrelated spaces, and a similarity between them means nothing;
- rank **only current rows**; a superseded version of a note is history, not an answer;
- score each row by the dot product with the query vector, since every vector is normalized;
- return the ids of the `k` best rows, **best first**, breaking ties by id, and all current rows if there are fewer than `k`;
- change neither input.

The starter below ranks every row and returns the worst first. Run the visible cases to see where it fails, then repair it.

```python tags=["exercise", "learner-owned", "ch06-search"]
def search(index, query, k):
    """Return the ids of the k best current rows for the query, best first."""
    current = [row for row in index if row["current"]]
    for row in current:
        if row["model"] != query["model"] or len(row["vector"]) != len(query["vector"]):
            raise ValueError("vectors from another model cannot be compared")
    scored = sorted(current, key=lambda row: (-dot(row["vector"], query["vector"]), row["id"]))
    return [row["id"] for row in scored[:k]]
```

<details><summary>Hint 1 — which rows take part</summary>

Filter to current rows first. Check the model and length of those rows only: a superseded row from an old model is history, and it must not block a search.

</details>

<details><summary>Hint 2 — the order</summary>

`sorted` is ascending. Sort by the negative score, and by the id second, so that equal scores come out in a fixed order: `key=lambda row: (-score, row["id"])`.

</details>

<details><summary>Hint 3 — why refuse instead of skip</summary>

Skipping rows from another model would quietly return fewer or wrong answers. When the embedding model changes, every note must be embedded again. The refusal makes that impossible to forget.

</details>

```python tags=["assessment", "visible"]
import copy


def row(identity, vector, current=True, model="m"):
    return {"id": identity, "text": identity, "model": model, "vector": vector, "current": current}


EAST, NORTH, NORTHEAST = [1.0, 0.0], [0.0, 1.0], [0.6, 0.8]
VISIBLE_CASES = [
    (
        "best first",
        [row("a", EAST), row("b", NORTH), row("c", NORTHEAST)],
        {"model": "m", "vector": EAST},
        2,
        ["a", "c"],
    ),
    (
        "ties by id",
        [row("b", EAST), row("a", EAST), row("c", NORTH)],
        {"model": "m", "vector": EAST},
        2,
        ["a", "b"],
    ),
    (
        "a superseded row is skipped",
        [row("a", EAST, current=False), row("b", NORTHEAST)],
        {"model": "m", "vector": EAST},
        2,
        ["b"],
    ),
    (
        "another model is refused",
        [row("a", EAST), row("b", NORTH, model="other")],
        {"model": "m", "vector": EAST},
        1,
        "ValueError",
    ),
    (
        "another length is refused",
        [row("a", EAST), row("b", [1.0, 0.0, 0.0])],
        {"model": "m", "vector": EAST},
        1,
        "ValueError",
    ),
    (
        "an old model's superseded row does not block",
        [row("a", EAST), row("b", NORTH, current=False, model="old")],
        {"model": "m", "vector": EAST},
        1,
        ["a"],
    ),
    (
        "fewer rows than k",
        [row("a", NORTH), row("b", EAST)],
        {"model": "m", "vector": NORTHEAST},
        5,
        ["a", "b"],
    ),
]


def grade_search(candidate, cases):
    rows = []
    for label, index_rows, query_vector, k, expected in cases:
        supplied_index, supplied_query = copy.deepcopy(index_rows), copy.deepcopy(query_vector)
        try:
            observed = candidate(supplied_index, supplied_query, k)
        except Exception as error:
            observed = type(error).__name__
        passed = (
            observed == expected and supplied_index == index_rows and supplied_query == query_vector
        )
        rows.append(
            {
                "case": label,
                "expected": expected,
                "observed": observed,
                "status": "PASS" if passed else "FAIL",
            }
        )
    return rows


visible_results = grade_search(search, VISIBLE_CASES)
VISIBLE_PASSED = all(r["status"] == "PASS" for r in visible_results)
for visible_row in visible_results:
    print(visible_row["status"], visible_row["case"], "->", visible_row["observed"])
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 3. Build Lucy's index and search it

Once the visible cases pass, the cell below uses *your* `search` on Lucy's twelve notes, embedded with the vectors you trained:

1. It searches for "a vegan treat" and compares the result with keyword matching.
2. Lucy's delivery day moves from Monday to Friday: a new version of the note is added, and the old one stops being current.
3. It searches for "supplier delivers tubs" again, and checks that the old day cannot come back.
4. It tries to search the index with a vector labeled as another model.

Before running it, predict whether a note that never says "vegan" comes back for "a vegan treat".

```python tags=["integration", "learner-path"]
connected = None
if VISIBLE_PASSED:

    def ask(text, k):
        return search(index, {"model": "scratch-2d", "vector": note_vector(text, embedding)}, k)

    keyword = [
        i
        for i, t in zip(NOTE_IDS, NOTES, strict=True)
        if set(tokenize("a vegan treat")) & set(tokenize(t))
    ]
    vegan = ask("a vegan treat", 4)
    before_change = ask("supplier delivers tubs", 1)
    index[8]["current"] = False
    index.append(
        {
            "id": "n13",
            "text": "the supplier delivers tubs on friday",
            "model": "scratch-2d",
            "vector": note_vector("the supplier delivers tubs on friday", embedding),
            "current": True,
        }
    )
    after_change = ask("supplier delivers tubs", 1)
    try:
        search(index, {"model": "all-minilm", "vector": [1.0, 0.0]}, 1)
        mismatch = "ranked"
    except ValueError:
        mismatch = "refused"
    connected = {
        "keyword": keyword,
        "vegan": vegan,
        "before_change": before_change,
        "after_change": after_change,
        "mismatch": mismatch,
    }
    print(json.dumps(connected))
    assert set(vegan) - set(keyword), "every vector result also matched a word"
    assert before_change == ["n9"] and after_change == ["n13"] and mismatch == "refused"
else:
    print("CONNECTION_NOT_READY — repair search, then run again.")
```

Look at the four ids for "a vegan treat". Which of them never use the word "vegan"? They came back because training placed "vegan", "dairy-free" and "sorbet" near each other.

Then trace the delivery note: the Monday version is still in the index, and still near the question, but it is no longer current, so it cannot be ranked.

## 4. Save the handoff

Unit B measures retrieval with the index you built. The handoff records the model's name, the word vectors, and every index row, in a JSON file in your work folder.

```python tags=["handoff"]
ARTIFACT_PATH = Path("ch06-unit-a-handoff-v1.json")
artifact_status = "NOT_WRITTEN"
if connected is not None:
    handoff = {
        "unit": "ch06-a",
        "status": "COMPLETED",
        "model": "scratch-2d",
        "words": embedding,
        "index": index,
    }
    ARTIFACT_PATH.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact_status = "WRITTEN"
    print(ARTIFACT_PATH)
else:
    print("HANDOFF_NOT_WRITTEN")
```

## Exit ticket

Answer three questions:

- Why does a one-hot vector make no mistakes about similarity, and why is that not enough?
- Why must `search` refuse a vector from another model instead of skipping it?
- Which observation proves that the Monday delivery note can no longer be the answer?

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch06-a",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": artifact_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: fuse two rankings

**Allow fifteen minutes:** three to predict, eight to implement and trace, and four for a case of your own.

Word matching finds exact codes; vectors find paraphrases. A search system often keeps both rankings and combines them. **Reciprocal rank fusion** gives each id the sum of $1/(60 + \text{rank})$ over the rankings that list it, with ranks starting at 1.

`transfer_fuse(rankings, k)` receives a list of rankings (each a list of ids, best first) and an integer `k`. Return the `k` best ids by fused score, best first, breaking ties by id. An id missing from a ranking gets nothing from it. Do not change the input.

Write your expected values before you run the table. The driver passes your function in directly, copies the inputs, and checks that they come back unchanged.

<details><summary>Hint — why ranks, not scores</summary>
A word score and a cosine are on different scales, so adding them favors whichever is larger. Ranks are on the same scale. The 60 keeps the first few ranks from dominating completely.
</details>

```python tags=["exercise", "transfer-owned"]
def transfer_fuse(rankings, k):
    score = {}
    for ranking in rankings:
        for rank, identity in enumerate(ranking, start=1):
            score[identity] = score.get(identity, 0.0) + 1 / (60 + rank)
    return sorted(score, key=lambda identity: (-score[identity], identity))[:k]
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("one ranking passes through", [[["n3", "n1", "n2"]], 2], ["n3", "n1"]),
    ("agreement wins", [[["n1", "n2"], ["n1", "n3"]], 1], ["n1"]),
    (
        "top of one beats middle of both",
        [[["n1", "n2", "n3"], ["n3", "n2", "n1"]], 3],
        ["n1", "n3", "n2"],
    ),
    ("an id in one ranking only", [[["n1"], ["n2", "n1"]], 2], ["n1", "n2"]),
    ("equal scores by id", [[["n2"], ["n1"]], 2], ["n1", "n2"]),
]


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        try:
            actual = candidate(*supplied)
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


transfer_observations = run_transfer(transfer_fuse, TRANSFER_CASES)
TRANSFER_PASSED = all(r["passed"] for r in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add one case with an expected outcome you worked out independently, and rerun the driver. Then, in a temporary copy, add the raw scores of two rankers instead of their reciprocal ranks, and name a case where one ranker's larger scale decides every result.


## Instructor explanation and additional transfer cases

Three misconceptions come up.

**"A superseded row is a worse row."** It is not worse; it is wrong. The Monday note is still near "supplier delivers tubs", which is exactly the danger. Only a flag set when the new version arrives keeps it out, which is why Part B of the chapter sets it in the same transaction.

**"A mismatched vector just scores low."** A cosine between vectors from two models is a number with no meaning. It can be high. The starter ranked it anyway; the repair refuses.

**"Middle of both beats top of one."** In reciprocal rank fusion, $1/61 + 1/63$ is slightly more than $2/62$, so an id first in one ranking and third in the other beats one second in both. Fusion rewards a strong vote over a lukewarm consensus, by a little.

The cases below add a longer list with a duplicated id across rankings and a request for more ids than exist.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    ("more ids than exist", [[["n1"], ["n1"]], 5], ["n1"]),
    ("three rankings", [[["n1", "n2"], ["n2", "n1"], ["n2"]], 2], ["n2", "n1"]),
]
instructor_observations = run_transfer(transfer_fuse, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(r["passed"] for r in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
holdout_index = [
    row("x", [0.8, 0.6]),
    row("y", [0.6, 0.8]),
    row("z", [1.0, 0.0], current=False),
    row("w", [0.0, 1.0], model="old", current=False),
]
assert search(holdout_index, {"model": "m", "vector": [1.0, 0.0]}, 3) == ["x", "y"]
assert search(holdout_index, {"model": "m", "vector": [0.0, 1.0]}, 1) == ["y"]
try:
    search(
        holdout_index + [row("v", [1.0, 0.0], model="new")], {"model": "m", "vector": [1.0, 0.0]}, 1
    )
    holdout_refused = False
except ValueError:
    holdout_refused = True
assert holdout_refused
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch06-a"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

These vectors were trained on twelve short notes, with two numbers per word. They show the mechanism; they are not a model of meaning. Unit B puts a real embedding model beside them.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch06-a",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch06-a-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch06-a",
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
