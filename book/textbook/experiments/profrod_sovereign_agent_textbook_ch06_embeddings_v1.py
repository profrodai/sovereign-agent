# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 6 experiment: what embeddings find that words cannot, and what they cost.

  uv run python book/textbook/experiments/profrod_sovereign_agent_textbook_ch06_embeddings_v1.py \
      --out ch06-embeddings-receipt.json

Uses a real embedding model, all-minilm (384 dimensions), served by Ollama on localhost.
  - Retrieval: Chapter 5's forty notes and its sixteen questions, plus eleven new paraphrases of
    the direct questions written to share no content word with their note. Four rankers:
    BM25 (Chapter 5), word vectors trained from scratch on the forty notes only, all-minilm, and
    reciprocal rank fusion of BM25 and all-minilm. Recall@1, recall@3 and reciprocal rank.
  - Failure probes: three order codes that are permutations of the same digits, sentences
    that differ only by a negation, and a delivery rule that has changed.
  - Approximate search: 2,000 sentences from this book's own chapters and 100 held-out queries.
    Exact top-10 against a navigable small-world graph searched with several beam widths; recall@10
    against the number of vectors compared.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import re
import runpy
import statistics
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
VEC = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch06_embeddings_learner.py")
)
RETRIEVAL = runpy.run_path(
    str(ROOT / "book/textbook/learner/profrod_sovereign_agent_ch05_retrieval_learner.py")
)
MEMORY = runpy.run_path(
    str(ROOT / "book/textbook/experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py")
)
MODEL = "all-minilm"
NOTES = MEMORY["NOTES"]
# Chapter 5's questions, then one new paraphrase of each direct question except the first (whose
# paraphrase Chapter 5 already has), written to share no content word with its note.
NEW_PARAPHRASES = [
    ("Which person handles our purchases at the cream company?", {1}),
    ("What do we pay per container of the red berry flavor?", {3}),
    ("What is the largest number of containers our cold storage can fit?", {6}),
    ("How early can customers come in at the weekend?", {8}),
    ("How low may the cocoa ice cream run before we buy more?", {12}),
    ("Past what spend does the owner need to sign off personally?", {13}),
    ("Which weekdays does the berry grower bring stock?", {15}),
    ("What is the smallest purchase the chocolate maker accepts?", {17}),
    ("At what time does the daily summary reach the owner's mobile?", {18}),
    ("Why don't we sell the green nut flavor?", {21}),
    ("Who gets the summary of what we spent each month?", {29}),
]
PROBES = {
    "codes": {
        "notes": [
            "Order code PX-4471 is the vanilla case.",
            "Order code PX-4417 is the strawberry case.",
            "Order code PX-7144 is the chocolate case.",
        ],
        "queries": ["PX-4471", "PX-4417", "PX-7144"],
    },
    "negation": [
        (
            "Mango sorbet contains dairy.",
            "Mango sorbet contains no dairy.",
            "Mango sorbet is made with milk.",
        ),
        (
            "The freezer alarm is on.",
            "The freezer alarm is not on.",
            "The freezer alarm is sounding.",
        ),
        (
            "Tom works on Saturdays.",
            "Tom never works on Saturdays.",
            "Tom is in the shop on Saturdays.",
        ),
        (
            "Lucy approved the order.",
            "Lucy did not approve the order.",
            "Lucy signed off on the order.",
        ),
        (
            "The supplier delivers on Tuesdays.",
            "The supplier does not deliver on Tuesdays.",
            "Tuesday is the supplier's delivery day.",
        ),
    ],
    "stale": {
        "old": "Meadow Farm delivers only on Tuesdays and Fridays.",
        "new": "From October, Meadow Farm delivers only on Wednesdays.",
        "query": "When does Meadow Farm deliver?",
    },
}


def embed(texts, batch=64):
    vectors = []
    for start in range(0, len(texts), batch):
        body = {"model": MODEL, "input": list(texts[start : start + batch])}
        request = Request(
            "http://127.0.0.1:11434/api/embed",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=300) as response:
            vectors.extend(json.loads(response.read())["embeddings"])
    return vectors


