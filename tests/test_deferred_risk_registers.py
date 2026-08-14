from pathlib import Path

from scripts.validate_deferred_risk_registers import validate


ROOT = Path(__file__).resolve().parents[1]


def test_deferred_and_residual_registers_are_generated_and_complete() -> None:
    result = validate(ROOT)
    assert result == {"valid": True, "deferred_debt": 4, "residual_risks": 17, "failures": []}
