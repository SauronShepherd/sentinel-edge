"""Reject hand-edited conformance and acceptance projections."""

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
    expected_ledger, expected_checklist = generate(root)
    failures: list[str] = []
    for row in expected_ledger.get("rows", []):
        if "artifact_refs" not in row or "deferral_reason" not in row:
            failures.append(f"row_schema_missing:{row.get('requirement_id')}")
        if row.get("status") != "VERIFIED" and not row.get("deferral_reason"):
            failures.append(f"missing_deferral_reason:{row.get('requirement_id')}")
    for name, expected in (
        ("qualification/conformance-ledger.json", expected_ledger),
        ("qualification/release-acceptance-checklist.json", expected_checklist),
    ):
        path = root / name
        try:
            actual = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            failures.append(f"projection_missing_or_invalid:{name}")
            continue
        if actual != expected:
            failures.append(f"projection_drift:{name}")
    return {"valid": not failures, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
