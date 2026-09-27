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
    lesson_id: memory
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch05-b-retrieval-and-recall-solution
    self_contained_runtime: true
    source_basis: chapter-5-manuscript
    source_unit: ch05-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch05-b
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

# Chapter 5, Unit B: Measure a retriever before trusting it

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-26**

This is the worked edition of Chapter 5, Unit B. It contains:

- complete answers;
- the instructor explanation;
- holdout cases that the student edition does not show.

Use it after a first attempt, or to rehearse the session. It runs on Google Colab (Python 3.13) or any local Python 3.12+ kernel, using only the standard library.

| Minutes | Dedicated work | Saved evidence |
| --- | --- | --- |
| 0–10 | Predict which questions the colleague's search misses | Written prediction |
| 10–30 | Ranking metrics and the three ideas behind BM25 | Worked outputs and handoff |
| 30–60 | Construct `bm25_scores` and pass the visible cases | Learner code and grade table |
| 60–70 | Evaluate three rankers on Lucy's labeled questions | Recall table and negative control |
| 70–85 | Changed-constraint task: mean reciprocal rank | Transfer results |
| 85–90 | Explain the result and save evidence | Retained submission |


## Run the self-contained setup

The unit needs only Python's standard library. The collapsed cell supplies:

- `NOTES`: forty of Lucy's shop notes, the agent's memory;
- `QUESTIONS`: sixteen questions, each labeled with the one note that answers it (and the expected answer, unused here). The last four are paraphrases that share few words with their note;
- `terms`, the tokenizer, and the colleague's `overlap_scores`, plus `recent_scores`, which ranks the newest notes first.

These are the notes and questions of the chapter's experiment. Run setup on every fresh kernel. Your saved work lives in `practical-work/ch05-b`.

<details><summary>Supplied setup: Lucy's notes, labeled questions and two simple rankers</summary>

```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("This unit needs Python 3.12 or newer; Google Colab runs Python 3.13.")

if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd()
    COURSE_ROOT = Path(tempfile.mkdtemp(prefix="ch05-course-"))

NOTES = [
    "Lucy asked for deliveries in the afternoon, because she opens the shop alone in the morning.",
    "The vanilla supplier is Hartwell Dairy, and its sales contact is Priya.",
    "Hartwell Dairy charges 250 cents for a tub of vanilla.",
    "Strawberry comes from Meadow Farm at 275 cents a tub.",
    "Chocolate comes from Cocoa Works at 300 cents a tub.",
    "Mango sorbet is seasonal and is only sold from June to August.",
    "The freezer holds at most forty tubs in total.",
    "The shop opens at nine and closes at six on weekdays.",
    "On Saturdays the shop opens at ten and closes at four.",
    "The shop is closed on Sundays.",
    "The reorder point for vanilla is eight tubs.",
    "The reorder point for strawberry is five tubs.",
    "The reorder point for chocolate is six tubs.",
    "Lucy approves every order above 2000 cents herself.",
    "Orders under 2000 cents may be drafted automatically but never sent without approval.",
    "Meadow Farm delivers only on Tuesdays and Fridays.",
    "Hartwell Dairy needs orders by Monday evening for Tuesday delivery.",
    "Cocoa Works has a minimum order of ten tubs.",
    "The morning brief goes to Lucy's phone at eight.",
    "Lucy prefers short briefs with the numbers first.",
    "Tom works in the shop on Saturdays.",
    "Tom is allergic to nuts, so pistachio is not stocked.",
    "The card reader was replaced in March after it stopped accepting contactless payments.",
    "The shop's delivery door is at the back, on Mill Lane.",
    "Last summer vanilla sold about twelve tubs a week.",
    "Strawberry sells best when the weather is warm.",
    "A school group visits every second Thursday during term.",
    "The school group usually buys about forty scoops.",
    "Lucy wants a warning when any flavor falls below its reorder point.",
    "The accountant, Marcus, receives the monthly spending report on the first.",
    "Spending reports list approved orders and reserved amounts separately.",
    "The freezer was serviced in April and runs at minus eighteen degrees.",
    "If the freezer alarm sounds, Lucy must be called immediately.",
    "Lucy's phone number for urgent calls is kept in the operator settings, not in notes.",
    "Pistachio was tried once in 2024 and removed after Tom joined.",
    "Customers asked for a dairy-free chocolate; Cocoa Works offers one at 320 cents a tub.",
    "The shop's loyalty card gives a free scoop after nine purchases.",
    "Waffle cones come from Crisp & Co. in boxes of two hundred.",
    "Lucy does not want the agent to reply to customer reviews.",
    "Delivery drivers should ring the bell at the back door and wait.",
]
QUESTIONS = [
    ("When should deliveries arrive?", {0}, "afternoon"),
    ("Who is the sales contact at Hartwell Dairy?", {1}, "Priya"),
    ("How much does a tub of strawberry cost?", {3}, "275"),
    ("How many tubs can the freezer hold?", {6}, ("forty", "40")),
    ("What time does the shop open on Saturdays?", {8}, ("ten", "10")),
    ("What is the reorder point for chocolate?", {12}, ("six", "6")),
    ("Above what amount must Lucy approve an order herself?", {13}, "2000"),
    ("On which days does Meadow Farm deliver?", {15}, ("Tuesday", "Tuesdays")),
    ("What is the minimum order at Cocoa Works?", {17}, ("ten", "10")),
    ("When does the morning brief arrive?", {18}, ("eight", "8")),
    ("Why is pistachio not stocked?", {21}, "allergic"),
    ("Who receives the monthly spending report?", {29}, "Marcus"),
    # Paraphrases: few words in common with the relevant note.
    ("At what hour should the supplier's van turn up?", {0}, "afternoon"),
    ("How cold is the freezer kept?", {31}, ("eighteen", "18")),
    ("Which company makes our cones?", {37}, "Crisp"),
    ("Is there a vegan option for the cocoa flavor, and what does it cost?", {35}, "320"),
]

WORD = re.compile(r"[a-z0-9]+")


def terms(text):
    return WORD.findall(text.lower())


def overlap_scores(query, documents):
    """The colleague's ranker: how many distinct words a note shares with the request."""
    wanted = set(terms(query))
    return [len(wanted & set(terms(d))) for d in documents]


def recent_scores(query, documents):
    """Newest first: the last note scores highest."""
    return list(range(len(documents)))


def ranking(scores):
    return sorted(range(len(scores)), key=lambda i: -scores[i])


COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch05-b"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
print("Python", sys.version.split()[0])
print("Save your work here:", COURSE_WORK)
```

