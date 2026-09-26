# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 5 experiment: should an agent send its whole memory, or retrieve from it?

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py \
      --out ch05-retrieval-receipt.json [--live | --regrade RECEIPT]

Offline, it ranks a memory of forty shop notes for sixteen questions with BM25, with plain word
overlap and with "the most recent notes", and reports recall@3 and mean reciprocal rank against
authored relevance labels. Four questions are paraphrases that share few words with their note.
With --live, a real model (served by Ollama on localhost) is asked:
  - position: a code is planted at five depths of filler contexts of about 1,000 and 4,000 tokens,
    eight trials each, for qwen2.5:0.5b and qwen2.5:1.5b; is it recalled at every depth?
  - retrieval against everything: each question answered with all forty notes in context, and with
    only BM25's top three, scoring the answer and recording the prompt tokens and prefill time.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import re
import runpy
import statistics
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
LEARN = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch05_retrieval_learner.py")
)

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
PARAPHRASES = set(range(12, 16))


def graded(answer, expected):
    """Whole-word match of any accepted form. The first version matched substrings of one form,
    which marked "8 AM" wrong for "eight" and would have accepted "often" for "ten"."""
    forms = (expected,) if isinstance(expected, str) else expected
    return any(re.search(rf"\b{re.escape(form)}\b", answer, re.I) for form in forms)


def overlap_scores(query, documents):
    q = set(LEARN["terms"](query))
    return [len(q & set(LEARN["terms"](d))) for d in documents]


def recent_scores(query, documents):
    return list(range(len(documents)))


def evaluate_ranker(name, scorer):
    rows = []
    for index, (question, relevant, _) in enumerate(QUESTIONS):
        ranked = LEARN["ranking"](scorer(question, NOTES))
        rows.append(
            {
                "question": index,
                "recall_at_3": LEARN["recall_at_k"](ranked, relevant, 3),
                "reciprocal_rank": LEARN["reciprocal_rank"](ranked, relevant),
            }
        )

    def mean(key, keep=lambda r: True):
        chosen = [r[key] for r in rows if keep(r)]
        return round(sum(chosen) / len(chosen), 3)

    return {
        "ranker": name,
        "recall_at_3": mean("recall_at_3"),
        "mrr": mean("reciprocal_rank"),
        "recall_at_3_direct": mean("recall_at_3", lambda r: r["question"] not in PARAPHRASES),
        "recall_at_3_paraphrase": mean("recall_at_3", lambda r: r["question"] in PARAPHRASES),
    }


def chat(model, system, user):
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 40},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=300) as response:
        return json.loads(response.read())


FILLER = [
    "A customer asked about {n} scoops for a party.",
    "The {w} delivery was checked in at {h} o'clock.",
    "Tom wiped down counter {n} before lunch.",
    "The till showed {n} card payments by {h} o'clock.",
    "A tourist asked for directions to the {w} market.",
    "Lucy noted that {n} cones were used on {w}.",
    "The freezer door was opened {n} times in the {w} hour.",
]
WORDS = ["morning", "noon", "evening", "north", "river", "station", "harbor", "garden"]


def haystack(rng, sentences, depth, code):
    notes = []
    for _ in range(sentences):
        template = rng.choice(FILLER)
        notes.append(
            template.format(n=rng.randint(2, 90), w=rng.choice(WORDS), h=rng.randint(9, 17))
        )
    needle = f"The back-door code for deliveries is {code}."
    notes.insert(round(depth * sentences), needle)
    return " ".join(notes)


def position_test(runs):
    results = []
    for model in ("qwen2.5:0.5b", "qwen2.5:1.5b"):
        for sentences in (80, 330):
            for depth in (0.0, 0.25, 0.5, 0.75, 1.0):
                correct, tokens = 0, []
                for trial in range(8):
                    rng = random.Random(1000 * sentences + 100 * trial + int(depth * 4))
                    code = str(rng.randint(1000, 9999))
                    context = haystack(rng, sentences, depth, code)
                    reply = chat(
                        model,
                        "Answer from the notes. Reply with the number only.",
                        f"Notes: {context}\n\nWhat is the back-door code for deliveries?",
                    )
                    answer = reply["message"]["content"]
                    correct += code in answer
                    tokens.append(reply["prompt_eval_count"])
                    runs.append(
                        {
                            "kind": "position",
                            "model": model,
                            "sentences": sentences,
                            "depth": depth,
                            "code": code,
                            "answer": answer,
                            "prompt_tokens": reply["prompt_eval_count"],
                        }
                    )
                results.append(
                    {
                        "model": model,
                        "prompt_tokens": round(statistics.median(tokens)),
                        "depth": depth,
                        "recalled": f"{correct}/8",
                    }
                )
                print(json.dumps(results[-1]), flush=True)
    return results


