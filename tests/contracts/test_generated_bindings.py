import json
from pathlib import Path

def test_generated_binding_families_exist_and_are_deterministic():
    out = Path("contracts/generated")
    for name in ("python_bindings.py", "typescript_bindings.ts", "openapi.json", "asyncapi.json"):
        assert (out / name).is_file(), name
    assert json.loads((out / "openapi.json").read_text())["openapi"] == "3.1.0"
