"""Reject priority/profile disagreement between contracts and registries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "docs/contracts/sentinel-edge-full-scope-product-contract-v0.22.0.md"
TECHNICAL = "docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md"
PRODUCT_ROW = re.compile(r"^\| (FR-[A-Z0-9-]+) \| (?:MUST|SHOULD) \| `?(H[01])`? \|", re.MULTILINE)
TECHNICAL_ROW = re.compile(r"^\| (FR-[A-Z0-9-]+) \| (?:MUST|SHOULD) / `?(H[01])`?", re.MULTILINE)


def profiles(text: str, pattern: re.Pattern[str]) -> dict[str, str]:
    return dict(pattern.findall(text))


def validate(root: Path) -> dict[str, object]:
    product_path = root / PRODUCT
    technical_path = root / TECHNICAL
    product_text = product_path.read_text(encoding="utf-8")
    technical_text = technical_path.read_text(encoding="utf-8")
    product = profiles(product_text, PRODUCT_ROW)
    technical = profiles(technical_text, TECHNICAL_ROW)
    requirements = yaml.safe_load((root / "registries/requirements.yaml").read_text(encoding="utf-8"))["items"]
    registry = {"FR-" + item["id"][4:]: item for item in requirements}
    failures: list[str] = []
    for source, mapping in (("product", product), ("technical", technical)):
        for functional_id, expected in mapping.items():
            actual = registry.get(functional_id)
            if actual is None:
                failures.append(f"registry_missing:{functional_id}:{source}")
                continue
            registry_profile = "H0" if "profile H0" in actual.get("statement", "") else "H1" if "profile H1" in actual.get("statement", "") else None
            if registry_profile != expected:
                failures.append(f"profile_mismatch:{functional_id}:{source}:{expected}!={registry_profile}")
            if expected == "H0" and actual.get("priority") != "P0":
                failures.append(f"priority_mismatch:{functional_id}:H0!={actual.get('priority')}")
    for functional_id in sorted(set(product) & set(technical)):
        if product[functional_id] != technical[functional_id]:
            failures.append(f"contract_profile_mismatch:{functional_id}:{product[functional_id]}!={technical[functional_id]}")
    return {
        "valid": not failures,
        "product_profile_count": len(product),
        "technical_profile_count": len(technical),
        "registry_count": len(registry),
        "contract_digests": {
            PRODUCT: hashlib.sha256(product_path.read_bytes()).hexdigest(),
            TECHNICAL: hashlib.sha256(technical_path.read_bytes()).hexdigest(),
        },
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
