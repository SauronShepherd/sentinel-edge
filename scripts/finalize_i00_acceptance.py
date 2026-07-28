from __future__ import annotations

import argparse
import datetime as dt
import json

from _repo import ROOT, load_json, repo_path, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-evidence", required=True)
    parser.add_argument("--passed", type=int, required=True)
    args = parser.parse_args()

    evidence_path = repo_path(args.gate_evidence)
    if not evidence_path.is_file():
        print(f"missing gate evidence: {args.gate_evidence}")
        return 1

    capability = load_json(ROOT / "provenance/capability-status.yaml")
    i00 = next(item for item in capability["capabilities"] if item["id"] == "I00")
    if i00["state"] != "demonstrated":
        print("I00 capability must be demonstrated before acceptance is finalized")
        return 1

    path = ROOT / "provenance/iterations/I00/acceptance.yaml"
    record = load_json(path)
    record["status"] = "complete"
    record["stages"] = {key: "complete" for key in record["stages"]}
    record["test_counts"] = {
        "passed": args.passed,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "rerun": 0,
        "collection_errors": 0,
    }
    record["evidence"] = [
        {"path": str(evidence_path.relative_to(ROOT)), "sha256": sha256_file(evidence_path)},
        {"path": "provenance/iterations/I00/evidence/adr-validation.json", "sha256": sha256_file(ROOT / "provenance/iterations/I00/evidence/adr-validation.json")},
        {"path": "provenance/iterations/I00/evidence/workspace-dependency-graph.json", "sha256": sha256_file(ROOT / "provenance/iterations/I00/evidence/workspace-dependency-graph.json")},
        {"path": "provenance/iterations/I00/evidence/controlled-failure-proof.txt", "sha256": sha256_file(ROOT / "provenance/iterations/I00/evidence/controlled-failure-proof.txt")},
        {"path": "provenance/iterations/I00/evidence/controlled-skip-proof.txt", "sha256": sha256_file(ROOT / "provenance/iterations/I00/evidence/controlled-skip-proof.txt")},
        {"path": "provenance/iterations/I00/evidence/ci-workflow-validation.txt", "sha256": sha256_file(ROOT / "provenance/iterations/I00/evidence/ci-workflow-validation.txt")},
        {"path": "provenance/iterations/I00/evidence/capability-registry-validation.txt", "sha256": sha256_file(ROOT / "provenance/iterations/I00/evidence/capability-registry-validation.txt")},
        {"path": "provenance/iterations/I00/evidence/source-baseline-validation.txt", "sha256": sha256_file(ROOT / "provenance/iterations/I00/evidence/source-baseline-validation.txt")},
        {"path": "build/test-results/governance.xml", "sha256": sha256_file(ROOT / "build/test-results/governance.xml")},
    ]
    clean_checkout = ROOT / "provenance/iterations/I00/evidence/clean-checkout-gate.txt"
    if clean_checkout.is_file():
        record["evidence"].append({"path": str(clean_checkout.relative_to(ROOT)), "sha256": sha256_file(clean_checkout)})
    record["accepted_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print("I00 acceptance finalized: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
