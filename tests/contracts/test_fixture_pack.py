from __future__ import annotations

import pytest

from sovereign_agent.contracts import (
    ExecutionReceipt,
    GovernedExecutionRequest,
    RuntimeCapabilityManifest,
)
from sovereign_agent.contracts.fixtures import FIXTURE_NAMES, load_fixture, read_fixture


def test_shipped_fixture_names_are_stable() -> None:
    assert FIXTURE_NAMES == (
        "capability-manifest.valid.json",
        "governed-execution-request.valid.json",
        "execution-receipt.valid.json",
        "compatibility-matrix.json",
    )
    for name in FIXTURE_NAMES:
        assert read_fixture(name)


def test_installed_fixtures_round_trip_typed_contracts() -> None:
    RuntimeCapabilityManifest.from_dict(load_fixture("capability-manifest.valid.json"))
    request = GovernedExecutionRequest.from_dict(
        load_fixture("governed-execution-request.valid.json")
    )
    receipt = ExecutionReceipt.from_dict(load_fixture("execution-receipt.valid.json"))
    assert request.operation == "run"
    assert receipt.status.value == "succeeded"


def test_compatibility_matrix_includes_previous_published_pair() -> None:
    matrix = load_fixture("compatibility-matrix.json")
    previous, current = matrix["pairs"]
    assert previous["sovereign_agent"] == "0.2.0"
    assert previous["zeocore"] is None
    assert current["sovereign_agent"] == "0.5.1"
    assert current["zeocore"] == ">=0.5,<0.6"
    assert current["python"] == ">=3.13"


def test_unknown_fixture_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown contract fixture"):
        load_fixture("not-a-fixture.json")
