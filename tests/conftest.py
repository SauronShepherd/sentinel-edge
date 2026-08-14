import pytest


@pytest.fixture
def viewer_headers() -> dict[str, str]:
    return {"Authorization": "Bearer sentinel-dev-viewer-token"}


@pytest.fixture
def operator_headers() -> dict[str, str]:
    return {"Authorization": "Bearer sentinel-dev-operator-token"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer sentinel-dev-admin-token"}
