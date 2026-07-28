import json
from pathlib import Path

def test_current_n_minus_one_policy_covers_breaking_changes():
    text = Path("contracts/compatibility-matrix/current-n-1.yaml").read_text()
    for marker in ("remove-required-field", "change-field-identity", "change-field-type"):
        assert marker in text
    schema = json.loads(Path("contracts/sentinel-contracts/schemas/collector.v1.json").read_text())
    assert "observation_id" in schema["required"]
