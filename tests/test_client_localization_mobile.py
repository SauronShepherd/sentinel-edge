from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_core_client_contains_english_spanish_labels_and_phone_layout() -> None:
    client = TestClient(create_app())
    page = client.get("/client").text
    css = client.get("/client/styles.css").text
    assert 'lang="en"' in page
    assert 'lang="es"' in page
    assert "Sesión local" in page
    assert "@media(max-width:360px)" in css
    assert "grid-template-columns:1fr" in css
    assert "prefers-reduced-motion" in css
