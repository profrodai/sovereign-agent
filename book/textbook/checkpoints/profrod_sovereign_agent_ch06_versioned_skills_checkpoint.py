# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 6: stage, evaluate, activate, and use one local opening procedure."""

import argparse
import json
import runpy
import statistics
import tempfile
from pathlib import Path

from reference_organizations.store.agent import OfflineShopModel, seed_lucy, shop_dispatcher
from reference_organizations.store.evaluation import CASES, candidate_checks, evaluate
from sovereign_agent.agent_loop import run_loop
from sovereign_agent.assistant_context import (
    activate_skill,
    context,
    remember,
    skill_snapshot,
    stage_skill,
)
from sovereign_agent.database import Database
from sovereign_agent.model_turn import HTTPModel

BOOK = Path(__file__).resolve().parents[1]
SENSITIVITY = runpy.run_path(
    str(BOOK / "learner/profrod_sovereign_agent_ch06_prompt_sensitivity_learner.py")
)


def prompt_sensitivity():
    """Part A's measures, checked by definition and against the receipt's retained answers."""
    label_of, spread = SENSITIVITY["label_of"], SENSITIVITY["spread"]
    assert label_of("Stock.") == "stock" and label_of("I would refuse this") == "refuse"
    assert label_of("pay") is None
    values = [0.25, 0.5, 0.75, 0.5]
    assert abs(spread(values)["sd"] - statistics.stdev(values)) < 1e-12
    assert SENSITIVITY["all_agree_share"]([[True, False, True], [True, True, True]]) == 2 / 3
    print("ok   labels, spread and agreement by their definitions")
    receipt = json.loads(
        (
            BOOK.parents[1] / "docs/evidence/book-ch06/ch06-prompt-sensitivity-receipt-v1.json"
        ).read_text()
    )
    for model in receipt["models"]:
        rows = {}
        for run in receipt["runs"]:
            if run["model"] == model["model"]:
                rows.setdefault(run["prompt"], []).append(
                    label_of(run["answer"]) == run["expected"]
                )
        recomputed = {name: round(sum(r) / len(r), 3) for name, r in rows.items()}
        assert recomputed == model["accuracy_by_prompt"], model["model"]
    print("ok   every prompt's accuracy recomputes from the retained answers")


def main():
    prompt_sensitivity()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--transcript", action="store_true")
    args = parser.parse_args()
    model_factory = (
        (lambda: HTTPModel(model=args.model, reasoning_effort="none"))
        if args.live
        else OfflineShopModel
    )
    with tempfile.TemporaryDirectory(prefix="lucy-skills-") as temporary:
        path = Path(temporary) / "agent.sqlite"
        db = Database(path)
        seed_lucy(db)
        remember(db, "lucy", "format", "three bullets", "lucy/message/3")
        source = (
            Path(__file__).parents[1]
            / "skills"
            / "profrod_sovereign_agent_textbook_opening_check_v1.toml"
        )
        candidate = stage_skill(db, source)
        print("Active before evaluation:", len(skill_snapshot(db)[1]))
        reports = []

        def check(skill):
            report = evaluate(model_factory, skill=skill, cases=CASES[:3])
            reports.append(report)
            return candidate_checks(report)

        try:
            activate_skill(
                db,
                candidate.name,
                candidate.version,
                evaluate=check,
                required_cases=frozenset(f"{case.name}:0" for case in CASES[:3]),
            )
        except ValueError:
            if args.transcript:
                print(json.dumps({"evaluations": reports}, indent=2))
            print("Candidate activation: REFUSED")
            db.close()
            return 1
        print("Candidate cases:", len(reports[0]["cases"]), reports[0]["passed"])
        db.close()
        db = Database(path)
        print("Active after reopening:", skill_snapshot(db)[1][0].version)
        dispatcher = shop_dispatcher(db)
        previous = runpy.run_path(
            str(Path(__file__).with_name("profrod_sovereign_agent_ch03_agent_loop_checkpoint.py"))
        )
        prompt = previous["MESSAGES"][1]["content"]
        denied = context(db, "lucy", prompt, allowed=frozenset({"list_stock"}))
        assert "skill_guidance" not in denied[0]["content"]
        print("Missing required tool excludes skill:", True)
        messages = context(db, "lucy", prompt, allowed=dispatcher.allowed)
        assert "skill_guidance" in messages[0]["content"]
        assert "three bullets" in messages[0]["content"]
        result = run_loop(model_factory(), dispatcher, messages)
        passed = result.status == "COMPLETED" and previous["draft_evidence"](result)
        print("Draft evidence:", "PASS" if passed else "FAIL")
        orders = db.connection.execute("SELECT count(*) FROM assistant_orders").fetchone()[0]
        print("Purchases:", orders)
        if args.transcript:
            print(json.dumps({"evaluations": reports, "transcript": result.messages}, indent=2))
        db.close()
        return 0 if passed and orders == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