</details>


## Commit to a prediction before the examples

The colleague's ranker counts shared words. Read the sixteen questions and their notes in `QUESTIONS` and `NOTES`, then write down:

- which questions you expect it to miss in its top three;
- whether you expect BM25 to fix all of them.

```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "List the questions word overlap will miss, and whether BM25 fixes them.",
    "reason": "Name the rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Retrieval is ranking, and ranking has metrics

A retriever orders the notes for a request. The notes that answer it are **relevant**; here, each question's relevant note is labeled in advance. Two measures matter most to an agent:

- **Recall@k:** the share of relevant notes in the top $k$. A relevant note outside the top $k$ never reaches the model, so a missed recall is a question the agent cannot answer from memory.
- **Reciprocal rank:** $1/r$ for the first relevant note at position $r$, or 0 if none is returned. It rewards putting the answer first.

Predict both for the ranking in the cell before you run it.

```python tags=["foundation", "worked-example"]
intro_ranked, intro_relevant = [4, 1, 7, 2], {1}
intro_recall = sum(i in intro_relevant for i in intro_ranked[:3]) / len(intro_relevant)
intro_first = next(p for p, i in enumerate(intro_ranked, start=1) if i in intro_relevant)
intro_rr = 1 / intro_first
print("recall@3", intro_recall, "reciprocal rank", intro_rr)
```

### Three ideas behind BM25

Counting shared words treats "the" like "Hartwell". Three refinements fix that.

1. **Rare terms matter more.** A term in $n_t$ of $N$ notes is weighted by its inverse document frequency, $\mathrm{idf}(t) = \ln\bigl(1 + \frac{N - n_t + 0.5}{n_t + 0.5}\bigr)$. A term in every note is worth almost nothing.
2. **Repetition saturates.** A term appearing $f$ times contributes $\frac{f(k_1 + 1)}{f + k_1}$, which rises with $f$ but never exceeds $k_1 + 1$.
3. **Long notes are discounted.** $k_1$ in the denominator becomes $k_1\bigl(1 - b + b\,\frac{|d|}{\overline{|d|}}\bigr)$, where $|d|$ is the note's length in terms and $\overline{|d|}$ the average.

$$
\mathrm{BM25}(q, d) = \sum_{t \in q} \mathrm{idf}(t)\,\frac{f_{t,d}\,(k_1 + 1)}{f_{t,d} + k_1\left(1 - b + b\,\frac{|d|}{\overline{|d|}}\right)}, \qquad k_1 = 1.5,\ b = 0.75.
$$

Each distinct query term counts once; a term absent from a note contributes nothing.

## Choose an explicit starting point

This unit starts from Unit A's work. To use your own, replace `None` with the path to your `practical-work/ch05-a/ch05-unit-a-handoff-v1.json`. Leave it as `None` to start from the supplied reference. Your submission records which you chose.

```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

