from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/uix-screen-contract.yaml"
OUTPUT = ROOT / "qualification/uix-conformance.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()



def main() -> int:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8")) or {}
    basis = contract.get("basis", {}) if isinstance(contract.get("basis"), dict) else {}
    spec_path = ROOT / str(basis.get("specification", ""))
    mockup_dir = ROOT / str(basis.get("reference_mockups", ""))
    basis_failures: list[str] = []
    if not spec_path.is_file():
        basis_failures.append("uix_specification_missing")
    mockups = sorted(mockup_dir.glob("*.png")) if mockup_dir.is_dir() else []
    if len(mockups) != 10:
        basis_failures.append(f"reference_mockup_count:{len(mockups)}")
    design_basis = {
        "specification": {
            "path": spec_path.relative_to(ROOT).as_posix() if spec_path.is_file() else str(basis.get("specification", "")),
            "sha256": sha256(spec_path) if spec_path.is_file() else None,
        },
        "reference_mockups": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in mockups
        ],
        "reference_mockup_count": len(mockups),
        "valid": not basis_failures,
        "failures": basis_failures,
    }
    source_map = contract.get("sources", {})
    if not isinstance(source_map, dict):
        raise SystemExit("uix_contract_invalid:sources")

    contents: dict[str, str] = {}
    source_records: dict[str, dict[str, Any]] = {}
    for key, rel in source_map.items():
        path = ROOT / str(rel)
        if not path.is_file():
            print(json.dumps({"valid": False, "reason": f"missing_source:{rel}"}, indent=2))
            return 2
        contents[str(key)] = path.read_text(encoding="utf-8")
        source_records[str(key)] = {
            "path": str(rel),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }

    results = []
    failures = list(basis_failures)
    for requirement in contract.get("requirements", []):
        rid = str(requirement.get("id", "missing"))
        checks = []
        requirement_passed = True
        for check in requirement.get("checks", []):
            source = str(check.get("source", ""))
            haystack = contents.get(source, "")
            all_tokens = [str(item) for item in check.get("all", [])]
            any_tokens = [str(item) for item in check.get("any", [])]
            missing_all = [item for item in all_tokens if item not in haystack]
            any_passed = True if not any_tokens else any(item in haystack for item in any_tokens)
            passed = not missing_all and any_passed
            requirement_passed = requirement_passed and passed
            check_record = {
                "source": source,
                "passed": passed,
                "required_all": all_tokens,
                "missing_all": missing_all,
                "required_any": any_tokens,
                "any_passed": any_passed,
            }
            checks.append(check_record)
        if not requirement_passed:
            failures.append(rid)
        results.append({
            "id": rid,
            "profile": requirement.get("profile", "H0"),
            "description": requirement.get("description", ""),
            "passed": requirement_passed,
            "checks": checks,
        })

    h0 = [r for r in results if r["profile"] == "H0"]
    h1 = [r for r in results if r["profile"] == "H1"]
    payload = {
        "schema": "sentinel-edge.uix-conformance.v1",
        "contract_version": contract.get("version"),
        "contract_path": CONTRACT.relative_to(ROOT).as_posix(),
        "contract_sha256": sha256(CONTRACT),
        "source_digest": hashlib.sha256("".join(sorted(record["sha256"] for record in source_records.values())).encode("ascii")).hexdigest(),
        "source_files": source_records,
        "design_basis": design_basis,
        "summary": {
            "overall_status": "pass" if not failures else "fail",
            "requirement_count": len(results),
            "passed_count": sum(1 for item in results if item["passed"]),
            "failed_count": len(failures),
            "h0_count": len(h0),
            "h0_passed": sum(1 for r in h0 if r["passed"]),
            "h1_count": len(h1),
            "h1_passed": sum(1 for r in h1 if r["passed"]),
            "failed_ids": failures,
        },
        "requirements": results,
        "truth_boundary": {
            "reference_mockups_are_runtime_evidence": False,
            "emulated_arm64_disclosure_required": True,
            "research_mvp_warning_required": True,
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