def questions():
    rows = [
        (q, set(r), "direct" if i < 12 else "paraphrase", "chapter 5")
        for i, (q, r, _) in enumerate(MEMORY["QUESTIONS"])
    ]
    rows += [(q, set(r), "paraphrase", "chapter 6") for q, r in NEW_PARAPHRASES]
    return rows


def overlap(question, note):
    """Content terms a question shares with its note, by Chapter 5's BM25 tokenization."""
    return sorted(set(RETRIEVAL["terms"](question)) & set(RETRIEVAL["terms"](note)))


def retrieval():
    rows = questions()
    note_vectors = embed(NOTES)
    query_vectors = embed([q for q, _, _, _ in rows])
    words, _ = VEC["train_word_vectors"](NOTES, dim=16, epochs=60, seed=7)
    scratch_notes = [VEC["text_vector"](n, words) for n in NOTES]
    rankings = {"bm25": [], "scratch": [], "all-minilm": [], "fused": []}
    unknown = []
    for (question, _, _, _), q_vector in zip(rows, query_vectors, strict=True):
        scores = RETRIEVAL["bm25_scores"](question, NOTES)
        bm25 = sorted(range(len(NOTES)), key=lambda i: (-scores[i], i))
        dense = VEC["exact_search"](note_vectors, q_vector, len(NOTES))
        try:
            scratch = VEC["exact_search"](
                scratch_notes, VEC["text_vector"](question, words), len(NOTES)
            )
            unknown.append(False)
        except ValueError:  # no word of the question was ever seen in the notes
            scratch = list(range(len(NOTES)))
            unknown.append(True)
        rankings["bm25"].append(bm25)
        rankings["scratch"].append(scratch)
        rankings["all-minilm"].append(dense)
        rankings["fused"].append(VEC["reciprocal_rank_fusion"]([bm25, dense])[: len(NOTES)])
    table = []
    for ranker, ranked in rankings.items():
        for kind in ("direct", "paraphrase"):
            picked = [i for i, row in enumerate(rows) if row[2] == kind]
            table.append(
                {
                    "ranker": ranker,
                    "questions": kind,
                    "count": len(picked),
                    "recall_at_1": round(
                        statistics.mean(
                            VEC["recall_at_k"](ranked[i], rows[i][1], 1) for i in picked
                        ),
                        3,
                    ),
                    "recall_at_3": round(
                        statistics.mean(
                            VEC["recall_at_k"](ranked[i], rows[i][1], 3) for i in picked
                        ),
                        3,
                    ),
                    "mean_reciprocal_rank": round(
                        statistics.mean(
                            VEC["reciprocal_rank"](ranked[i], rows[i][1]) for i in picked
                        ),
                        3,
                    ),
                }
            )
    return {
        "questions": [
            {
                "question": q,
                "relevant": sorted(r),
                "kind": kind,
                "source": source,
                "shared_terms": overlap(q, NOTES[min(r)]),
                "scratch_knows_no_word": gap,
            }
            for (q, r, kind, source), gap in zip(rows, unknown, strict=True)
        ],
        "rankings": {k: [v[:10] for v in ranked] for k, ranked in rankings.items()},
        "table": table,
    }


