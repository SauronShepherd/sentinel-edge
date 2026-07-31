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
    models = {s.stem.split(".")[0]: json.loads(s.read_text(encoding="utf-8")) for s in sorted(SCHEMAS.glob("*.json"))}
    py = ["# generated; do not edit", "from dataclasses import dataclass", ""]
    ts = ["// generated; do not edit", ""]
    def typ(spec: dict[str, object]) -> str:
        t=spec.get("type", "object")
        if isinstance(t, list): t = next((x for x in t if x != "null"), "object")
        return {"string":"str","integer":"int","number":"float","boolean":"bool","array":"tuple[object, ...]","object":"dict[str, object]"}.get(t,"object")
    def tst(spec: dict[str, object]) -> str:
        t=spec.get("type", "unknown")
        if isinstance(t, list): t = " | ".join(t)
        return {"string":"string","integer":"number","number":"number","boolean":"boolean","array":"unknown[]","object":"Record<string, unknown>"}.get(t,"unknown")
    for name, schema in models.items():
        cls = "".join(part.title() for part in name.split("_")) + "V1"
        fields = schema.get("properties", {})
        py += ["@dataclass(frozen=True)", f"class {cls}:"] + [f"    {field}: {typ(spec)}" for field, spec in fields.items()] + [""]
        ts += [f"export interface {cls} {{"] + [f"  {field}: {tst(spec)};" for field, spec in fields.items()] + ["}", ""]
    (OUT / "python_bindings.py").write_bytes(("\n".join(py) + "\n").encode("utf-8"))
    (OUT / "typescript_bindings.ts").write_bytes(("\n".join(ts) + "\n").encode("utf-8"))
    paths = {f"/{name}": {"get": {"responses": {"200": {"description": "OK", "content": {"application/json": {"schema": schema}}}}}} for name, schema in models.items()}
    channels = {name: {"messages": {"v1": {"payload": schema}}} for name, schema in models.items()}
    (OUT / "openapi.json").write_bytes((json.dumps({"openapi":"3.1.0","info":{"title":"Sentinel Edge API","version":"1.0.0"},"paths":paths}, indent=2) + "\n").encode("utf-8"))
    (OUT / "asyncapi.json").write_bytes((json.dumps({"asyncapi":"3.0.0","info":{"title":"Sentinel Edge Events","version":"1.0.0"},"channels":channels}, indent=2) + "\n").encode("utf-8"))

if __name__ == "__main__": generate()
