"""Generate machine-readable deferred-debt and residual-risk registers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def generate(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    uncertainties_path = root / "registries/uncertainties.yaml"
    uncertainties = (yaml.safe_load(uncertainties_path.read_text(encoding="utf-8")) or {}).get("items", [])
    debt_items = [
        {
            "id": item["id"],
            "owner": item["owner"],
            "severity": item["severity"],
            "rationale": item["deferral_rationale"],
            "dependency": item["question"],
            "safe_limitation": "Development and fixture behavior remains available, but no target or field qualification claim is permitted.",
            "due_date": item.get("due_date"),
            "status": item["status"],
        }
        for item in uncertainties
    ]
    blockers_path = root / "docs/OPEN_BLOCKERS.md"
    blocker_lines = [
        line.strip() for line in blockers_path.read_text(encoding="utf-8").splitlines()
        if re.match(r"^\d+\.\s+", line.strip())
    ]
    risks = [
        {
            "id": f"RISK-OPEN-BLOCKER-{index:02d}",
            "owner": "release-owner",
            "severity": "BLOCKING",
            "rationale": text.split(". ", 1)[0] + ".",
            "dependency": text,
            "safe_limitation": "The release candidate remains not admitted and the limitation is surfaced in generated manifests.",
            "status": "OPEN",
        }
        for index, text in enumerate(blocker_lines, start=1)
    ]
    source_digests = {
        "registries/uncertainties.yaml": hashlib.sha256(uncertainties_path.read_bytes()).hexdigest(),
        "docs/OPEN_BLOCKERS.md": hashlib.sha256(blockers_path.read_bytes()).hexdigest(),
    }
    base = {"schema": "sentinel-edge.deferred-register.v1", "source_digests": source_digests}
    return ({**base, "items": debt_items}, {**base, "items": risks, "schema": "sentinel-edge.residual-risk-register.v1"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    debt, risks = generate(root)
    out = root / "qualification"
    out.mkdir(exist_ok=True)
    (out / "deferred-debt-register.json").write_text(json.dumps(debt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "residual-risk-register.json").write_text(json.dumps(risks, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"deferred_debt": len(debt["items"]), "residual_risks": len(risks["items"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
