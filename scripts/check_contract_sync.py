from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "docs/contracts/sentinel-edge-full-scope-product-contract-v0.22.0.md"
TECH = ROOT / "docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md"


def main() -> int:
    product_text = PRODUCT.read_text(encoding="utf-8")
    tech_text = TECH.read_text(encoding="utf-8")
    contract_requirements = set(re.findall(r"^\| (FR-[A-Z0-9-]+) \|", product_text, re.MULTILINE))
    contract_adrs = set(re.findall(r"^### (?:\d+(?:\.\d+)* )?(ADR-\d{3}) —", tech_text, re.MULTILINE))
    requirements = yaml.safe_load((ROOT / "registries/requirements.yaml").read_text(encoding="utf-8"))["items"]
    decisions = yaml.safe_load((ROOT / "registries/decisions.yaml").read_text(encoding="utf-8"))["items"]
    registry_requirements = {"FR-" + item["id"][4:] for item in requirements}
    registry_adrs = {f"ADR-{int(item['id'].split('-')[1]):03d}" for item in decisions}
    errors = []
    if len(contract_requirements) != 743 or contract_requirements != registry_requirements:
        errors.append("requirement registry does not exactly match the 743-row product contract")
    if len(contract_adrs) != 193 or contract_adrs != registry_adrs:
        errors.append("decision registry does not exactly match the 193-ADR technical contract")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 743 requirements and 193 ADRs are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
