from sentinel_edge.gateway.api import _CLIENT_HTML, _CLIENT_JS
from sentinel_edge.qualification.accessibility import audit_core_ui_accessibility


def test_core_ui_accessibility_contract_passes() -> None:
    result = audit_core_ui_accessibility(_CLIENT_HTML, _CLIENT_JS)
    assert result.passed is True
    assert result.failures == ()


def test_accessibility_audit_detects_missing_equivalents() -> None:
    result = audit_core_ui_accessibility("<main></main>", "")
    assert result.passed is False
    assert "tabular_equivalent" in result.failures
