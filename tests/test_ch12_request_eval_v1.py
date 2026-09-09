"""Adversarial checks for the Chapter 12 diagnostic and its evidence boundaries."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from sovereign_agent.model_turn import ModelTurn

EXPERIMENT = (
    Path(__file__).resolve().parents[1] / "book/always_on/experiments/ch12_request_eval_v1.py"
)
SPEC = importlib.util.spec_from_file_location("ch12_request_eval_v1", EXPERIMENT)
assert SPEC and SPEC.loader
lab = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lab
SPEC.loader.exec_module(lab)


@pytest.mark.parametrize(
    "raw",
    [
        '{"action":"purchase","sku":"V"}',
        '{"action":"draft","sku":"UNKNOWN"}',
        '{"action":"draft","sku":null}',
        '{"action":"stock","sku":1}',
        '{"action":"refuse","sku":"V"}',
        '{"action":"draft","sku":"V","approved":true}',
        '```json\n{"action":"stock","sku":"V"}\n```',
    ],
)
def test_invalid_or_unusable_decisions_are_failed_attempts(raw):
    row = lab.run_case(lab.CASES[0], "broken", lambda _: (raw, 12))
    assert row["error"] is not None
    assert not row["passed"]
    assert row["events"] == ()


def test_actual_decision_controls_response_and_wrong_draft_is_detected():
    stock, draft = lab.CASES[:2]
    assert stock.catalog == draft.catalog

    def infer(_):
        return '{"action":"draft","sku":"V"}', 10

    bad = lab.run_case(stock, "always_draft", infer)
    good = lab.run_case(draft, "always_draft", infer)
    assert bad["events"] == (("draft", "V", 6, 1500),)
    assert not bad["checks"]["no_unrequested_draft"]
    assert not bad["passed"]
    assert good["passed"]


def test_always_clarify_cannot_pass_positive_task():
    row = lab.run_case(lab.CASES[1], "always_clarify", lambda _: ('{"action":"clarify"}', 3))
    assert not row["passed"]
    assert row["events"] == ()


def test_timeout_remains_in_denominator_and_usage_is_unknown():
    def timeout(_):
        raise TimeoutError("not retained in report")

    bad = lab.run_case(lab.CASES[0], "candidate", timeout)
    good = lab.run_case(lab.CASES[0], "candidate", lambda _: ('{"action":"stock","sku":"V"}', 7))
    summary = lab.summarize([bad, good])["candidate"]
    assert summary["attempts"] == 2
    assert summary["passed"] == 1
    assert summary["errors"] == 1
    assert summary["unknown_usage_attempts"] == 1
    assert summary["observed_output_tokens"] == 7
    assert bad["raw"] is None and bad["output_tokens"] is None
    assert bad["error"] == "TimeoutError"


def test_model_receives_only_request_and_catalog_and_observed_usage_returns():
    received = []

    class RecordingModel:
        def complete(self, messages, tools, **kwargs):
            received.append((messages, tools, kwargs))
            return ModelTurn(content='{"action":"stock","sku":"V"}', output_tokens=17)

    case = lab.CASES[0]
    row = lab.run_case(case, "recording", lab.model_infer(RecordingModel(), "frozen prompt", 2))
    messages, tools, bounds = received[0]
    assert messages[0] == {"role": "system", "content": "frozen prompt"}
    assert json.loads(messages[1]["content"]) == {
        "request": "Report vanilla stock.",
        "catalog": [
            {
                "sku": "V",
                "name": "vanilla",
                "on_hand": 2,
                "reserved": 0,
                "target": 8,
                "unit_pence": 250,
            }
        ],
    }
    assert tools == []
    assert bounds == {"timeout": 2, "max_output_tokens": 300}
    assert row["passed"] and row["output_tokens"] == 17


def test_candidate_mutating_its_input_does_not_change_case():
    def mutate(payload):
        payload["catalog"][0]["on_hand"] = 900
        return '{"action":"stock","sku":"V"}', 1

    row = lab.run_case(lab.CASES[0], "mutating", mutate)
    assert row["events"] == (("stock", "V", 2, None),)
    assert lab.CASES[0].catalog[0].on_hand == 2


def test_public_transfer_exposes_keyword_quotation_failure():
    case = next(c for c in lab.CASES if c.name == "quoted")
    row = lab.run_case(case, "keywords", lambda p: (lab.keyword_decision(p), 0))
    assert row["decision"] == {"action": "refuse", "sku": None}
    assert not row["passed"]


def test_response_arithmetic_has_independent_reserved_and_no_shortage_cases():
    mango = lab.parse_decision('{"action":"draft","sku":"M"}', lab.M)
    assert lab.fulfill(mango, lab.M) == (("draft", "M", 5, 625),)
    sufficient = (lab.Product("M", "mango", 20, 1, 9, 125),)
    assert lab.fulfill(mango, sufficient) == (("draft", "M", 0, 0),)


def test_report_refuses_overwrite(tmp_path):
    path = tmp_path / "report.json"
    lab.write_report(path, {"first": True})
    with pytest.raises(FileExistsError):
        lab.write_report(path, {"second": True})
    assert json.loads(path.read_text()) == {"first": True}
