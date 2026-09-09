"""Executable checker for the Chapter 9 lab."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def check(target_module: ModuleType, root: Path) -> dict[str, object]:
    observed = target_module.exercise(root)
    reservation = observed["reservation"]
    assert reservation["result"] == "requested 4, available 3"
    assert reservation["state"] == {
        "on_hand": 5,
        "reserved": 2,
        "available": 3,
        "cash_total": 0,
        "cash_rows": 0,
        "event_rows": 0,
    }
    committed = observed["committed_sale"]
    assert committed["receipt"] == {"sale_id": "sale-one", "quantity": 2, "amount_cents": 850}
    assert committed["event_payload"] == {
        "amount_cents": 850,
        "qty": 2,
        "sale_id": "sale-one",
        "sku": "SKU-GELATO",
    }
    assert committed["state"] == {
        "on_hand": 3,
        "reserved": 2,
        "available": 1,
        "cash_total": 850,
        "cash_rows": 1,
        "event_rows": 1,
    }
    fault = observed["fault_injection"]
    assert fault["result"] == "injected failure after cash"
    assert fault["state_unchanged"] is True, "inventory, cash, and event must roll back together"
    assert fault["state"] == committed["state"]
    contention = observed["contention"]
    assert contention["statuses"] == ["committed", "refused"]
    assert contention["state"] == {
        "on_hand": 1,
        "reserved": 0,
        "available": 1,
        "cash_total": 850,
        "cash_rows": 1,
        "event_rows": 1,
    }
    return observed


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("student_ch09", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    module = _load(Path(sys.argv[1]))
    print(json.dumps(check(module, Path(sys.argv[2])), indent=2, sort_keys=True))