def retrieval_against_everything(runs, model="qwen2.5:1.5b"):
    system = "Answer the question from the shop notes, in one short sentence."
    rows = []
    for index, (question, relevant, expected) in enumerate(QUESTIONS):
        top = LEARN["ranking"](LEARN["bm25_scores"](question, NOTES))[:3]
        for mode, chosen in (("everything", range(len(NOTES))), ("bm25_top3", top)):
            notes = "\n".join(f"- {NOTES[i]}" for i in chosen)
            reply = chat(model, system, f"Shop notes:\n{notes}\n\nQuestion: {question}")
            answer = reply["message"]["content"]
            row = {
                "question": index,
                "mode": mode,
                "correct": graded(answer, expected),
                "relevant_in_context": bool(relevant & set(chosen)),
                "prompt_tokens": reply["prompt_eval_count"],
                "prefill_seconds": reply["prompt_eval_duration"] / 1e9,
            }
            rows.append(row)
            runs.append({"kind": "retrieval", "answer": answer, **row})
    return {"model": model, "summary": summarize(rows)}


def summarize(rows):
    summary = {}
    for mode in ("everything", "bm25_top3"):
        chosen = [r for r in rows if r["mode"] == mode]
        summary[mode] = {
            "correct": f"{sum(r['correct'] for r in chosen)}/{len(chosen)}",
            "correct_on_paraphrases": "{}/4".format(
                sum(r["correct"] for r in chosen if r["question"] in PARAPHRASES)
            ),
            "relevant_note_in_context": "{}/{}".format(
                sum(r["relevant_in_context"] for r in chosen), len(chosen)
            ),
            "mean_prompt_tokens": round(statistics.mean(r["prompt_tokens"] for r in chosen)),
            "mean_prefill_seconds": round(statistics.mean(r["prefill_seconds"] for r in chosen), 3),
        }
    return summary


def regrade(receipt):
    """Score a live run's retained answers again with the current grader; no model is called."""
    runs = [r for r in receipt["runs"] if r["kind"] == "retrieval"]
    for run in runs:
        run["correct"] = graded(run["answer"], QUESTIONS[run["question"]][2])
    receipt["retrieval_against_everything"]["summary"] = summarize(runs)
    receipt["rankers"] = [
        evaluate_ranker("bm25", LEARN["bm25_scores"]),
        evaluate_ranker("word_overlap", overlap_scores),
        evaluate_ranker("most_recent", recent_scores),
    ]
    receipt["regraded"] = (
        "retained answers scored again by graded(), and the offline rankers recomputed; "
        "the model was not called"
    )
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--regrade", type=Path, help="re-score the answers retained in a receipt")
    args = parser.parse_args()
    if args.regrade:
        receipt = regrade(json.loads(args.regrade.read_text()))
        args.out.write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt["retrieval_against_everything"], indent=2))
        return
    started = time.time()
    receipt = {
        "schema": 1,
        "experiment": "ch05-retrieval-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "notes": len(NOTES),
        "questions": len(QUESTIONS),
        "rankers": [
            evaluate_ranker("bm25", LEARN["bm25_scores"]),
            evaluate_ranker("word_overlap", overlap_scores),
            evaluate_ranker("most_recent", recent_scores),
        ],
    }
    runs = []
    if args.live:
        receipt["position"] = position_test(runs)
        receipt["retrieval_against_everything"] = retrieval_against_everything(runs)
        receipt["runs"] = runs
    receipt["seconds"] = round(time.time() - started, 1)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    json.dump({k: v for k, v in receipt.items() if k != "runs"}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
