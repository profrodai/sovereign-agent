from __future__ import annotations

import json

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
