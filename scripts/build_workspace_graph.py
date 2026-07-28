from __future__ import annotations

import argparse
import json
import tomllib

from _repo import ROOT, repo_path

PLANNED_NODES = [
    "contracts/sentinel-contracts",
    "sdk/sentinel-plugin-sdk",
    "sdk/sentinel-testkit",
    "modules/streaming-source-collector",
    "modules/analysis-enrichment-engine",
    "modules/model-workload-runtime",
    "modules/incident-event-engine",
    "modules/rest-api-integration-gateway",
    "modules/client-applications",
    "apps/sentinel-node",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_dependencies = data.get("project", {}).get("dependencies", [])
    if runtime_dependencies:
        print(f"I00 workspace must not have runtime dependencies: {runtime_dependencies}")
        return 1
    graph = {
        "schema_version": 1,
        "workspace": data["project"]["name"],
        "runtime_dependencies": [],
        "active_nodes": ["delivery-governance"],
        "planned_nodes": PLANNED_NODES,
        "implementation_edges": [],
        "authority_note": "No domain module is active in I00; future edges must use public contracts and ports.",
    }
    target = repo_path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("workspace dependency graph: PASS (zero implementation edges)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