```python tags=["setup", "independent-reference-start"]
import hashlib
import shutil

COURSE_INPUT = COURSE_WORK / "ch05-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    reference_source = (
        "def remember(db, session, name, value, source):\n    ...  # Supplied reference.\n"
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

Unit A decided what Lucy's memory keeps. This unit decides which of those records a given request sees. A record that is stored but never retrieved is, for that request, not remembered at all.

## Main practical: construct, connect and challenge

## 1. Construct `bm25_scores`

`bm25_scores(query, documents, k1=1.5, b=0.75)` must return one score per document, by the formula above, using `terms` to split text. It must also:

- return an empty list for no documents;
- raise `ValueError` when `k1` is negative or `b` lies outside $[0, 1]$.

The starter below is the colleague's overlap count. Run the visible cases, then repair it.

```python tags=["exercise", "learner-owned", "ch05-bm25-scores"]
from collections import Counter


def bm25_scores(query, documents, k1=1.5, b=0.75):
    """Score each document for the query; higher is more relevant."""
    if k1 < 0 or not 0 <= b <= 1:
        raise ValueError("k1 must be at least 0, and b between 0 and 1")
    tokenized = [terms(d) for d in documents]
    if not tokenized:
        return []
    average = sum(len(t) for t in tokenized) / len(tokenized) or 1.0
    containing = Counter(term for t in tokenized for term in set(t))
    scores = []
    for tokens in tokenized:
        frequency = Counter(tokens)
        score = 0.0
        for term in set(terms(query)):
            f = frequency[term]
            if f:
                idf = math.log(
                    1 + (len(tokenized) - containing[term] + 0.5) / (containing[term] + 0.5)
                )
                score += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * len(tokens) / average))
        scores.append(score)
    return scores
```

<details><summary>Hint 1 — the pieces</summary>

Tokenize every document once. Count, for each term, how many documents contain it: that is $n_t$. The average length is the mean number of terms per document.

</details>

<details><summary>Hint 2 — the first visible case</summary>

With three documents of equal length and a term in only one of them, the length factor is 1 and the saturation term is $\frac{1 \cdot 2.5}{1 + 1.5} = 1$. The score is just $\mathrm{idf} = \ln(1 + 2.5/1.5)$.

</details>

```python tags=["assessment", "visible"]
import copy


def outcome(call):
    try:
        return [round(x, 6) for x in call()]
    except Exception as error:
        return type(error).__name__


