from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "sentinel-contracts" / "schemas"
OUT = ROOT / "contracts" / "generated"

def generate() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    names = []
    for schema in sorted(SCHEMAS.glob("*.json")):
        data = json.loads(schema.read_text(encoding="utf-8"))
        name = schema.stem.replace(".v1", "")
        names.append(name)
        (OUT / f"{name}.json").write_bytes((json.dumps(data, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    (OUT / "catalog.json").write_bytes((json.dumps({"version": 1, "schemas": names}, indent=2) + "\n").encode("utf-8"))
    (OUT / "python_bindings.py").write_bytes(("# generated; do not edit\nSCHEMAS = " + repr(names) + "\n").encode("utf-8"))
    (OUT / "typescript_bindings.ts").write_bytes(("// generated; do not edit\nexport type ContractFamily = " + " | ".join(repr(n) for n in names) + ";\n").encode("utf-8"))
    (OUT / "openapi.json").write_bytes((json.dumps({"openapi":"3.1.0","info":{"title":"Sentinel Edge API","version":"1.0.0"},"paths":{}}, indent=2) + "\n").encode("utf-8"))
    (OUT / "asyncapi.json").write_bytes((json.dumps({"asyncapi":"3.0.0","info":{"title":"Sentinel Edge Events","version":"1.0.0"},"channels":{}}, indent=2) + "\n").encode("utf-8"))

if __name__ == "__main__": generate()
