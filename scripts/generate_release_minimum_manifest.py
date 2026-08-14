"""Generate the authoritative H0 release-minimum manifest.

The manifest is deliberately descriptive: it never upgrades a registry status
or invents evidence. Missing closure fields remain visible so a release gate
can fail closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


def generate(root: Path) -> dict:
    requirements = yaml.safe_load((root / "registries/requirements.yaml").read_text(encoding="utf-8"))["items"]
    tasks = yaml.safe_load((root / "registries/tasks.yaml").read_text(encoding="utf-8"))["items"]
    tests = yaml.safe_load((root / "registries/tests.yaml").read_text(encoding="utf-8"))["items"]
    task_by_requirement: dict[str, list[dict]] = {}
    for task in tasks:
        for scope in task.get("criterion_scopes", []):
            task_by_requirement.setdefault(scope["requirement_id"], []).append(task)
    test_by_requirement: dict[str, list[dict]] = {}
    for test in tests:
        for scope in test.get("covers", []):
            test_by_requirement.setdefault(scope["requirement_id"], []).append(test)
    h0 = [item for item in requirements if "profile H0" in item.get("statement", "")]
    rows = []
    for item in h0:
        requirement_id = item["id"]
        linked_tasks = task_by_requirement.get(requirement_id, [])
        linked_tests = test_by_requirement.get(requirement_id, [])
        task_ids = sorted({task["id"] for task in linked_tasks})
        test_ids = sorted({test["id"] for test in linked_tests})
        gate_ids = sorted({test["level"].lower() for test in linked_tests if test.get("level")})
        rows.append({
            "requirement_id": requirement_id,
            "statement": item["statement"],
            "owner": item.get("owner"),
            "slice": sorted({task.get("iteration_id") for task in linked_tasks if task.get("iteration_id")} ),
            "status": item.get("status"),
            "implementation": item.get("implementation", item.get("implementation_refs", task_ids)),
            "tests": item.get("verification_test_ids", item.get("test_ids", test_ids)),
            "gates": item.get("gate_ids", item.get("gates", gate_ids)),
            "evidence": item.get("verification_evidence_ids", item.get("evidence_ids", [])),
            "completion_execution_id": item.get("completion_execution_id"),
            "closure_complete": item.get("status") in {"IMPLEMENTED", "VERIFIED"},
        })
    mapping_failures = [
        row["requirement_id"]
        for row in rows
        if not row["owner"] or not row["implementation"] or not row["tests"] or not row["gates"]
    ]
    open_rows = sorted(
        (row for row in rows if not row["closure_complete"]),
        key=lambda row: (row["owner"] or "", row["requirement_id"]),
    )
    critical_path = [
        {
            "requirement_id": row["requirement_id"],
            "owner": row["owner"],
            "slice": row["slice"],
            "gates": row["gates"],
            "implementation": row["implementation"],
            "tests": row["tests"],
            "evidence": row["evidence"],
            "status": row["status"],
        }
        for row in open_rows
    ]
    emulated_profile = (root / "config/arm64-emulation.yaml").is_file()
    release_admitted = bool(emulated_profile and not critical_path)
    return {
        "schema": "sentinel-edge-release-minimum-manifest/1.0",
        "contract_version": "0.22.0",
        "profile": "H0",
        "requirement_registry_sha256": hashlib.sha256(
            (root / "registries/requirements.yaml").read_bytes()
        ).hexdigest(),
        "requirement_count": len(rows),
        "closed_count": sum(row["closure_complete"] for row in rows),
        "open_count": sum(not row["closure_complete"] for row in rows),
        "release_profile": "H0-EMULATED-AARCH64-20260813" if emulated_profile else "physical-target",
        "release_admitted": release_admitted,
        "critical_path": {
            "status": "open" if critical_path else "complete",
            "open_requirement_ids": [item["requirement_id"] for item in critical_path],
            "items": critical_path,
        },
        "automatic_cut": {
            "status": "cut" if critical_path else "clear",
            "release_admitted": release_admitted,
            "reason_codes": (["open_h0_requirements"] if critical_path else []),
            "open_count": len(critical_path),
        },
        "mapping_failures": mapping_failures,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "qualification" / "release-minimum-manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = generate(root)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: manifest[key] for key in ("requirement_count", "closed_count", "open_count", "release_admitted")}, sort_keys=True))
    return 0 if manifest["requirement_count"] == 240 and not manifest["mapping_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
