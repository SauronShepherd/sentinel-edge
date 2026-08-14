from __future__ import annotations

from pathlib import Path

from scripts.validate_contract_profile import PRODUCT_ROW, profiles, validate


ROOT = Path(__file__).resolve().parents[1]


def test_contract_profile_registry_is_synchronized() -> None:
    result = validate(ROOT)
    assert result["valid"] is True
    assert result["product_profile_count"] > 0
    assert result["technical_profile_count"] > 0


def test_profile_mutation_has_stable_failure_reason() -> None:
    text = "| FR-TEST-001 | MUST | `H0` | Example |\n"
    assert profiles(text, PRODUCT_ROW) == {"FR-TEST-001": "H0"}
