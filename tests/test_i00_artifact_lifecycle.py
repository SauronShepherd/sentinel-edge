from __future__ import annotations

from pathlib import Path

from sentinel_edge.storage import ContentAddressedArtifactStore


def test_artifact_store_close_is_explicit_and_idempotent(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    store.close()
    store.close()