VISIBLE_CASES = [
    (
        "a term in one of three equal notes scores its idf",
        lambda: bm25_scores("a", ["a b", "b c", "c d"]),
        [round(math.log(1 + 2.5 / 1.5), 6), 0.0, 0.0],
    ),
    (
        "eight repeats score less than eight times one",
        lambda: bm25_scores("a", ["a a a a a a a a", "a b c d e f g h"]),
        [round(math.log(1.2) * 8 * 2.5 / 9.5, 6), round(math.log(1.2), 6)],
    ),
    (
        "the rare shared term wins",
        lambda: ranking(
            bm25_scores("the note hartwell", ["hartwell", "the note", "the other note"])
        )[:1],
        [0],
    ),
    (
        "a shorter note with the same term ranks higher",
        lambda: ranking(bm25_scores("mint", ["mint tea and cake and coffee", "mint"]))[:1],
        [1],
    ),
    ("no documents", lambda: bm25_scores("a", []), []),
    ("a negative k1 is refused", lambda: bm25_scores("a", ["a"], k1=-1), "ValueError"),
    ("b above one is refused", lambda: bm25_scores("a", ["a"], b=1.5), "ValueError"),
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

## 2. Connect: evaluate three rankers on Lucy's labeled questions

The cell below ranks the forty notes for every question with your `bm25_scores`, with the colleague's overlap count and with "newest first". It reports recall@3 on the twelve direct questions and on the four paraphrases.

Your BM25 must find every direct question's note in its top three. "Newest first" is the **negative control**: an evaluation that cannot tell it apart from a real ranker proves nothing.

Predict each ranker's recall on the paraphrases.

```python tags=["integration", "learner-path"]
connected = None
PARAPHRASES = set(range(12, 16))


def recall_at_3(scorer, keep):
    hits = [
        relevant & set(ranking(scorer(question, NOTES))[:3]) != set()
        for index, (question, relevant, _) in enumerate(QUESTIONS)
        if keep(index)
    ]
    return round(sum(hits) / len(hits), 3)


if VISIBLE_PASSED:
    table = {}
    for name, scorer in (
        ("bm25", bm25_scores),
        ("word_overlap", overlap_scores),
        ("newest_first", recent_scores),
    ):
        table[name] = {
            "direct": recall_at_3(scorer, lambda i: i not in PARAPHRASES),
            "paraphrases": recall_at_3(scorer, lambda i: i in PARAPHRASES),
        }
    finds_direct = table["bm25"]["direct"] == 1.0
    control_rejected = table["newest_first"]["direct"] < 0.2
    missed = [
        question
        for index, (question, relevant, _) in enumerate(QUESTIONS)
        if not relevant & set(ranking(bm25_scores(question, NOTES))[:3])
    ]
    connected = {
        "table": table,
        "finds_direct": finds_direct,
        "negative_control_rejected": control_rejected,
        "bm25_missed": missed,
    }
    for name, row in table.items():
        print(
            f"{name:13} recall@3 direct {row['direct']:.3f}  paraphrases {row['paraphrases']:.3f}"
        )
    print("BM25 finds every direct question's note:", finds_direct)
    print("negative control rejected:", control_rejected)
    print("BM25 misses:", missed)
else:
    print("CONNECTION_NOT_READY — repair bm25_scores, then run again.")
```

Both word-based rankers are perfect on direct questions, and both fail paraphrases: "At what hour should the supplier's van turn up?" shares no useful word with "Lucy asked for deliveries in the afternoon". **No lexical ranker can find a note that says the same thing in different words.** That needs an embedding model, which maps meaning rather than words to vectors. It is also why the chapter measured whether sending the whole memory would be better: for forty notes, it was.

## Exit ticket

Answer three questions:

- Why is recall@k, not precision@k, the measure that decides what an agent can answer from memory?
- Which of BM25's three ideas moved the rare-term case, and which moved the repeated-term case?
- Your colleague "tried every question" and saw good answers. Name two ways a good-looking answer can hide a retrieval miss.

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch05-b",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: mean reciprocal rank

**Allow fifteen minutes:** three to predict, eight to implement and check, and four for a case of your own.

Recall@3 says whether the note arrived. Reciprocal rank says how early. Averaged over many requests, it is the **mean reciprocal rank** (MRR).

Implement `mean_reciprocal_rank(rankings, relevant_sets)`:

- `rankings` is a list of ranked index lists, one per request; `relevant_sets` the matching sets of relevant indices;
- each request scores $1/r$ for the first relevant index at position $r$ (from 1), or 0 if none appears;
- return the mean over requests;
- raise `ValueError` when the lists are empty or of different lengths, or when any relevant set is empty;
- do not change the inputs.

<details><summary>Hint — positions start at one</summary>
<code>enumerate(ranked, start=1)</code> gives each index with its position.
</details>

```python tags=["exercise", "transfer-owned"]
def mean_reciprocal_rank(rankings, relevant_sets):
    if not rankings or len(rankings) != len(relevant_sets) or not all(relevant_sets):
        raise ValueError("need matching, nonempty rankings and relevant sets")
    total = 0.0
    for ranked, relevant in zip(rankings, relevant_sets, strict=True):
        total += next((1 / p for p, i in enumerate(ranked, start=1) if i in relevant), 0.0)
    return total / len(rankings)
```

```python tags=["assessment", "transfer-invocation"]
TRANSFER_CASES = [
    ("first at position two", [[[3, 1, 2]], [{1}]], 0.5),
    ("first and second", [[[0], [1, 0]], [{0}, {0}]], 0.75),
    ("never returned", [[[2, 3]], [{9}]], 0.0),
    ("the first of several relevant counts", [[[5, 4, 3]], [{4, 3}]], 0.5),
    ("no requests are refused", [[], []], {"raises": "ValueError"}),
    ("mismatched lists are refused", [[[1]], [{1}, {2}]], {"raises": "ValueError"}),
    ("an empty relevant set is refused", [[[1]], [set()]], {"raises": "ValueError"}),
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


transfer_observations = run_transfer(mean_reciprocal_rank, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add a case with an expected value you worked out by hand, and rerun the driver. Then compute MRR over the sixteen questions for BM25 and for word overlap, using your function and `ranking`. The chapter measured 0.791 and 0.804: overlap puts the answer first slightly more often, although BM25 has the better recall. Explain how both can be true, and which you would optimize for an agent that sends three notes.


## Instructor explanation and additional transfer cases

Three misconceptions come up.

**"It worked on every question I tried."** The questions a developer thinks of share words with the notes, because the developer wrote both. Paraphrases are what users actually send. Labeled questions, including paraphrases, are the only honest test.

**"Better MRR means a better retriever."** For an agent that sends the top three, the order within the three matters little; whether the note is among them matters a lot. Choose the metric by how the ranking is used.

**"BM25 understands the question."** It matches words. Its gain over overlap is from weighting rare words and discounting long notes, not from meaning. On Lucy's short notes, the length discount rarely matters.

The cases below add ties and a longer ranking.

```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    (
        "third, fourth and not found",
        [[[1, 2, 3], [5, 6, 7, 8], [1]], [{3}, {8}, {9}]],
        round((1 / 3 + 1 / 4) / 3, 6),
    ),
    ("all first", [[[1], [2]], [{1}, {2}]], 1.0),
]
instructor_observations = run_transfer(mean_reciprocal_rank, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_observations)
```

```python tags=["instructor-check", "core-holdout"]
# An independent BM25, written differently, must agree with the learner's on every question.
def reference_bm25(query, documents, k1=1.5, b=0.75):
    bags = [Counter(terms(d)) for d in documents]
    lengths = [sum(bag.values()) for bag in bags]
    mean_length = sum(lengths) / len(lengths)
    out = []
    for bag, length in zip(bags, lengths, strict=True):
        s = 0.0
        for term in set(terms(query)):
            n = sum(1 for other in bags if term in other)
            if bag[term]:
                idf = math.log((len(bags) - n + 0.5) / (n + 0.5) + 1)
                s += (
                    idf
                    * bag[term]
                    * (k1 + 1)
                    / (bag[term] + k1 * (1 - b + b * length / mean_length))
                )
        out.append(s)
    return out


for holdout_question, _, _ in QUESTIONS:
    for mine, theirs in zip(
        bm25_scores(holdout_question, NOTES), reference_bm25(holdout_question, NOTES), strict=True
    ):
        assert math.isclose(mine, theirs, abs_tol=1e-12)
assert (
    connected is not None and connected["finds_direct"] and connected["negative_control_rejected"]
)
holdout_mrr = mean_reciprocal_rank(
    [ranking(bm25_scores(q, NOTES)) for q, _, _ in QUESTIONS], [r for _, r, _ in QUESTIONS]
)
print("BM25 MRR over the sixteen questions:", round(holdout_mrr, 3))
assert round(holdout_mrr, 3) == 0.791
print("HOLDOUT_RESULT=" + json.dumps({"status": "PASSED", "unit": "ch05-b"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill in the prediction notes and your explanation before saving. Include:

- the exact observed value, and the input that caused it;
- your code's invocation point;
- one failed hypothesis;
- the strongest claim the evidence still cannot support.

Sixteen labeled questions over forty notes is a small evaluation. It shows how lexical ranking fails, not how often it would fail on Lucy's real requests.

```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch05-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch05-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch05-b",
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
