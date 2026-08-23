"""Internal helpers shared by the wire-contract models."""

from __future__ import annotations

import copy
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class ContractValidationError(ValueError):
    """A wire value does not satisfy its contract."""


@dataclass(frozen=True)
class FrozenDict(Mapping[str, Any]):
    """Small immutable mapping used to make frozen contracts deeply immutable."""

    _items: tuple[tuple[str, Any], ...] = ()

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, key: str) -> Any:
        for item_key, value in self._items:
            if item_key == key:
                return value
        raise KeyError(key)

    def __hash__(self) -> int:
        return hash(self._items)


def freeze_json(value: Any, *, path: str = "$") -> Any:
    """Validate and deeply freeze a JSON-compatible value."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ContractValidationError(f"{path} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        items: list[tuple[str, Any]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractValidationError(f"{path} has a non-string object key")
            items.append((key, freeze_json(item, path=f"{path}.{key}")))
        return FrozenDict(tuple(items))
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item, path=f"{path}[{index}]") for index, item in enumerate(value))
    raise ContractValidationError(f"{path} contains non-JSON value {type(value).__name__}")


def thaw_json(value: Any) -> JsonValue:
    """Return a detached mutable JSON representation of a frozen value."""
    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [thaw_json(item) for item in value]
    return copy.deepcopy(value)


def require_object(data: object, name: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ContractValidationError(f"{name} must be a JSON object")
    if not all(isinstance(key, str) for key in data):
        raise ContractValidationError(f"{name} keys must be strings")
    return data


def require_string(value: object, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise ContractValidationError(f"{name} must be {qualifier}")
    return value


def parse_datetime(value: object, name: str) -> datetime:
    text = require_string(value, name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractValidationError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractValidationError(f"{name} must include a UTC offset")
    return parsed.astimezone(UTC)


def format_datetime(value: datetime, name: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ContractValidationError(f"{name} must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: object) -> bytes:
    """Encode JSON deterministically as UTF-8, independent of insertion order."""
    thawed = thaw_json(freeze_json(value))
    return json.dumps(
        thawed,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def split_known(
    data: Mapping[str, Any], known: frozenset[str]
) -> tuple[dict[str, Any], FrozenDict]:
    values = {key: data[key] for key in known if key in data}
    unknown = freeze_json({key: value for key, value in data.items() if key not in known})
    assert isinstance(unknown, FrozenDict)
    return values, unknown


def merge_unknown(known: dict[str, JsonValue], unknown: Mapping[str, Any]) -> dict[str, JsonValue]:
    collision = known.keys() & unknown.keys()
    if collision:
        raise ContractValidationError(
            f"unknown fields collide with known fields: {sorted(collision)}"
        )
    result = {key: thaw_json(value) for key, value in unknown.items()}
    result.update(known)
    return result
