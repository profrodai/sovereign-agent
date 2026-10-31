"""Invented input tests are engineering controls, never assessed real papers."""

import hashlib
import json
import os
from copy import deepcopy

import pytest

from sovereign_agent import paper_assessment as paper


def supplied(root, *, prior=False, text_override=None):
    root.mkdir(parents=True, exist_ok=True)
    documents = []
    for identifier, role in [("main", "paper"), *([("prior", "prior_work")] if prior else [])]:
        text = (text_override or f"Invented {role} evidence. A bounded decision rule is specified.\n").encode()
        (root / (identifier + ".txt")).write_bytes(text)
        documents.append(
            {
                "id": identifier,
                "role": role,
                "title": "Invented input, not a real paper",
                "source_url": "https://example.invalid/" + identifier,
                "source_version": "fixture-v1",
                "source_id": "invented-" + identifier,
                "source_api": "supplied-public-paper",
                "source_observation": "explicit synthetic fixture, no acquisition",
                "original_path": identifier + ".txt",
                "original_sha256": paper.sha256(text),
                "text_path": identifier + ".txt",
                "text_sha256": paper.sha256(text),
                "extractor_ref": "identity-text-fixture/v1, not a PDF extractor",
                "extractor_sha256": paper.sha256(b"invented identity-extractor fixture/v1"),
                "extraction_config_sha256": paper.sha256(b"identity UTF-8 fixture"),
                "locator_map_sha256": "0" * 64,
                "use": "private_assessment",
                "anchors": [
                    {
                        "id": "a",
                        "locator": "invented paragraph 1",
                        "start": 0,
                        "end": len(text),
                        "quote_sha256": paper.sha256(text),
                    }
                ],
            }
        )
    for document in documents:
        document["locator_map_sha256"] = paper.sha256(json.dumps(
            document["anchors"], sort_keys=True, separators=(",", ":")
        ).encode())
    manifest = {
        "schema": "sovereign.paper-source/v1",
        "observed_utc": "2026-10-31T00:00:00+00:00",
        "documents": documents,
    }
    return write_manifest(root, manifest), manifest


def write_manifest(root, manifest):
    body = json.dumps(manifest).encode()
    (root / "manifest.json").write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def card(input_digest, observation):
    dimensions = {
        name: {
            "level": None, "explanation": "Not established from this invented excerpt",
            "limitations": "A synthetic fragment cannot qualify science",
            "evidence": [], "missing": "Required source material not examined",
        }
        for name in paper.DIMENSIONS
    }
    dimensions["clarity"] = {
        "level": 3, "explanation": "The inspected decision rule can be followed",
        "limitations": "No complete paper was examined", "evidence": [observation], "missing": "",
    }
    return {
        "input_sha256": input_digest,
        "rubric": paper.RUBRIC,
        "contribution": "An invented decision rule, not a claimed scientific advance",
        "contribution_evidence": [observation],
        "audience": "Engineering fixture readers",
        "dimensions": dimensions,
        "closest_prior_work": [],
        "strongest_support": "insufficient evidence",
        "support_evidence": [],
        "unresolved": ["Actual scientific usefulness is untested"],
        "reproduction": "not attempted",
    }


def loaded(root):
    digest, _ = supplied(root)
    source = paper.load(root, "manifest.json", digest, "operator approves synthetic fixture only")
    observation = paper.observe(source, "main/a", "fixture-observation")
    return digest, source, observation


def test_valid_private_shape_links_exact_inspected_bytes(tmp_path):
    digest, source, observation = loaded(tmp_path)
    proposal = paper.Card.model_validate(card(digest, observation["operation"]))
    result = paper.validate_card(proposal, source, [observation])
    assert len(result) == 64
    assert observation["quote"].encode() == (tmp_path / "main.txt").read_bytes()
    assert proposal.dimensions["originality"].level is None
    assert proposal.reproduction == "not attempted"


@pytest.mark.parametrize("change", ["quote", "range", "original", "text", "use", "authors"])
def test_forged_or_unapproved_inputs_refuse_before_admission(tmp_path, change):
    _, manifest = supplied(tmp_path)
    document = manifest["documents"][0]
    if change == "quote":
        document["anchors"][0]["quote_sha256"] = "0" * 64
    elif change == "range":
        document["anchors"][0]["end"] = 99999
    elif change == "original":
        document["original_sha256"] = "0" * 64
    elif change == "text":
        document["text_sha256"] = "0" * 64
    elif change == "use":
        document["use"] = "citation_link_only"
    else:
        document["authors"] = ["forbidden identifying scoring field"]
    digest = write_manifest(tmp_path, manifest)
    with pytest.raises((ValueError, PermissionError)):
        paper.load(tmp_path, "manifest.json", digest, "operator fixture reference")


