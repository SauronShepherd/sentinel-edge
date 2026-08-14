from pathlib import Path


API_SOURCE = Path(__file__).parents[1] / "src" / "sentinel_edge" / "gateway" / "api.py"


def test_gateway_public_problem_details_do_not_serialize_exception_text() -> None:
    source = API_SOURCE.read_text(encoding="utf-8")

    assert '"message": str(exc)' not in source
    assert "'message': str(exc)" not in source
    assert '"detail": str(exc)' not in source
    assert "'detail': str(exc)" not in source


def test_gateway_safe_message_is_constant_and_non_diagnostic() -> None:
    source = API_SOURCE.read_text(encoding="utf-8")

    assert 'def _safe_public_message() -> str:' in source
    assert 'return "request could not be processed"' in source
