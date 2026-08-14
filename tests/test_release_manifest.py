from pathlib import Path
from sentinel_edge.release import build_manifest


def test_release_manifest_is_sorted_and_excludes_itself(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    manifest = build_manifest(tmp_path)
    assert [item["path"] for item in manifest["files"]] == ["a.txt", "b.txt"]
