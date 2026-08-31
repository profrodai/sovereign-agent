"""Shape and shared validation helpers for the Unit 12 redacted proof pack.

`docs/evidence/unit12/proof-pack.json` is the machine-verifiable manifest
governing ruling Holding 2 requires. This module names its required fields,
the exact shapes those fields are validated against, and the two narrow
free-text secret-shaped patterns `verify_proof_pack.py` scans for. It holds
no CLI of its own -- `verify_proof_pack.py` is the entry point; this module
exists so the schema is named once and reused, not duplicated between the
verifier and anything that later needs to construct a conforming manifest.

Lives in `scripts/`, not `src/sovereign_agent/`, matching this unit's own
budget instruction: the proof pack is a release/evidence surface, the same
split Unit 9 established for `pulse_gate.py` and Unit 11 continued for
`pilot.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Provider status: exactly one of these four values, no fifth, no free text.
# ---------------------------------------------------------------------------

PROVIDER_STATUSES = frozenset(
    {"LIVE_PASS", "NOT_RUN_UNAVAILABLE", "NOT_RUN_UNAUTHENTICATED", "FAIL"}
)
NOT_RUN_STATUSES = frozenset({"NOT_RUN_UNAVAILABLE", "NOT_RUN_UNAUTHENTICATED"})
REQUIRED_PROVIDERS = ("claude", "codex", "cursor")

# ---------------------------------------------------------------------------
# The evidence directory every evidence path must resolve inside.
# ---------------------------------------------------------------------------

EVIDENCE_DIR_NAME = "docs/evidence/unit12"

# ---------------------------------------------------------------------------
# Known field shapes. A field matching one of these MUST be validated against
# its own shape and never rejected merely for being long -- the exact defect
# the SOW names as caught twice before (a git commit SHA is 40 hex chars, a
# SHA-256 digest is 64 hex chars, and both would trip a blind entropy rule).
# ---------------------------------------------------------------------------

COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-.](?:dev|a|b|rc)\d*)?$")

# Dotted-path field names (using "." to mean "any object key at this level")
# that carry a known fixed shape. Anything not listed here that is a string
# is treated as free text and scanned for the two narrow secret patterns
# below, never for length or entropy.
KNOWN_SHAPE_FIELDS: dict[str, re.Pattern[str]] = {
    "source_commit": COMMIT_SHA_RE,
    "release_candidate_commit": COMMIT_SHA_RE,
    "python_version": re.compile(r"^\d+\.\d+\.\d+$"),
    "package_version": SEMVER_RE,
    "sha256": SHA256_DIGEST_RE,
    "digest": SHA256_DIGEST_RE,
}

# Field NAMES (last path component) that hold a path string, validated
# against the path-escape rule rather than any secret-shaped pattern.
PATH_FIELD_NAMES = frozenset({"path", "evidence_path"})

# ---------------------------------------------------------------------------
# The two narrow secret-shaped patterns free-text fields are scanned for.
# No entropy heuristic. No blind length check.
# ---------------------------------------------------------------------------

# (a) a known credential env-var NAME immediately followed by '=' and a
# non-empty, non-placeholder value. The names come directly from each
# provider adapter's own `authentication_environment` tuple:
#   ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, CLAUDE_CODE_OAUTH_TOKEN
#     (src/sovereign_agent/providers/claude.py:24-27)
#   CODEX_API_KEY (src/sovereign_agent/providers/codex.py:26)
#   CURSOR_API_KEY (src/sovereign_agent/providers/cursor.py:24)
CREDENTIAL_ENV_VAR_NAMES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CODEX_API_KEY",
    "CURSOR_API_KEY",
)

# A NAME=value assignment: the name, an '=', then at least one non-whitespace
# character that is not obviously a placeholder like "<redacted>" or "...".
# A bare variable name (no '=') or a name inside a sentence describing that
# it was redacted must NOT match this.
_NAMES_ALTERNATION = "|".join(re.escape(name) for name in CREDENTIAL_ENV_VAR_NAMES)
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    rf"\b(?:{_NAMES_ALTERNATION})=(?!\s*$)(?!<[^>]*>)(?!\.\.\.$)\S+"
)

# (b) a literal "Bearer <token>" HTTP authorization-header shape. The token
# itself must look like a credential (8+ characters of token-alphabet: letters,
# digits, '-', '_', '.') so ordinary prose mentioning the word "Bearer" (e.g.
# "the Bearer pattern is checked") does not false-positive -- this is still
# not a general entropy heuristic: it fires only immediately after the
# literal word "Bearer", the fixed HTTP authorization-header shape.
BEARER_TOKEN_RE = re.compile(r"\bBearer\s+[A-Za-z0-9\-_.]{8,}\b")

# ---------------------------------------------------------------------------
# Required top-level manifest fields (Holding 2 / SOW section 1).
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL_FIELDS = (
    "source_commit",
    "release_candidate_commit",
    "python_version",
    "package_version",
    "artifact_digests",
    "deterministic_gate_results",
    "installed_wheel_results",
    "local_pilot_mechanism_evidence",
    "andrea_live_evaluation",
    "provider_status",
    "redactions_performed",
    "non_claims",
    "evidence_files",
)


@dataclass(frozen=True)
class ValidationError:
    """One named rejection reason -- never a bare boolean."""

    reason: str


@dataclass(frozen=True)
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def messages(self) -> list[str]:
        return [error.reason for error in self.errors]
