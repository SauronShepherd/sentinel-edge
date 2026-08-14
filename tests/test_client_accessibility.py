from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_core_client_exposes_keyboard_controls_and_textual_severity() -> None:
    client = TestClient(create_app())
    page = client.get("/client").text
    script = client.get("/client/app.js").text
    assert 'type="button"' in page
    assert 'tabindex="-1"' in page
    assert '<strong>Severity:</strong>' in script
    assert 'aria-live="polite"' in page
