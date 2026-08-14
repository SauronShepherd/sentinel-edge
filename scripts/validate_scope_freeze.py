"""Reject unapproved changes to the frozen H0 scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.generate_scope_freeze import generate
except ModuleNotFoundError:  # direct script execution
    from generate_scope_freeze import generate


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_EXCEPTION_FIELDS = {"exception_id", "reason", "approver", "displaced_or_cut", "affected_requirements", "mandatory_reruns"}


def validate(root: Path) -> dict[str, object]:
    path = root / "qualification/scope-freeze.json"
    failures: list[str] = []
    try:
        actual = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"valid": False, "failures": ["scope_freeze_missing_or_invalid"]}
    expected = generate(root)
    for field in ("schema", "freeze_id", "requirements_sha256", "h0_ids_sha256", "h0_count", "exception_schema"):
        if actual.get(field) != expected[field]:
            failures.append(f"scope_freeze_drift:{field}")
    for index, exception in enumerate(actual.get("exceptions", [])):
        missing = REQUIRED_EXCEPTION_FIELDS - set(exception)
        failures.extend(f"exception[{index}]:missing:{field}" for field in sorted(missing))
        for field in ("reason", "approver", "displaced_or_cut"):
            if field in exception and not str(exception[field]).strip():
                failures.append(f"exception[{index}]:blank:{field}")
        if "mandatory_reruns" in exception and not exception["mandatory_reruns"]:
            failures.append(f"exception[{index}]:empty:mandatory_reruns")
    return {"valid": not failures, "h0_count": expected["h0_count"], "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
