import pytest

from sentinel_edge.gateway.schema_refs import resolve_schema_refs


def test_only_local_refs_resolve_and_descriptions_are_bounded() -> None:
    doc = {"components": {"schemas": {"Thing": {"type": "object", "description": "a\n b"}}}, "$ref": "#/components/schemas/Thing"}
    result = resolve_schema_refs(doc)
    assert result["type"] == "object"
    assert result["description"] == "a b"


def test_external_refs_cycles_and_size_fail_closed() -> None:
    with pytest.raises(ValueError, match="external"):
        resolve_schema_refs({"$ref": "https://example.invalid/schema.json"})
    with pytest.raises(ValueError, match="bounds"):
        resolve_schema_refs({"$ref": "#/self", "self": {"$ref": "#/self"}}, max_depth=2)
