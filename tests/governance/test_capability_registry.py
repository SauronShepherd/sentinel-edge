
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("capability_validator", ROOT / "scripts/validate_capability_status.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_registry_is_valid() -> None:
    data = module.load_json(ROOT / "provenance/capability-status.yaml")
    assert module.validate_registry(data) == []


def test_active_capability_without_test_is_rejected() -> None:
    data = module.load_json(ROOT / "provenance/capability-status.yaml")
    mutated = copy.deepcopy(data)
    mutated["capabilities"][0]["acceptance_tests"] = []
    assert any("lacks acceptance tests" in error for error in module.validate_registry(mutated))


def test_direct_planned_to_demonstrated_is_illegal() -> None:
    assert not module.legal_transition("planned", "demonstrated", evidence_current=True)


def test_active_to_demonstrated_requires_current_evidence() -> None:
    assert not module.legal_transition("active", "demonstrated", evidence_current=False)
    assert module.legal_transition("active", "demonstrated", evidence_current=True)
