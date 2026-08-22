"""Non-mutating redaction helpers for contract payloads and logs."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from ._core import ContractValidationError, freeze_json, thaw_json

REDACTED = "[REDACTED]"

DEFAULT_SENSITIVE_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "client_secret",
        "cookie",
        "password",
        "private_key",
        "refresh_token",
        "secret",
        "set-cookie",
        "token",
    }
)

_CREDENTIAL_TEXT = re.compile(
    r"(?i)\b(bearer\s+|(?:api[_-]?key|token|password|secret)\s*[=:]\s*)"
    r"([^\s,;\"']+)"
)


def _normalize_key(key: str) -> str:
    return key.casefold().replace("-", "_")


def redact_json(
    value: object,
    *,
    sensitive_keys: Iterable[str] = DEFAULT_SENSITIVE_KEYS,
    replacement: str = REDACTED,
) -> Any:
    """Return a detached JSON value with sensitive object members replaced."""
    if not isinstance(replacement, str):
        raise ContractValidationError("redaction replacement must be a string")
    normalized = {_normalize_key(key) for key in sensitive_keys}

    def visit(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                key: replacement if _normalize_key(key) in normalized else visit(child)
                for key, child in item.items()
            }
        if isinstance(item, (list, tuple)):
            return [visit(child) for child in item]
        return item

    return visit(thaw_json(freeze_json(value)))


def redact_mapping(
    value: Mapping[str, Any],
    *,
    sensitive_keys: Iterable[str] = DEFAULT_SENSITIVE_KEYS,
    replacement: str = REDACTED,
) -> dict[str, Any]:
    redacted = redact_json(value, sensitive_keys=sensitive_keys, replacement=replacement)
    assert isinstance(redacted, dict)
    return redacted


def redact_text(value: str, *, replacement: str = REDACTED) -> str:
    """Redact common inline credentials without changing unrelated text."""
    if not isinstance(value, str):
        raise ContractValidationError("text to redact must be a string")
    return _CREDENTIAL_TEXT.sub(lambda match: f"{match.group(1)}{replacement}", value)


__all__ = [
    "DEFAULT_SENSITIVE_KEYS",
    "REDACTED",
    "redact_json",
    "redact_mapping",
    "redact_text",
]
