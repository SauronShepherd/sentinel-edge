from __future__ import annotations

import json

from _repo import ROOT, load_json


def main() -> int:
    path = ROOT / "provenance/iterations/I00/acceptance.yaml"
    record = load_json(path)
    if record.get("iteration") != "I00":
        print("unexpected acceptance record")
        return 1
    record["status"] = "gate-running"
    record["accepted_at"] = None
    record["evidence"] = []
    record["test_counts"] = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "rerun": 0,
        "collection_errors": 0,
    }
    path.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print("I00 gate state: gate-running")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
