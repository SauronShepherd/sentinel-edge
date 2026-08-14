"""Validate requirement-to-task/test/evidence traceability projections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.generate_conformance_ledger import generate
except ModuleNotFoundError:  # direct script execution
    from generate_conformance_ledger import generate


ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path) -> dict[str, object]:
    ledger, _ = generate(root)
    failures: list[str] = []
    for row in ledger["rows"]:
        requirement_id = row["requirement_id"]
        if row["profile"] == "H0" and not row["implementation_task_ids"]:
            failures.append(f"missing_implementation_task:{requirement_id}")
        if row["profile"] == "H0" and not row["verification_test_ids"]:
            failures.append(f"missing_verification_test:{requirement_id}")
        if not row["target_evidence_backed"] and not row["deferral_reason"]:
            failures.append(f"missing_evidence_disposition:{requirement_id}")
        for ref in row["artifact_refs"]:
            if not ref.get("evidence_id") or not ref.get("path"):
                failures.append(f"invalid_artifact_ref:{requirement_id}")
    return {
        "valid": not failures,
        "requirement_count": ledger["requirement_count"],
        "h0_count": ledger["profile_counts"]["H0"],
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
