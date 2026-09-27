# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 15: evaluate named outcomes, expose blind spots and preserve a report."""

import argparse
import hashlib
import itertools
import json
import math
import random
import runpy
import tempfile
import tomllib
from pathlib import Path

from reference_organizations.store.agent import OfflineShopModel
from reference_organizations.store.evaluation import CASES, evaluate
from reference_organizations.store.improvement import save_report
from sovereign_agent.assistant_context import Skill
from sovereign_agent.model_turn import HTTPModel, ModelTurn, ToolCall

LEARNER = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "learner/profrod_sovereign_agent_ch15_evaluation_statistics_learner.py"
    )
)


def statistics():
    """Part A's estimators, each checked against an independent computation."""
    wilson, wald = LEARNER["wilson_interval"], LEARNER["wald_interval"]
    z = LEARNER["Z95"]
    for k, n in ((3, 10), (26, 28), (10, 28)):
        for p in wilson(k, n):
            assert math.isclose(abs(k / n - p), z * math.sqrt(p * (1 - p) / n), rel_tol=1e-9)
    assert wald(16, 16) == (1.0, 1.0) and round(wilson(16, 16)[0], 3) == 0.806
    print("ok   Wilson endpoints solve the quadratic; Wald collapses at 16/16")

    rng = random.Random(3)
    draws = 20_000
    inside = 0
    for _ in range(draws):
        low, high = wald(sum(rng.random() < 0.95 for _ in range(16)), 16)
        inside += low <= 0.95 <= high
    assert abs(inside / draws - LEARNER["coverage"](wald, 0.95, 16)) < 0.01
    print("ok   exact coverage agrees with simulation (Wald, p = 0.95, n = 16)")

    once = [[True], [False], [True], [True], [False]]
    twice = [group * 2 for group in once]
    se = LEARNER["clustered_standard_error"]
    assert math.isclose(se(once), se(twice))
    print("ok   duplicating every attempt leaves the clustered standard error unchanged")

    for b, c in ((1, 7), (0, 5), (4, 6)):
        m = b + c
        extreme = sum(
            min(sum(signs), m - sum(signs)) <= min(b, c)
            for signs in itertools.product((0, 1), repeat=m)
        )
        assert math.isclose(LEARNER["mcnemar_exact"](b, c), min(1.0, extreme / 2**m))
    print("ok   McNemar's p-value equals enumerating every sign assignment")

    samples, correct, k = 6, 2, 3
    subsets = list(itertools.combinations([True] * correct + [False] * (samples - correct), k))
    assert math.isclose(
        LEARNER["pass_at_k"](samples, correct, k), sum(any(s) for s in subsets) / len(subsets)
    )
    truth = 1 - (1 - 0.3) ** 5
    expected_naive = sum(
        LEARNER["binomial_pmf"](c, 10, 0.3) * LEARNER["naive_pass_at_k"](10, c, 5)
        for c in range(11)
    )
    expected_unbiased = sum(
        LEARNER["binomial_pmf"](c, 10, 0.3) * LEARNER["pass_at_k"](10, c, 5) for c in range(11)
    )
    assert math.isclose(expected_unbiased, truth) and expected_naive < truth - 0.01
    print("ok   pass@k is unbiased by enumeration; the plug-in is biased downward")

    n = LEARNER["cases_needed"](0.80, 0.85)
    rng = random.Random(11)
    rejected = 0
    for _ in range(1000):
        x = sum(rng.random() < 0.80 for _ in range(n))
        y = sum(rng.random() < 0.85 for _ in range(n))
        pooled = (x + y) / (2 * n)
        rejected += abs(y - x) / n > z * math.sqrt(2 * pooled * (1 - pooled) / n)
    assert 0.75 < rejected / 1000 < 0.85
    print(f"ok   {n} cases per candidate give power {rejected / 1000:.2f} by simulation")

    labels = ["pass"] * 8 + ["fail"] * 2
    assert LEARNER["cohen_kappa"](labels, ["pass"] * 10) == 0
    assert LEARNER["cohen_kappa"](labels, labels) == 1
    print("ok   kappa is 0 for a constant grader and 1 for perfect agreement")


class FluentWithoutEvidence:
    def complete(self, *args, **kwargs):
        return ModelTurn("Everything is fine. Buy nothing.")


class WrongCurrency(OfflineShopModel):
    def complete(self, *args, **kwargs):
        turn = super().complete(*args, **kwargs)
        return ModelTurn(turn.content.replace("cents USD", "euros"), turn.calls, turn.output_tokens)


class WrongAmount(OfflineShopModel):
    def complete(self, *args, **kwargs):
        turn = super().complete(*args, **kwargs)
        return ModelTurn(
            turn.content.replace("1500 cents USD", "999999 cents USD"),
            turn.calls,
            turn.output_tokens,
        )


class ForbiddenRequest:
    def complete(self, messages, *args, **kwargs):
        if not any(m["role"] == "tool" for m in messages):
            return ModelTurn(calls=(ToolCall(id="forbidden", name="approve", arguments={}),))
        return ModelTurn("No purchases made.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="qwen3")
    parser.add_argument("--output", type=Path, help="retain the complete report in this directory")
    args = parser.parse_args()
    statistics()
    models = (FluentWithoutEvidence, WrongCurrency, ForbiddenRequest)
    failures = [evaluate(model, cases=(CASES[0],)) for model in models]
    assert all(not report["passed"] for report in failures)
    assert all(report["acceptance"]["status"] == "REJECTED" for report in failures)
    assert failures[2]["cases"][0]["checks"]["no_purchases"]
    print("Fluent, wrong-currency and forbidden-request fixtures:", "REJECTED")
    blind = evaluate(WrongAmount, cases=(CASES[0],))
    assert blind["passed"] and "999999 cents USD" in blind["cases"][0]["answer"]
    assert blind["acceptance"]["status"] == "REVIEW_REQUIRED"
    print("Wrong prose amount with correct calls:", blind["acceptance"]["status"])
    source = (
        Path(__file__).parents[1]
        / "skills"
        / "profrod_sovereign_agent_textbook_opening_check_v1.toml"
    )
    skill = Skill.model_validate(tomllib.loads(source.read_text()))
    factory = (
        (lambda: HTTPModel(model=args.model, reasoning_effort="none"))
        if args.live
        else OfflineShopModel
    )
    report = evaluate(factory, skills=(skill,), repeats=2)
    passed = sum(row["passed"] for row in report["cases"])
    print("Named case checks:", passed, "/", len(report["cases"]))
    print("Acceptance:", report["acceptance"]["status"])
    assert report["baseline_totals"]["model_calls"] == 0
    assert all(row["checks"]["baseline_matches_authored_answer"] for row in report["cases"])
    print("Baseline authored-answer matches:", len(report["cases"]))
    with tempfile.TemporaryDirectory(prefix="lucy-evaluation-proof-") as temporary:
        path, digest = save_report(args.output or Path(temporary), report)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        assert json.loads(path.read_text())["acceptance"] == report["acceptance"]
        print("Saved report digest verified:", True)
        if args.output:
            print("Retained report:", path)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
