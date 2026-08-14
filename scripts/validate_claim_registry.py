"""Validate generated Claim Registry closure and claim-class ceiling."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from sentinel_edge.release import ClaimRegistry


ROOT = Path(__file__).resolve().parents[1]
PERFORMANCE_VALUE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|ms|s|fps|joules?|w(?:atts?)?)(?=\s|$|[,.])", re.IGNORECASE)


def validate(root: Path) -> dict[str, object]:
    path = root / "qualification/claim-registry.json"
    failures: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ClaimRegistry.read(path)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {"valid": False, "claims": 0, "failures": [f"registry_invalid:{type(exc).__name__}"]}
    if payload.get("schema") != "sentinel-edge-claim-registry/1.0":
        failures.append("schema_mismatch")
    source_digests: set[str] = set()
    for item in payload.get("source_artifacts", []):
        source = root / item.get("path", "")
        if not source.is_file():
            failures.append(f"source_missing:{item.get('path')}")
        elif hashlib.sha256(source.read_bytes()).hexdigest() != item.get("sha256"):
            failures.append(f"source_digest_mismatch:{item.get('path')}")
        if isinstance(item.get("sha256"), str):
            source_digests.add(item["sha256"])
    ceiling = payload.get("claim_ceiling", {})
    if not ceiling.get("target_measurement_claim_allowed", False):
        for claim in payload.get("claims", []):
            if claim.get("claim_class") in {"measured", "target"}:
                failures.append(f"claim_exceeds_ceiling:{claim.get('claim_id')}")
    for claim in payload.get("claims", []):
        for artifact_ref in claim.get("artifact_refs", []):
            if not isinstance(artifact_ref, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", artifact_ref):
                failures.append(f"claim_artifact_ref_invalid:{claim.get('claim_id')}")
            elif artifact_ref.removeprefix("sha256:") not in source_digests:
                failures.append(f"claim_artifact_ref_unregistered:{claim.get('claim_id')}")
        if PERFORMANCE_VALUE.search(str(claim.get("statement", ""))):
            failures.append(f"hand_entered_performance_value:{claim.get('claim_id')}")
    return {"valid": not failures, "claims": len(payload.get("claims", [])), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
