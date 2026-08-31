#!/usr/bin/env python3
"""Verify the Unit 12 redacted proof-pack manifest.

    python scripts/verify_proof_pack.py [path-to-proof-pack.json]

Defaults to `docs/evidence/unit12/proof-pack.json`. Rejects, each with a
specific named reason:

- missing required fields (governing ruling Holding 2);
- an unknown provider status value (only LIVE_PASS, NOT_RUN_UNAVAILABLE,
  NOT_RUN_UNAUTHENTICATED, FAIL are allowed);
- an unknown Andrea evaluation status value (only NOT_RUN, PASS, FAIL are
  allowed);
- a SHA-256 digest that does not match the file it claims to describe;
- any evidence path that escapes `docs/evidence/unit12/` (`..`, absolute
  paths, symlink traversal);
- secret-shaped content -- FIELD-SCHEMA-AWARE, not a blind content scan.
  Fields with a known fixed shape (commit SHAs, SHA-256 digests, semantic
  versions, paths) are validated against that shape and never rejected for
  being long. Free-text fields are scanned for exactly two narrow patterns:
  a credential env-var NAME=value assignment, or a literal "Bearer <token>"
  shape. No entropy heuristic anywhere;
- a NOT_RUN or NOT_RUN_* status whose accompanying prose claims success (the
  "NOT_RUN means PASS" lie Holding 2 names explicitly). Lie-scan context is
  derived structurally during the manifest walk from each object's OWN
  recognized status field -- provider_status.<provider> and
  andrea_live_evaluation alike, and any future status-bearing object for
  free -- never from a caller-injected, field-specific flag.

Exits 0 when the manifest is well-formed and internally truthful. This
verifier does NOT claim the manifest is COMPLETE -- a genuinely partial
manifest (real gate evidence, honest NOT_RUN for what this unit's own
implementation cannot itself produce) is expected to pass.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from proof_pack_schema import (  # noqa: E402
    ANDREA_STATUSES,
    BEARER_TOKEN_RE,
    CREDENTIAL_ASSIGNMENT_RE,
    EVIDENCE_DIR_NAME,
    KNOWN_SHAPE_FIELDS,
    KNOWN_STATUS_VALUES,
    PATH_FIELD_NAMES,
    PROVIDER_STATUSES,
    REQUIRED_PROVIDERS,
    REQUIRED_TOP_LEVEL_FIELDS,
)

EVIDENCE_ROOT = (REPO_ROOT / EVIDENCE_DIR_NAME).resolve()

# Prose/claim shapes that assert success. Deliberately narrow -- this is a
# small, explicit lie-detector for the one lie Holding 2 names ("NOT_RUN
# means PASS"), not a general sentiment classifier.
SUCCESS_CLAIM_SNIPPETS = (
    "live_pass",
    "passed live",
    "live evaluation passed",
    "successfully completed a live",
    "verified live",
)


def fail(failures: list[str], message: str) -> None:
    failures.append(message)


def _is_path_field(dotted_path: str) -> bool:
    last = dotted_path.rsplit(".", 1)[-1]
    return last in PATH_FIELD_NAMES


def _known_shape_pattern(dotted_path: str) -> Any:
    last = dotted_path.rsplit(".", 1)[-1]
    return KNOWN_SHAPE_FIELDS.get(last)


def check_path_escape(dotted_path: str, value: str, failures: list[str]) -> bool:
    """Returns True if `value` is a safe evidence-relative path.

    Mirrors `sovereign_agent.workspace.safe_join`'s own discipline: refuse an
    absolute path outright, then resolve both the evidence root and the
    candidate and require the candidate to sit at or under the resolved
    root -- resolving handles `..` segments and symlink traversal alike,
    which a string-prefix check cannot see through.
    """
    if not value or not value.strip():
        fail(failures, f"{dotted_path}: empty evidence path")
        return False
    if Path(value).is_absolute():
        fail(failures, f"{dotted_path}: evidence path {value!r} is absolute (escapes evidence dir)")
        return False
    candidate = (EVIDENCE_ROOT / value).resolve()
    try:
        candidate.relative_to(EVIDENCE_ROOT)
    except ValueError:
        fail(
            failures,
            f"{dotted_path}: evidence path {value!r} escapes {EVIDENCE_DIR_NAME}/",
        )
        return False
    return True


def scan_free_text(dotted_path: str, value: str, failures: list[str]) -> None:
    """The two narrow secret-shaped patterns. No entropy heuristic."""
    match = CREDENTIAL_ASSIGNMENT_RE.search(value)
    if match is not None:
        fail(
            failures,
            f"{dotted_path}: contains an unredacted credential assignment "
            f"({match.group(0).split('=', 1)[0]}=...)",
        )
    bearer = BEARER_TOKEN_RE.search(value)
    if bearer is not None:
        fail(failures, f"{dotted_path}: contains a literal Bearer-token shape")


def check_not_run_means_pass_lie(dotted_path: str, value: str, failures: list[str]) -> None:
    lowered = value.lower()
    for snippet in SUCCESS_CLAIM_SNIPPETS:
        if snippet in lowered:
            fail(
                failures,
                f"{dotted_path}: prose claims success ({snippet!r}) alongside a "
                "NOT_RUN status -- NOT_RUN does not mean PASS",
            )
            return


def _is_not_run_status(value: Any) -> bool:
    """True for a RECOGNIZED status value that is NOT_RUN or NOT_RUN_*.

    Consults the closed union of both status domains (provider and Andrea)
    so this one check works for either kind of object. An unrecognized
    status value is not this function's concern -- rejecting it with a
    named reason is check_provider_status / check_andrea_status's job; this
    function only ever widens lie-scan context, never narrows a rejection.
    """
    return (
        isinstance(value, str)
        and value in KNOWN_STATUS_VALUES
        and (value == "NOT_RUN" or value.startswith("NOT_RUN_"))
    )


def walk_and_validate_strings(
    node: Any, dotted_path: str, failures: list[str], *, not_run_context: bool = False
) -> None:
    """Depth-first walk validating every string leaf against its OWN field
    shape -- never a blind scan applied uniformly to all content.

    - A field with a known fixed shape (commit SHA, SHA-256 digest, semver)
      is checked against that shape only.
    - A field whose name marks it as a path is checked against the
      path-escape rule only.
    - Everything else is free text: scanned for the two narrow secret
      patterns, and if `not_run_context` is set, also scanned for a false
      success claim.

    `not_run_context` is DERIVED here, not injected by the caller: any dict
    node carrying its own recognized `status` key whose value is NOT_RUN or
    NOT_RUN_* becomes a lie-scan context root for its own subtree -- prose
    and nested sibling fields alike -- regardless of which top-level field
    the object lives under (provider_status.<provider> or
    andrea_live_evaluation today; any future status-bearing object for
    free). A dict without its own status key inherits the context its
    parent was walked with, so nested siblings of a NOT_RUN root stay
    covered without needing a status key of their own.
    """
    if isinstance(node, dict):
        context = not_run_context or _is_not_run_status(node.get("status"))
        for key, child in node.items():
            child_path = f"{dotted_path}.{key}" if dotted_path else key
            walk_and_validate_strings(child, child_path, failures, not_run_context=context)
        return
    if isinstance(node, list):
        for index, item in enumerate(node):
            walk_and_validate_strings(
                item, f"{dotted_path}[{index}]", failures, not_run_context=not_run_context
            )
        return
    if not isinstance(node, str):
        return

    shape = _known_shape_pattern(dotted_path)
    if shape is not None:
        if not shape.match(node):
            fail(failures, f"{dotted_path}: does not match its required shape ({node!r})")
        return  # known-shape fields are never scanned for secret patterns

    if _is_path_field(dotted_path):
        check_path_escape(dotted_path, node, failures)
        return  # path fields are validated as paths, never as free text

    # Free text: the two narrow secret patterns, always.
    scan_free_text(dotted_path, node, failures)
    if not_run_context:
        check_not_run_means_pass_lie(dotted_path, node, failures)


def check_required_fields(manifest: dict[str, Any], failures: list[str]) -> None:
    for name in REQUIRED_TOP_LEVEL_FIELDS:
        if name not in manifest:
            fail(failures, f"missing required field: {name}")


def check_provider_status(manifest: dict[str, Any], failures: list[str]) -> None:
    provider_status = manifest.get("provider_status")
    if not isinstance(provider_status, dict):
        fail(failures, "provider_status: must be an object keyed by provider name")
        return
    for provider in REQUIRED_PROVIDERS:
        row = provider_status.get(provider)
        if row is None:
            fail(failures, f"provider_status.{provider}: missing")
            continue
        if not isinstance(row, dict):
            fail(failures, f"provider_status.{provider}: must be an object")
            continue
        status = row.get("status")
        if status not in PROVIDER_STATUSES:
            fail(
                failures,
                f"provider_status.{provider}.status: unknown value {status!r} "
                f"(must be one of {sorted(PROVIDER_STATUSES)})",
            )
            continue
        if status == "LIVE_PASS":
            evidence_path = row.get("evidence_path")
            if not evidence_path:
                fail(
                    failures,
                    f"provider_status.{provider}: status is LIVE_PASS but no "
                    "evidence_path is recorded",
                )
            elif not isinstance(evidence_path, str):
                fail(failures, f"provider_status.{provider}.evidence_path: must be a string")
            elif check_path_escape(
                f"provider_status.{provider}.evidence_path", evidence_path, failures
            ):
                target = (EVIDENCE_ROOT / evidence_path).resolve()
                if not target.is_file():
                    fail(
                        failures,
                        f"provider_status.{provider}: status is LIVE_PASS but evidence_path "
                        f"{evidence_path!r} does not exist -- an unbacked LIVE_PASS claim",
                    )
        # NOT_RUN_* success-claim, shape and secret-pattern checks all happen
        # via the single whole-manifest walk in check_top_level_shapes, which
        # derives lie-scan context from this row's own status field itself --
        # no second walk of this row is needed here.


def check_andrea_status(manifest: dict[str, Any], failures: list[str]) -> None:
    """Reject an Andrea evaluation status outside the closed domain.

    Mirrors check_provider_status's own-field validation, but for the single
    andrea_live_evaluation object rather than a dict keyed by provider name.
    The NOT_RUN-means-PASS lie check for this field's prose happens via the
    same whole-manifest walk check_provider_status now also relies on.
    """
    andrea = manifest.get("andrea_live_evaluation")
    if not isinstance(andrea, dict):
        fail(failures, "andrea_live_evaluation: must be an object")
        return
    status = andrea.get("status")
    if status not in ANDREA_STATUSES:
        fail(
            failures,
            f"andrea_live_evaluation.status: unknown value {status!r} "
            f"(must be one of {sorted(ANDREA_STATUSES)})",
        )


def check_digests(manifest: dict[str, Any], failures: list[str]) -> None:
    """Every evidence_files entry's recorded sha256 must match the file on disk."""
    evidence_files = manifest.get("evidence_files")
    if evidence_files is None:
        return
    if not isinstance(evidence_files, list):
        fail(failures, "evidence_files: must be a list")
        return
    for index, entry in enumerate(evidence_files):
        label = f"evidence_files[{index}]"
        if not isinstance(entry, dict):
            fail(failures, f"{label}: must be an object")
            continue
        path_value = entry.get("path")
        digest_value = entry.get("sha256")
        if not isinstance(path_value, str):
            fail(failures, f"{label}.path: missing or not a string")
            continue
        if not isinstance(digest_value, str):
            fail(failures, f"{label}.sha256: missing or not a string")
            continue
        if not check_path_escape(f"{label}.path", path_value, failures):
            continue
        target = (EVIDENCE_ROOT / path_value).resolve()
        if not target.is_file():
            fail(failures, f"{label}: evidence file {path_value!r} does not exist on disk")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest_value.lower():
            fail(
                failures,
                f"{label}: recorded sha256 {digest_value!r} does not match "
                f"the file's actual digest {actual!r}",
            )


def check_top_level_shapes(manifest: dict[str, Any], failures: list[str]) -> None:
    """Validate every string in the manifest against its own field schema,
    field by field, never as one blind scan over the serialized document."""
    walk_and_validate_strings(manifest, "", failures)


def verify(manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    check_required_fields(manifest, failures)
    check_provider_status(manifest, failures)
    check_andrea_status(manifest, failures)
    check_digests(manifest, failures)
    check_top_level_shapes(manifest, failures)
    return failures


def main(argv: list[str]) -> int:
    path = (
        Path(argv[1])
        if len(argv) > 1
        else REPO_ROOT / "docs" / "evidence" / "unit12" / "proof-pack.json"
    )
    if not path.is_file():
        print(f"no proof pack at {path}")
        return 2
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FAIL: {path} is not valid JSON: {error}")
        return 1
    if not isinstance(manifest, dict):
        print("FAIL: proof pack top level must be a JSON object")
        return 1

    failures = verify(manifest)
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"\n{len(failures)} problem(s): proof pack is not valid.")
        return 1
    print(
        "proof pack valid: required fields present, provider statuses honest, "
        "digests match, no evidence-path escape, no secret-shaped content."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
