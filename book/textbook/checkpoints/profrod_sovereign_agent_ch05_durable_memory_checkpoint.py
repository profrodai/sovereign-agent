# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 5: persistence, correction, and forgetting that changes future context."""

import argparse
import copy
import json
import math
import runpy
import tempfile
from pathlib import Path

from reference_organizations.store.agent import OfflineShopModel, seed_lucy, shop_dispatcher
from sovereign_agent.agent_loop import run_loop
from sovereign_agent.assistant_context import context, forget, preferences, remember
from sovereign_agent.assistant_work import claim, enqueue, finish
from sovereign_agent.database import Database
from sovereign_agent.model_turn import HTTPModel


class ObservedModel:
    def __init__(self, model):
        self.model = model
        self.first_messages = None

    def complete(self, messages, tools, **kwargs):
        if self.first_messages is None:
            self.first_messages = copy.deepcopy(messages)
        return self.model.complete(messages, tools, **kwargs)


BOOK = Path(__file__).resolve().parents[1]
RETRIEVAL = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch05_retrieval_learner.py"))


def retrieval():
    """Part A's retrieval functions, each checked against an independent computation."""
    bm25 = RETRIEVAL["bm25_scores"]
    # "a" appears once, in one of three equal-length records: the score is idf alone.
    scores = bm25("a", ["a b", "b c", "c d"])
    assert math.isclose(scores[0], math.log(1 + 2.5 / 1.5)) and scores[1:] == [0.0, 0.0]
    repeated = bm25("a", ["a " * 200, "b", "c", "d"])[0]
    assert repeated < math.log(1 + 3.5 / 1.5) * 2.5
    print("ok   BM25 equals idf for a single occurrence, and saturates below idf (k1 + 1)")

    ranked, relevant = [4, 1, 7, 2], {1, 2}
    assert RETRIEVAL["precision_at_k"](ranked, relevant, 2) == 0.5
    assert RETRIEVAL["recall_at_k"](ranked, relevant, 3) == 0.5
    assert RETRIEVAL["reciprocal_rank"](ranked, relevant) == 0.5
    assert RETRIEVAL["reciprocal_rank"](ranked, {9}) == 0.0
    print("ok   precision@k, recall@k and reciprocal rank by their definitions")

    assert math.isclose(RETRIEVAL["cosine"]([1, 2, 3], [3, 6, 9]), 1.0)
    assert math.isclose(RETRIEVAL["cosine"]([1, 0], [0, 5]), 0.0)
    records = ["x" * 50, "y" * 30, "z" * 30, "w" * 10]
    chosen = RETRIEVAL["pack_context"](records, [4, 3, 2, 1], 70, len)
    assert chosen == [0, 3] and sum(len(records[i]) for i in chosen) <= 70
    print("ok   cosine ignores length; the packer keeps the budget and skips what does not fit")

    lab = runpy.run_path(
        str(BOOK / "experiments/profrod_sovereign_agent_textbook_ch05_retrieval_v1.py")
    )
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch05/ch05-retrieval-receipt-v1.json").read_text()
    )
    fresh = lab["evaluate_ranker"]("bm25", RETRIEVAL["bm25_scores"])
    assert fresh == receipt["rankers"][0]
    print("ok   the receipt's BM25 recall@3 and MRR recompute exactly:", fresh["recall_at_3"])


def main():
    retrieval()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--transcript", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="lucy-memory-") as temporary:
        path = Path(temporary) / "agent.sqlite"
        db = Database(path)
        seed_lucy(db)
        remember(db, "lucy", "supplier", "Ask for morning delivery", "lucy/message/1")
        db.close()
        db = Database(path)
        retained = preferences(db, "lucy", "delivery")[0]
        assert retained["source"] == "lucy/message/1"
        print("After reopening:", retained["value"])
        remember(db, "lucy", "supplier", "Ask for afternoon delivery", "lucy/message/2")
        print("After correction:", preferences(db, "lucy", "delivery")[0]["value"])
        remember(db, "lucy", "format", "three bullets", "lucy/message/3")
        enqueue(db, "old-turn", "lucy", "Prepare a brief")
        owner = claim(db, "first-worker")
        finish(db, owner, "DONE", "Lucy asks for afternoon delivery.")
        forget(db, "lucy", "supplier")
        selected = context(db, "lucy", "Prepare replenishment drafts.", allowed=frozenset())
        assert "afternoon delivery" not in selected[0]["content"]
        assert "three bullets" in selected[0]["content"]
        print("Forgotten value in future context:", "afternoon delivery" in selected[0]["content"])
        assert db.connection.execute("SELECT count(*) FROM assistant_work").fetchone()[0] == 1
        print("Operational record retained:", True)
        enqueue(db, "new-turn", "lucy", "Prepare replenishment drafts from current stock.")
        model = ObservedModel(
            HTTPModel(model=args.model, reasoning_effort="none")
            if args.live
            else OfflineShopModel()
        )
        previous = runpy.run_path(
            str(Path(__file__).with_name("profrod_sovereign_agent_ch03_agent_loop_checkpoint.py"))
        )
        dispatcher = shop_dispatcher(db)
        messages = context(
            db, "lucy", previous["MESSAGES"][1]["content"], allowed=dispatcher.allowed
        )
        messages[0]["content"] = previous["MESSAGES"][0]["content"] + "\n" + messages[0]["content"]
        current = claim(db, "new-worker")
        result = run_loop(model, dispatcher, messages)
        assert model.first_messages is not None
        assert "three bullets" in model.first_messages[0]["content"]
        assert "afternoon delivery" not in model.first_messages[0]["content"]
        passed = previous["draft_evidence"](result)
        finish(db, current, "DONE" if passed else "BLOCKED", result.answer)
        print("Context reached the model:", True)
        print("Draft evidence:", "PASS" if passed else "FAIL")
        if args.transcript:
            print(json.dumps(result.messages, indent=2))
        db.close()
        return 0 if result.status == "COMPLETED" and passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
