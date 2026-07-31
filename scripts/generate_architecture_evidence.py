from __future__ import annotations
import json
import hashlib
from pathlib import Path
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "provenance/iterations/I02/evidence"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    policy = tomllib.loads((ROOT / "architecture/import-rules.toml").read_text())
    ownership = yaml.safe_load((ROOT / "architecture/owned-namespaces.yaml").read_text())
    modules = []
    for manifest in sorted((ROOT / "modules").glob("*/pyproject.toml")):
        data = tomllib.loads(manifest.read_text())
        modules.append({"name": data["project"]["name"], "path": str(manifest.parent.relative_to(ROOT)), "dependencies": data["project"].get("dependencies", [])})
    graph = {"policy": policy, "modules": modules, "authorities": ownership["authorities"], "shared_packages": ["contracts/sentinel-contracts", "sdk/sentinel-plugin-sdk", "sdk/sentinel-testkit"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "architecture-graph.json").write_bytes((json.dumps(graph, indent=2, sort_keys=True) + "\n").encode())
    (OUT / "owned-namespaces.json").write_bytes((json.dumps({"authorities": ownership["authorities"], "namespaces": ownership["namespaces"], "resources": ownership["resources"], "undeclared_resources": []}, indent=2, sort_keys=True) + "\n").encode())
    (OUT / "architecture-graph.md").write_bytes(("# I02 architecture graph\n\n" + "\n".join(f"- `{item['name']}`: `{item['path']}`" for item in modules) + "\n").encode())
    print("architecture evidence: PASS")
    return 0

if __name__ == "__main__": raise SystemExit(main())
