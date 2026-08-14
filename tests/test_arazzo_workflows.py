from pathlib import Path

import pytest

from sentinel_edge.workflows.arazzo import validate_workflow


ROOT = Path(__file__).parents[1]
ALLOWED = {"./openapi.yaml"}


@pytest.mark.parametrize("name", ["upload-review.arazzo.yaml", "cursor-resync.arazzo.yaml"])
def test_selected_workflows_are_pinned_and_offline(name: str) -> None:
    document = validate_workflow(ROOT / "fixtures" / "workflows" / name, allowed_openapi=ALLOWED)
    assert document["arazzo"] == "1.1.0"
    assert set(document["workflows"][0]["x-proof-paths"]) == {"retry", "idempotency", "optimistic-conflict", "rest-resync"}


def test_external_reference_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text((ROOT / "fixtures/workflows/upload-review.arazzo.yaml").read_text().replace("./openapi.yaml", "https://example.invalid/openapi.yaml"), encoding="utf-8")
    with pytest.raises(ValueError, match="unallowlisted"):
        validate_workflow(path, allowed_openapi=ALLOWED)