def probes():
    codes = PROBES["codes"]
    notes = NOTES + codes["notes"]
    vectors = embed(notes)
    code_rows = []
    for offset, query in enumerate(codes["queries"]):
        target = len(NOTES) + offset
        q = embed([query])[0]
        scores = RETRIEVAL["bm25_scores"](query, notes)
        bm25 = sorted(range(len(notes)), key=lambda i: (-scores[i], i))
        dense = VEC["exact_search"](vectors, q, len(notes))
        rivals = [len(NOTES) + i for i in range(len(codes["notes"])) if i != offset]
        code_rows.append(
            {
                "query": query,
                "bm25_rank": bm25.index(target) + 1,
                "dense_rank": dense.index(target) + 1,
                "fused_rank": VEC["reciprocal_rank_fusion"]([bm25, dense]).index(target) + 1,
                "dense_score": round(VEC["dot"](vectors[target], q), 3),
                "best_rival_dense_score": round(max(VEC["dot"](vectors[r], q) for r in rivals), 3),
            }
        )
    between = [
        round(VEC["cosine"](vectors[len(NOTES) + i], vectors[len(NOTES) + j]), 3)
        for i in range(3)
        for j in range(i + 1, 3)
    ]
    negation = []
    for base, negated, paraphrase in PROBES["negation"]:
        v = embed([base, negated, paraphrase])
        negation.append(
            {
                "sentence": base,
                "negated": negated,
                "paraphrase": paraphrase,
                "cosine_negated": round(VEC["cosine"](v[0], v[1]), 3),
                "cosine_paraphrase": round(VEC["cosine"](v[0], v[2]), 3),
            }
        )
    stale = PROBES["stale"]
    old, new, query = embed([stale["old"], stale["new"], stale["query"]])
    return {
        "codes": {"notes": codes["notes"], "rows": code_rows, "cosine_between_notes": between},
        "negation": negation,
        "stale": {
            **stale,
            "cosine_old": round(VEC["cosine"](query, old), 3),
            "cosine_new": round(VEC["cosine"](query, new), 3),
        },
    }


def book_sentences():
    """Sentences from this book's chapters: prose only, 40 to 240 characters, deduplicated."""
    sentences = set()
    for path in sorted((ROOT / "book/textbook").glob("ch[0-9][0-9]/*-chapter.md")):
        text = re.sub(r"```.*?```", " ", path.read_text(), flags=re.S)
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith(
                ("#", "|", ">", "-", "*", "$", "!", "[")
            ):
                continue
            line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
            for sentence in re.split(r"(?<=[.!?])\s+", line):
                sentence = sentence.strip()
                if 40 <= len(sentence) <= 240 and "`" not in sentence and "$" not in sentence:
                    sentences.add(sentence)
    ordered = sorted(sentences)
    random.Random(6).shuffle(ordered)
    return ordered


def approximate(count, queries):
    sentences = book_sentences()[: count + queries]
    corpus, held_out = sentences[:count], sentences[count:]
    started = time.perf_counter()
    vectors = embed(corpus)
    seconds = time.perf_counter() - started
    query_vectors = embed(held_out)
    graph = VEC["small_world_graph"](vectors, links=8)
    exact = [VEC["exact_search"](vectors, q, 10) for q in query_vectors]
    rows = []
    for ef in (10, 20, 40, 80, 160):
        recalls, compared = [], []
        for q, truth in zip(query_vectors, exact, strict=True):
            found, n = VEC["graph_search"](vectors, graph, q, 10, ef)
            recalls.append(len(set(found) & set(truth)) / 10)
            compared.append(n)
        rows.append(
            {
                "ef": ef,
                "mean_recall_at_10": round(statistics.mean(recalls), 3),
                "mean_compared": round(statistics.mean(compared), 1),
                "share_of_exact_comparisons": round(statistics.mean(compared) / count, 3),
            }
        )
    digest = hashlib.sha256("\n".join(corpus + held_out).encode()).hexdigest()
    return {
        "corpus": count,
        "queries": queries,
        "dimensions": len(vectors[0]),
        "sentences_sha256": digest,
        "embedding_seconds": round(seconds, 2),
        "texts_per_second": round(count / seconds, 1),
        "links": 8,
        "rows": rows,
        "index_megabytes": round(VEC["index_bytes"](count, len(vectors[0])) / 1e6, 2),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--corpus", type=int, default=2000)
    parser.add_argument("--queries", type=int, default=100)
    args = parser.parse_args()
    started = time.time()
    embed(["warm up"])
    receipt = {
        "schema": 1,
        "experiment": "ch06-embeddings-v1",
        "recorded": time.strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "model": MODEL,
        "retrieval": retrieval(),
        "probes": probes(),
        "approximate": approximate(args.corpus, args.queries),
    }
    receipt["seconds"] = round(time.time() - started, 1)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    shown = {k: v for k, v in receipt.items() if k != "retrieval"}
    shown["retrieval"] = receipt["retrieval"]["table"]
    print(json.dumps(shown, indent=2))


if __name__ == "__main__":
    main()
