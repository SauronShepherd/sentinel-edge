"""Validate the generated twelve-pack G0 status artifact."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from .generate_g0_gate_status import generate
except ImportError:  # direct script execution
    from generate_g0_gate_status import generate


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "qualification/g0-gate-status.json"
ALLOWED_STATUSES = {"pass", "pass_with_declared_limitation", "fail", "not_applicable"}


def main() -> int:
    if not OUTPUT.is_file():
        print("g0_gate_status: artifact missing")
        return 1
    actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
    expected = generate(ROOT)
    if actual != expected:
        print("g0_gate_status: projection drift")
        return 1
    ids = [item["id"] for item in actual["packs"]]
    expected_ids = [f"G0-{index:02d}" for index in range(1, 13)]
    if ids != expected_ids:
        print(f"g0_gate_status: invalid pack IDs: {ids}")
        return 1
    if any(item["status"] not in ALLOWED_STATUSES for item in actual["packs"]):
        print("g0_gate_status: invalid contract status vocabulary")
        return 1
    try:
        manifest = json.loads((ROOT / "qualification/release-minimum-manifest.json").read_text(encoding="utf-8"))
        expected_requirements = {row["requirement_id"] for row in manifest["rows"]}
        mapped_requirements = {requirement_id for pack in actual["packs"] for requirement_id in pack.get("requirements", [])}
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        print("g0_gate_status: release manifest missing or invalid")
        return 1
    if mapped_requirements != expected_requirements:
        print({"g0_gate_status": "requirement_mapping_mismatch", "missing": sorted(expected_requirements - mapped_requirements), "extra": sorted(mapped_requirements - expected_requirements)})
        return 1
    if any(not pack.get("tests") or not pack.get("artifacts") for pack in actual["packs"]):
        print("g0_gate_status: pack evidence mapping incomplete")
        return 1
    if actual["release_admitted"] and any(item["status"] not in {"pass", "pass_with_declared_limitation"} for item in actual["packs"]):
        print("g0_gate_status: admitted release has non-passing pack")
        return 1
    print({"valid": True, "packs": len(ids), "status": actual["summary"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
