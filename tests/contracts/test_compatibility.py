import json
from pathlib import Path
from scripts.check_compatibility import compare

def test_current_n_minus_one_policy_covers_breaking_changes():
    text = Path("contracts/compatibility-matrix/current-n-1.yaml").read_text()
    for marker in ("remove-required-field", "change-field-identity", "change-field-type"):
        assert marker in text
    schema = json.loads(Path("contracts/sentinel-contracts/schemas/collector.v1.json").read_text())
    assert "observation_id" in schema["required"]

def test_breaking_type_mutation_is_rejected():
    schema = json.loads(Path("contracts/sentinel-contracts/schemas/collector.v1.json").read_text())
    mutated = json.loads(json.dumps(schema))
    mutated["properties"]["observation_id"]["type"] = "integer"
    assert "changed field type: observation_id" in compare(schema, mutated)

def test_required_removal_enum_and_nullability_mutations_are_rejected():
    schema = {"required": ["state"], "properties": {"state": {"type": "string", "enum": ["a", "b"], "nullable": True}}}
    removed = {"required": [], "properties": schema["properties"]}
    narrowed = {"required": schema["required"], "properties": {"state": {"type": "string", "enum": ["a"], "nullable": False}}}
    assert "removed required field: state" in compare(schema, removed)
    errors = compare(schema, narrowed)
    assert "narrowed enum: state" in errors
    assert "narrowed nullability: state" in errors
