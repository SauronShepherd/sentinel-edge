import json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

def test_all_contract_schemas_are_valid_json():
    schemas = Path("contracts/sentinel-contracts/schemas")
    files = list(schemas.glob("*.json"))
    assert len(files) == 5
    examples = yaml.safe_load(Path("contracts/sentinel-contracts/examples/golden-v1.yaml").read_text())
    for path in files:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        family = path.stem.split(".")[0]
        fixture = examples[family]
        Draft202012Validator(schema).validate(fixture["valid"])
        assert list(Draft202012Validator(schema).iter_errors(fixture["invalid"]))

def test_catalog_references_every_schema_family():
    catalog = Path("contracts/sentinel-contracts/catalog.yaml").read_text()
    for family in ("collector", "analyzer", "runtime", "incident", "api"):
        assert f"id: {family}" in catalog
        assert (Path("contracts/sentinel-contracts/schemas") / f"{family}.v1.json").is_file()
