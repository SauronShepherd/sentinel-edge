from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_conformance_ledger import generate


ROOT = Path(__file__).resolve().parents[1]


def test_conformance_ledger_and_checklist_preserve_claim_ceiling() -> None:
    ledger, checklist = generate(ROOT)
    assert ledger["requirement_count"] == 743
    assert ledger["profile_counts"]["H0"] == 240
    assert ledger["target_evidence_backed_count"] == 0
    cnf = next(row for row in ledger["rows"] if row["requirement_id"] == "REQ-CNF-001")
    assert cnf["artifact_refs"] == []
    assert cnf["deferral_reason"] == "requirement_status_not_verified"
    assert checklist["release_admitted"] is True
    assert checklist["release_profile"] == "H0-EMULATED-AARCH64-20260813"
    assert checklist["summary"] == {
        "required_count": 240,
            "implementation_complete_count": 240,
        "target_evidence_backed_count": 0,
        "release_ready_count": 240,
        "open_count": 0,
    }


def test_conformance_projection_is_deterministic() -> None:
    first = generate(ROOT)
    second = generate(ROOT)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_target_backing_requires_a_locally_available_receipt() -> None:
    ledger, _ = generate(ROOT)
    assert ledger["target_evidence_backed_count"] == 0
    assert all(not row["target_evidence_backed"] for row in ledger["rows"])
