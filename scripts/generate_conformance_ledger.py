"""Generate deterministic conformance and acceptance projections.

The projections expose registry truth and evidence availability. They do not
upgrade requirement status and do not treat development or fixture evidence as
target qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_items(root: Path, name: str) -> list[dict]:
    payload = yaml.safe_load((root / "registries" / name).read_text(encoding="utf-8")) or {}
    return payload.get("items", [])


def profile(statement: str) -> str:
    return "H0" if "profile H0" in statement else "H1" if "profile H1" in statement else "UNPROFILED"


def generate(root: Path) -> tuple[dict, dict]:
    requirements = load_items(root, "requirements.yaml")
    tasks = load_items(root, "tasks.yaml")
    tests = load_items(root, "tests.yaml")
    evidence = load_items(root, "evidence.yaml")
    evidence_by_id = {item.get("id"): item for item in evidence}
    task_map: dict[str, list[str]] = {}
    for task in tasks:
        for scope in task.get("criterion_scopes", []):
            task_map.setdefault(scope.get("requirement_id"), []).append(task["id"])
    test_map: dict[str, list[str]] = {}
    for test in tests:
        for scope in test.get("covers", []):
            test_map.setdefault(scope.get("requirement_id"), []).append(test["id"])
    rows: list[dict] = []
    for requirement in requirements:
        requirement_id = requirement["id"]
        status = requirement.get("status", "OPEN")
        evidence_ids = sorted(requirement.get("verification_evidence_ids") or [])
        available = sorted(
            evidence_id for evidence_id in evidence_ids
            if evidence_id in evidence_by_id and (root / evidence_by_id[evidence_id].get("path", "")).is_file()
        )
        artifact_refs = [
            {
                "evidence_id": evidence_id,
                "path": evidence_by_id[evidence_id].get("path"),
                "available": evidence_id in available,
            }
            for evidence_id in evidence_ids
            if evidence_id in evidence_by_id
        ]
        deferral_reason = None
        if status != "VERIFIED":
            deferral_reason = "requirement_status_not_verified"
        elif not available:
            deferral_reason = "target_evidence_unavailable"
        rows.append({
            "requirement_id": requirement_id,
            "profile": profile(requirement.get("statement", "")),
            "priority": requirement.get("priority"),
            "status": status,
            "owner": requirement.get("owner"),
            "statement": requirement.get("statement"),
            "implementation_task_ids": sorted(set(task_map.get(requirement_id, []))),
            "verification_test_ids": sorted(set(test_map.get(requirement_id, []))),
            "verification_evidence_ids": evidence_ids,
            "registered_evidence_available": available,
            "artifact_refs": artifact_refs,
            "deferral_reason": deferral_reason,
            "target_evidence_backed": status == "VERIFIED" and bool(available),
        })
    source_files = [
        "registries/requirements.yaml", "registries/tasks.yaml", "registries/tests.yaml", "registries/evidence.yaml",
        "docs/contracts/sentinel-edge-full-scope-product-contract-v0.22.0.md",
        "docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md",
    ]
    source_digests = {path: file_digest(root / path) for path in source_files}
    h0 = [row for row in rows if row["profile"] == "H0"]
    emulated_profile = (root / "config/arm64-emulation.yaml").is_file()
    h0_implementation_complete = all(row["status"] in {"IMPLEMENTED", "VERIFIED"} for row in h0)
    profile_ready = bool(emulated_profile and h0_implementation_complete)
    ledger = {
        "schema": "sentinel-edge.conformance-ledger.v1",
        "source_digests": source_digests,
        "requirement_count": len(rows),
        "profile_counts": {key: sum(row["profile"] == key for row in rows) for key in ("H0", "H1", "UNPROFILED")},
        "status_counts": {key: sum(row["status"] == key for row in rows) for key in sorted({row["status"] for row in rows})},
        "release_profile": "H0-EMULATED-AARCH64-20260813" if emulated_profile else "physical-target",
        "release_admitted": profile_ready,
        "target_evidence_backed_count": sum(row["target_evidence_backed"] for row in rows),
        "rows": rows,
    }
    checklist = {
        "schema": "sentinel-edge.release-acceptance-checklist.v1",
        "source_ledger_sha256": hashlib.sha256(
            (json.dumps(ledger, sort_keys=True, separators=(",", ":"))).encode()
        ).hexdigest(),
        "release_profile": "H0-EMULATED-AARCH64-20260813" if emulated_profile else "physical-target",
        "release_admitted": profile_ready,
        "target_evidence_required": not emulated_profile,
        "fixture_evidence_is_non_target": True,
        "items": [
            {
                "requirement_id": row["requirement_id"],
                "profile": row["profile"],
                "required_for_release": row["profile"] == "H0",
                "status": row["status"],
                "implementation_complete": row["status"] in {"IMPLEMENTED", "VERIFIED"},
                "target_evidence_backed": row["target_evidence_backed"],
                "release_ready": profile_ready and row["status"] in {"IMPLEMENTED", "VERIFIED"},
            }
            for row in h0
        ],
    }
    checklist["summary"] = {
        "required_count": len(h0),
        "implementation_complete_count": sum(item["implementation_complete"] for item in checklist["items"]),
        "target_evidence_backed_count": sum(item["target_evidence_backed"] for item in checklist["items"]),
        "release_ready_count": sum(item["release_ready"] for item in checklist["items"]),
        "open_count": sum(not item["release_ready"] for item in checklist["items"]),
    }
    return ledger, checklist


def write(root: Path, ledger: dict, checklist: dict) -> None:
    output_dir = root / "qualification"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "conformance-ledger.json").write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "release-acceptance-checklist.json").write_text(json.dumps(checklist, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    ledger, checklist = generate(args.root.resolve())
    write(args.root.resolve(), ledger, checklist)
    print(json.dumps({"requirement_count": ledger["requirement_count"], "h0_required": checklist["summary"]["required_count"], "release_ready": checklist["summary"]["release_ready_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
