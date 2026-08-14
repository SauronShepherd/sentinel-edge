from __future__ import annotations

import json
import hashlib
from pathlib import Path
import yaml

from scripts import audit_baseline


def test_inventory_excludes_the_receipt_that_it_rewrites() -> None:
    assert "provenance/evidence/remediation/R00/baseline-receipt.json" not in audit_baseline.inventory()


def test_registry_counts_parse_authoritative_items() -> None:
    counts = audit_baseline.registry_counts()
    assert counts["requirements.yaml"] == 743
    assert counts["decisions.yaml"] == 193
    assert counts["evidence.yaml"] == 350
    assert counts["tasks.yaml"] == 96
    # The active v0.22 registry has grown as the H0 closure and emulated-Arm64
    # lanes were made executable.  Keep this assertion tied to the current
    # authoritative registry rather than the older pre-closure baseline.
    assert counts["tests.yaml"] == 400


def test_generated_receipt_is_json_and_has_truthful_policy() -> None:
    receipt = audit_baseline.build_receipt()
    assert receipt["status_policy"] == {
        "verified_requires_receipt": True,
        "fixture_evidence_is_non_target": True,
    }
    json.dumps(receipt)


def test_registered_governance_receipt_has_matching_digest() -> None:
    registry = yaml.safe_load((audit_baseline.ROOT / "registries/evidence.yaml").read_text(encoding="utf-8"))
    record = next(item for item in registry["items"] if item["id"] == "EV-R00-GOVERNANCE-RECEIPT-20260812")
    path = audit_baseline.ROOT / record["path"]
    assert path.is_file()
    assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
