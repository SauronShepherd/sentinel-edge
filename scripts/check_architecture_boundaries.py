from __future__ import annotations

import ast
import re
import tomllib
import yaml
import sys
from pathlib import Path

from _repo import ROOT

FORBIDDEN_IMPLEMENTATION_PREFIXES = (
    "sentinel_streaming_source_collector",
    "sentinel_analysis_enrichment_engine",
    "sentinel_model_workload_runtime",
    "sentinel_incident_event_engine",
    "sentinel_rest_api_integration_gateway",
    "modules.streaming_source_collector",
    "modules.analysis_enrichment_engine",
    "modules.model_workload_runtime",
    "modules.incident_event_engine",
    "modules.rest_api_integration_gateway",
    "modules.client_applications",
)


def check(root: Path) -> list[str]:
    errors: list[str] = []
    policy = tomllib.loads((root / "architecture/import-rules.toml").read_text(encoding="utf-8"))
    if not policy.get("rules", {}).get("forbidden_cross_module_imports", False):
        print("architecture policy disables cross-module import enforcement")
        return 1
    logical_for_dirs = {
        "streaming-source-collector": "collector", "analysis-enrichment-engine": "analyzer",
        "model-workload-runtime": "runtime", "incident-event-engine": "incidents",
        "rest-api-integration-gateway": "api", "client-applications": "client",
    }
    for path in sorted(root.rglob("*.py")):
        if any(part in {".venv", "build", "node_modules"} for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.startswith(FORBIDDEN_IMPLEMENTATION_PREFIXES):
                    owner = next((part for part in FORBIDDEN_IMPLEMENTATION_PREFIXES if part in path.parts), None)
                    target = next((part for part in FORBIDDEN_IMPLEMENTATION_PREFIXES if name.startswith(part)), None)
                    if owner is None or target != owner:
                        errors.append(f"{path.relative_to(root)}:{node.lineno}: forbidden module implementation import {name}")
        text = path.read_text(encoding="utf-8")
        owner = next((logical_for_dirs[part] for part in path.parts if part in logical_for_dirs), None)
        if owner:
            for namespace in re.findall(r"runtime/(collector|analyzer|runtime|incidents|api|client)(?:/|['\"])", text):
                if namespace != owner:
                    errors.append(f"{path.relative_to(root)}: cross-owned namespace runtime/{namespace}")
    source_docs = root / "docs/baseline/v0.13.0"
    if not source_docs.is_dir():
        errors.append("immutable source baseline directory is missing")
    ownership = yaml.safe_load((root / "architecture/owned-namespaces.yaml").read_text(encoding="utf-8"))
    authorities = ownership.get("authorities", {})
    expected = {
        "collector": "streaming-source-collector",
        "workload_execution": "model-workload-runtime",
        "incident_lifecycle": "incident-event-engine",
        "client_mutation_boundary": "rest-api-integration-gateway",
    }
    for authority, owner in expected.items():
        if authorities.get(authority) != owner:
            errors.append(f"authority {authority} must be owned by {owner}")
    business_distributions = {"sentinel-streaming-source-collector", "sentinel-analysis-enrichment-engine", "sentinel-model-workload-runtime", "sentinel-incident-event-engine", "sentinel-rest-api-integration-gateway"}
    for path in sorted((root / "modules").glob("*/pyproject.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        deps = {str(dep).split("[", 1)[0].split(">", 1)[0].split("=", 1)[0].strip() for dep in data.get("project", {}).get("dependencies", [])}
        own = str(data.get("project", {}).get("name", ""))
        forbidden = (deps & business_distributions) - {own}
        if forbidden: errors.append(f"{path.relative_to(root)}: forbidden business dependencies: {sorted(forbidden)}")
        if data.get("tool", {}).get("sentinel-edge", {}).get("incident_authority"):
            if path.parent.name != "incident-event-engine":
                errors.append(f"{path.relative_to(root)}: duplicate incident authority")
    for path in sorted((root / "modules").rglob("*.ts")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?:from|import)\s*['\"](?:sentinel_|.*(?:sqlite|internal-transport))", text):
            errors.append(f"{path.relative_to(root)}: forbidden client implementation import")
    namespace_paths = [item["path"] for item in ownership.get("namespaces", [])]
    if len(namespace_paths) != len(set(namespace_paths)):
        errors.append("duplicate owned namespace")
    return errors

def main() -> int:
    errors = check(ROOT)
    if errors: print("\n".join(errors)); return 1
    print("architecture boundary gate: PASS"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
