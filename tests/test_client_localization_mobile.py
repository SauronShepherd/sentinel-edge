from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_core_client_contains_english_spanish_labels_and_phone_layout() -> None:
    client = TestClient(create_app())
    page = client.get("/client").text
    assert 'lang="es"' in page
    assert "Sesión local" in page
    assert "@media (max-width: 360px)" in page
    assert "grid-template-columns:1fr" in page
