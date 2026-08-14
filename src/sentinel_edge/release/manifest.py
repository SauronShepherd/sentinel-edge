from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sentinel_edge.security import sha256_file
from sentinel_edge.security import canonical_json_bytes, sha256_bytes


EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache"}


def build_manifest(root: str | Path) -> dict:
    root = Path(root).resolve()
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "release-manifest.json":
            continue
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        "schema": "sentinel-edge-release-manifest/1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def write_manifest(root: str | Path, output: str | Path | None = None) -> Path:
    root = Path(root).resolve()
    output_path = Path(output) if output else root / "release-manifest.json"
    output_path.write_text(json.dumps(build_manifest(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def build_release_candidate_manifest(root: str | Path, candidate_path: str | Path) -> dict:
    """Build a deterministic manifest that binds the candidate and its complete file inventory."""
    root_path = Path(root).resolve()
    candidate = Path(candidate_path).resolve()
    if candidate.parent != root_path and root_path not in candidate.parents:
        raise ValueError("candidate must be inside the release root")
    manifest = build_manifest(root_path)
    candidate_record = next((item for item in manifest["files"] if item["path"] == candidate.relative_to(root_path).as_posix()), None)
    if candidate_record is None:
        raise ValueError("candidate is not present in manifest inventory")
    payload = {
        "schema": "sentinel-edge-release-candidate-manifest/1.0",
        "candidate_path": candidate.relative_to(root_path).as_posix(),
        "candidate_sha256": candidate_record["sha256"],
        "inventory_sha256": sha256_bytes(canonical_json_bytes(manifest["files"])),
        "manifest": manifest,
    }
    return payload
