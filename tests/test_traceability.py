from __future__ import annotations

from pathlib import Path

from scripts.validate_traceability import validate


ROOT = Path(__file__).resolve().parents[1]


def test_authoritative_traceability_is_complete() -> None:
    result = validate(ROOT)
    assert result == {"valid": True, "requirement_count": 743, "h0_count": 240, "failures": []}
