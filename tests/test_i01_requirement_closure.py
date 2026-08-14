from __future__ import annotations

import subprocess
import sys
import hashlib
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_requirement_closure_passes_without_unsubstantiated_verified_claims() -> None:
    result = subprocess.run([sys.executable, "scripts/validate_requirement_closure.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_requirement_closure_rejects_verified_claim_without_receipt(tmp_path: Path) -> None:
    copied = tmp_path / "repo"
    copied.mkdir()
    (copied / "registries").mkdir()
    for name in ("requirements.yaml", "evidence.yaml"):
        (copied / "registries" / name).write_text((ROOT / "registries" / name).read_text(encoding="utf-8"), encoding="utf-8")
    requirements = (copied / "registries/requirements.yaml").read_text(encoding="utf-8").replace("status: CONFIRMED", "status: VERIFIED", 1)
    (copied / "registries/requirements.yaml").write_text(requirements, encoding="utf-8")
    result = subprocess.run([sys.executable, "scripts/validate_requirement_closure.py", "--root", str(copied)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 1
    assert "verified_missing_receipt_fields" in result.stdout


def test_requirement_closure_rejects_inactive_receipt(tmp_path: Path) -> None:
    copied = tmp_path / "repo"
    copied.mkdir()
    (copied / "registries").mkdir()
    for name in ("requirements.yaml", "evidence.yaml"):
        (copied / "registries" / name).write_text((ROOT / "registries" / name).read_text(encoding="utf-8"), encoding="utf-8")

    requirements_path = copied / "registries/requirements.yaml"
    requirements_payload = yaml.safe_load(requirements_path.read_text(encoding="utf-8"))
    selected = next(item for item in requirements_payload["items"] if item.get("status") == "CONFIRMED")
    selected["status"] = "VERIFIED"
    selected["source_evidence_ids"] = ["EV-R00-FULL-SUITE-R04-20260812"]
    selected["verification_evidence_ids"] = ["EV-R00-FULL-SUITE-R04-20260812"]
    selected["verification_test_ids"] = ["TEST-001"]
    selected["completion_execution_id"] = "EXEC-TEST"
    requirements_path.write_text(yaml.safe_dump(requirements_payload, sort_keys=False), encoding="utf-8")

    receipt = copied / "receipt.json"
    receipt.write_text('{"receipt": true}\n', encoding="utf-8")
    evidence_path = copied / "registries/evidence.yaml"
    evidence_payload = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    evidence = next(item for item in evidence_payload["items"] if item.get("id") == "EV-R00-FULL-SUITE-R04-20260812")
    evidence["path"] = "receipt.json"
    evidence["sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
    evidence["status"] = "RETIRED"
    evidence_path.write_text(yaml.safe_dump(evidence_payload, sort_keys=False), encoding="utf-8")

    result = subprocess.run([sys.executable, "scripts/validate_requirement_closure.py", "--root", str(copied)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 1
    assert "verified_evidence_not_active" in result.stdout
