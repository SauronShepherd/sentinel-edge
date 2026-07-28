
from __future__ import annotations

import sys

from _repo import ROOT, load_json

LANE_TO_CAPABILITY = {
    "test-all-modules": "I02",
    "plugins": "I01",
    "contracts": "I01",
    "components": "I02",
    "consumer-provider": "I03",
    "pairwise": "I03",
    "slices": "I08",
    "scenario": "I08",
    "chaos": "I16",
    "security": "I17",
    "privacy": "I17",
    "accessibility": "I07",
    "test-arm": "I18",
    "benchmark": "I18",
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in LANE_TO_CAPABILITY:
        print(f"unknown capability lane: {sys.argv[1:]}")
        return 2
    lane = sys.argv[1]
    target = LANE_TO_CAPABILITY[lane]
    data = load_json(ROOT / "provenance/capability-status.yaml")
    cap = next(item for item in data["capabilities"] if item["id"] == target)
    if cap["state"] == "planned":
        print(f"{lane}: PLANNED ({target}); excluded by capability registry, not counted as passing evidence")
        return 0
    if not cap["acceptance_tests"]:
        print(f"{lane}: active capability {target} has no acceptance tests")
        return 1
    print(f"{lane}: active via {target}; acceptance tests are executed by their owning gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