def test_operator_approval_is_outside_manifest_and_binds_exact_digest(tmp_path):
    digest, _ = supplied(tmp_path)
    with pytest.raises(PermissionError):
        paper.load(tmp_path, "manifest.json", digest, "")
    with pytest.raises(ValueError, match="digest mismatch"):
        paper.load(tmp_path, "manifest.json", "0" * 64, "nonempty is not the expected digest")
    # This is explicit operator attestation, not automatic rights verification.
    assert paper.load(tmp_path, "manifest.json", digest, "approved fixture")["approval"]


@pytest.mark.parametrize("kind", ["fifo", "final_alias", "parent_alias", "hardlink", "oversize"])
def test_bounded_owned_input_refuses_alias_or_blocking_file(tmp_path, kind):
    target = tmp_path / "input"
    relative = "input"
    if kind == "fifo":
        os.mkfifo(target)
    elif kind == "final_alias":
        (tmp_path / "source").write_text("x")
        target.symlink_to(tmp_path / "source")
    elif kind == "parent_alias":
        (tmp_path / "real").mkdir()
        (tmp_path / "real" / "input").write_text("x")
        (tmp_path / "alias").symlink_to(tmp_path / "real", target_is_directory=True)
        relative = "alias/input"
    elif kind == "hardlink":
        (tmp_path / "source").write_text("x")
        os.link(tmp_path / "source", target)
    else:
        target.write_bytes(b"x" * 10)
    with pytest.raises((ValueError, OSError)):
        paper.read_owned(tmp_path, relative, 5)


def test_duplicate_json_and_forbidden_review_metadata_are_not_silently_flattened(tmp_path):
    _, manifest = supplied(tmp_path)
    manifest["venue_decision"] = "not a permitted scoring input"
    digest = write_manifest(tmp_path, manifest)
    with pytest.raises(ValueError):
        paper.load(tmp_path, "manifest.json", digest, "fixture approval")
    body = b'{"schema":"first","schema":"second"}'
    (tmp_path / "manifest.json").write_bytes(body)
    with pytest.raises(ValueError, match="duplicate"):
        paper.load(tmp_path, "manifest.json", paper.sha256(body), "fixture approval")


@pytest.mark.parametrize("change", ["unbacked", "unknown", "version", "novelty", "composite", "reproduced"])
def test_card_rejects_unbacked_scores_and_authority_claims(tmp_path, change):
    digest, source, observation = loaded(tmp_path)
    value = card(digest, observation["operation"])
    if change == "unbacked":
        value["dimensions"]["clarity"]["evidence"] = []
    elif change == "unknown":
        value["contribution_evidence"] = ["uninspected"]
    elif change == "version":
        value["input_sha256"] = "0" * 64
    elif change == "novelty":
        value["dimensions"]["originality"] = deepcopy(value["dimensions"]["clarity"])
    elif change == "composite":
        value["overall_score"] = 4
    else:
        value["reproduction"] = "reproduced within stated tolerance"
    with pytest.raises(ValueError):
        paper.validate_card(paper.Card.model_validate(value), source, [observation])


def test_prior_work_requires_actual_examined_prior_document(tmp_path):
    digest, _ = supplied(tmp_path, prior=True)
    source = paper.load(tmp_path, "manifest.json", digest, "fixture approval")
    primary = paper.observe(source, "main/a", "primary")
    prior = paper.observe(source, "prior/a", "prior")
    value = card(digest, "primary")
    value["closest_prior_work"] = [{"evidence": ["prior"], "difference": "Fixture comparison only"}]
    value["dimensions"]["originality"] = deepcopy(value["dimensions"]["clarity"])
    value["dimensions"]["originality"]["evidence"] = ["primary", "prior"]
    assert paper.validate_card(paper.Card.model_validate(value), source, [primary, prior])
    value["closest_prior_work"][0]["evidence"] = ["primary"]
    with pytest.raises(ValueError, match="prior-work source"):
        paper.validate_card(paper.Card.model_validate(value), source, [primary, prior])


def test_structural_locator_does_not_prove_scientific_entailment(tmp_path):
    digest, source, observation = loaded(tmp_path)
    value = card(digest, observation["operation"])
    value["contribution"] = "An unsupported scientific interpretation using a valid pointer"
    # Structural validation cannot judge this meaning. Independent scientific review must.
    assert paper.validate_card(paper.Card.model_validate(value), source, [observation])


def test_private_input_cannot_be_admitted_under_a_git_worktree(tmp_path):
    repository = tmp_path / "public-source"
    repository.mkdir()
    (repository / ".git").mkdir()
    private = repository / "misplaced-paper-root"
    digest, _ = supplied(private)
    with pytest.raises(PermissionError, match="outside Git"):
        paper.load(private, "manifest.json", digest, "fixture input attestation")
