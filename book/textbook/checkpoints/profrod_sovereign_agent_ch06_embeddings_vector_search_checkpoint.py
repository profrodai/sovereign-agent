# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 6: embeddings, a vector index with provenance, and the measured retrieval."""

import json
import math
import runpy
import sqlite3
import tempfile
from array import array
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
VEC = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch06_embeddings_learner.py"))
LEXICAL = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch05_retrieval_learner.py"))
NOTES = runpy.run_path(
    str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py")
)["NOTES"]
MODEL = "scratch-16"


def vector_arithmetic():
    """The learner functions against values computed by hand."""
    vocab = ["chocolate", "vanilla", "vegan"]
    assert VEC["dot"](VEC["one_hot"]("vanilla", vocab), VEC["one_hot"]("vegan", vocab)) == 0
    assert VEC["matvec"]([[1, 2, 3], [4, 5, 6]], VEC["one_hot"]("vegan", vocab)) == [3, 6]
    a, b = VEC["normalize"]([1, 2, 2]), VEC["normalize"]([2, 1, 2])
    assert math.isclose(VEC["squared_distance"](a, b), 2 - 2 * VEC["cosine"](a, b))
    assert VEC["reciprocal_rank_fusion"]([[1, 2, 3], [3, 2, 1]]) == [1, 3, 2]
    assert VEC["recall_at_k"]([4, 7, 1], {1, 9}, 3) == 0.5
    assert VEC["reciprocal_rank"]([4, 7, 1], {1}) == 1 / 3
    assert VEC["index_bytes"](1_000_000, 384) == 1_536_000_000
    points = [VEC["normalize"]([math.cos(i / 5), math.sin(i / 5), 0.1 * i]) for i in range(60)]
    graph = VEC["small_world_graph"](points, links=4)
    query = VEC["normalize"]([0.3, 0.9, 1.0])
    found, compared = VEC["graph_search"](points, graph, query, 5, ef=len(points))
    assert found == VEC["exact_search"](points, query, 5) and compared <= len(points)
    print("ok   one-hot, lookup, distance identity, fusion, metrics and graph search")


def open_store(path):
    db = sqlite3.connect(path)
    db.execute(
        "CREATE TABLE IF NOT EXISTS note_vectors("
        " note_id INTEGER NOT NULL, revision INTEGER NOT NULL, current INTEGER NOT NULL,"
        " model TEXT NOT NULL, dimensions INTEGER NOT NULL, vector BLOB NOT NULL,"
        " text TEXT NOT NULL, PRIMARY KEY (note_id, revision))"
    )
    return db


def add(db, note_id, revision, text, model, vector):
    with db:
        db.execute("UPDATE note_vectors SET current = 0 WHERE note_id = ?", (note_id,))
        db.execute(
            "INSERT INTO note_vectors VALUES (?, ?, 1, ?, ?, ?, ?)",
            (note_id, revision, model, len(vector), array("f", vector).tobytes(), text),
        )


def search(db, query_vector, model, k=3):
    rows = db.execute(
        "SELECT note_id, model, dimensions, vector, text FROM note_vectors WHERE current = 1"
    ).fetchall()
    if any(row[1] != model or row[2] != len(query_vector) for row in rows):
        raise ValueError("stored vectors come from another model; re-embed them first")
    scored = [
        (VEC["dot"](array("f", row[3]).tolist(), query_vector), row[0], row[4]) for row in rows
    ]
    return sorted(scored, key=lambda s: (-s[0], s[1]))[:k]


def vector_index():
    """Part B's store, through a real database file closed and reopened."""
    words, _ = VEC["train_word_vectors"](NOTES, dim=16, epochs=60, seed=7)

    def embed(text):
        return VEC["text_vector"](text, words)

    with tempfile.TemporaryDirectory(prefix="lucy-vectors-") as directory:
        path = Path(directory) / "vectors.sqlite"
        db = open_store(path)
        for i, note in enumerate(NOTES):
            add(db, i, 1, note, MODEL, embed(note))
        changed = "From October, Meadow Farm delivers only on Wednesdays."
        add(db, 15, 2, changed, MODEL, embed(changed))
        db.close()
        db = open_store(path)
        current = db.execute("SELECT revision FROM note_vectors WHERE note_id = 15 AND current = 1")
        assert current.fetchall() == [(2,)]
        assert db.execute("SELECT COUNT(*) FROM note_vectors").fetchone()[0] == len(NOTES) + 1
        texts = [row[2] for row in search(db, embed("Meadow Farm deliveries"), MODEL, len(NOTES))]
        assert changed in texts and NOTES[15] not in texts
        try:
            search(db, [1.0] + [0.0] * 383, "all-minilm")
        except ValueError:
            pass
        else:
            raise AssertionError("a query from another model was ranked")
        db.close()
    print("ok   index: provenance stored, only the current revision searched, other models refused")


def measured_retrieval():
    """The receipt's recall and reciprocal rank, recomputed from its retained rankings."""
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch06/ch06-embeddings-receipt-v1.json").read_text()
    )
    questions = receipt["retrieval"]["questions"]
    for row in receipt["retrieval"]["table"]:
        rankings = receipt["retrieval"]["rankings"][row["ranker"]]
        picked = [i for i, q in enumerate(questions) if q["kind"] == row["questions"]]
        for k, field in ((1, "recall_at_1"), (3, "recall_at_3")):
            values = [
                VEC["recall_at_k"](rankings[i], set(questions[i]["relevant"]), k) for i in picked
            ]
            assert round(sum(values) / len(values), 3) == row[field], (row, field)
    for q in questions:
        assert q["shared_terms"] == sorted(
            set(LEXICAL["terms"](q["question"])) & set(LEXICAL["terms"](NOTES[q["relevant"][0]]))
        )
    print("ok   recall recomputed from the retained rankings; shared terms recomputed")


def main():
    vector_arithmetic()
    vector_index()
    measured_retrieval()


if __name__ == "__main__":
    main()
