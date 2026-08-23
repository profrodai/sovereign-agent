from __future__ import annotations

import json
from datetime import UTC, datetime

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from sovereign_agent.contracts import (
    EvidenceLevel,
    ExecutionId,
    ExecutionReceipt,
    GovernedExecutionRequest,
    InvocationId,
    ReceiptStatus,
    RepositoryId,
    RuntimeCapabilityAssertion,
    RuntimeCapabilityManifest,
    SeatId,
    SeatInstanceId,
    SovereignSessionId,
)
from sovereign_agent.contracts.schemas import SCHEMA_NAMES, read_schema, schema_path


def test_all_contract_schemas_are_bundled_and_valid_json() -> None:
    assert set(SCHEMA_NAMES) == {
        "capability-manifest.schema.json",
        "execution-receipt.schema.json",
        "governed-execution-request.schema.json",
    }
    for name in SCHEMA_NAMES:
        payload = json.loads(read_schema(name))
        assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert payload["$id"].startswith("https://zeroemployee.org/schemas/")
        assert schema_path(name).is_file()


def test_schemas_preserve_forward_compatible_unknown_fields() -> None:
    for name in SCHEMA_NAMES:
        payload = json.loads(read_schema(name))
        assert payload["additionalProperties"] is True


def test_schemas_do_not_reference_an_internal_or_invented_corpus_path() -> None:
    for name in SCHEMA_NAMES:
        text = read_schema(name).decode()
        assert "sovereign_agent." not in text
        assert "/corpus/" not in text
        assert "../" not in text


def test_canonical_contract_instances_validate_against_bundled_schemas() -> None:
    manifest = RuntimeCapabilityManifest(
        {
            "network": RuntimeCapabilityAssertion(
                available=None,
                evidence_level=EvidenceLevel.UNKNOWN,
            )
        }
    )
    request = GovernedExecutionRequest(
        seat_instance_id=SeatInstanceId("seat-01"),
        sovereign_session_id=SovereignSessionId("session-01"),
        execution_id=ExecutionId("execution-01"),
        invocation_id=InvocationId("invocation-01"),
        repository_id=RepositoryId("repo:zeroemployee/sovereign-agent"),
        operation="run",
        input={"prompt": "check"},
        governance={"network": "restricted"},
        capability_manifest=manifest,
        requested_at=datetime(2026, 8, 22, 12, 0, tzinfo=UTC),
        conversation_id="round-1",
        seat_type=SeatId("zeo-stream"),
        requested_by="projects/runtime-SOW-1.md",
        authority_refs=("ruling/RULING-359.md",),
        work_artifact_refs=("projects/runtime-SOW-1.md",),
        base_ref="origin/main",
        branch="sovereign/seat-01/execution-01",
    )
    original = ExecutionReceipt(
        execution_id=ExecutionId("execution-01"),
        invocation_id=InvocationId("invocation-01"),
        status=ReceiptStatus.SUCCEEDED,
        started_at=datetime(2026, 8, 22, 12, 0, tzinfo=UTC),
        completed_at=datetime(2026, 8, 22, 12, 1, tzinfo=UTC),
        result={"summary": "ok"},
        evidence={"verification": True},
    ).finalize()
    corrected = original.supersede(
        status=ReceiptStatus.SUCCEEDED,
        completed_at=datetime(2026, 8, 22, 12, 2, tzinfo=UTC),
        result={"summary": "corrected"},
    )

    schemas = {name: json.loads(read_schema(name)) for name in SCHEMA_NAMES}
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema),
        )

    for schema_name, instance in (
        ("capability-manifest.schema.json", manifest.to_dict()),
        ("governed-execution-request.schema.json", request.to_dict()),
        ("execution-receipt.schema.json", original.to_dict()),
        ("execution-receipt.schema.json", corrected.to_dict()),
    ):
        Draft202012Validator(schemas[schema_name], registry=registry).validate(instance)
