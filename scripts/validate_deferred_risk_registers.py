"""Validate generated deferred-debt and residual-risk registers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.generate_deferred_risk_registers import generate
except ModuleNotFoundError:  # direct script execution
    from generate_deferred_risk_registers import generate


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id", "owner", "severity", "rationale", "dependency", "safe_limitation", "status"}


def validate(root: Path) -> dict[str, object]:
    expected_debt, expected_risks = generate(root)
    failures: list[str] = []
    for name, expected in (("deferred-debt-register.json", expected_debt), ("residual-risk-register.json", expected_risks)):
        path = root / "qualification" / name
        try:
            actual = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            failures.append(f"missing_or_invalid:{name}")
            continue
        if actual != expected:
            failures.append(f"projection_drift:{name}")
        for index, item in enumerate(actual.get("items", [])):
            failures.extend(f"{name}[{index}]:missing:{field}" for field in sorted(REQUIRED - set(item)))
    return {"valid": not failures, "deferred_debt": len(expected_debt["items"]), "residual_risks": len(expected_risks["items"]), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
