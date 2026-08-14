import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "qualification/uix-conformance.json"


def test_generated_uix_conformance_is_fail_closed_and_green():
    proc = subprocess.run(
        [sys.executable, "scripts/generate_uix_conformance.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert payload["schema"] == "sentinel-edge.uix-conformance.v1"
    summary = payload["summary"]
    assert summary["overall_status"] == "pass"
    assert summary["failed_count"] == 0
    assert summary["h0_passed"] == summary["h0_count"]
    assert summary["requirement_count"] >= 20
    assert payload["design_basis"]["valid"] is True
    assert payload["design_basis"]["reference_mockup_count"] == 10
    assert payload["design_basis"]["specification"]["sha256"]
    assert all(item["sha256"] for item in payload["design_basis"]["reference_mockups"])


def test_uix_contract_covers_all_ten_reference_screen_families_and_truth_boundary():
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    ids = {row["id"] for row in payload["requirements"]}
    required = {
        "UIX-SCREEN-OVERVIEW",
        "UIX-SCREEN-SITES",
        "UIX-SCREEN-DEVICES",
        "UIX-SCREEN-INCIDENTS",
        "UIX-SCREEN-AI-INVESTIGATION",
        "UIX-SCREEN-POLICIES",
        "UIX-SCREEN-REPORTS",
        "UIX-SCREEN-PROVISIONING",
        "UIX-SCREEN-FIRMWARE",
        "UIX-SCREEN-AUTOMATION",
    }
    assert required <= ids
    assert payload["truth_boundary"]["reference_mockups_are_runtime_evidence"] is False
    assert payload["truth_boundary"]["emulated_arm64_disclosure_required"] is True
    assert payload["truth_boundary"]["research_mvp_warning_required"] is True
