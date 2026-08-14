"""Bind submission/presentation artifacts to one candidate evidence closure."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def build_presentation_binding(candidate: dict[str, Any], claim_registry_path: str | Path, artifact_paths: list[str | Path], *, root: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    registry = Path(claim_registry_path).resolve()
    if not registry.is_file():
        raise ValueError("claim registry is missing")
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError("candidate_id is required")
    records = []
    for raw in artifact_paths:
        path = Path(raw).resolve()
        if not path.is_file() or root_path not in path.parents:
            raise ValueError("presentation artifact must be an existing file inside root")
        records.append({"path": path.relative_to(root_path).as_posix(), "sha256": sha256_file(path)})
    registry_digest = sha256_file(registry)
    base = {"candidate_id": candidate_id, "claim_registry_sha256": registry_digest, "artifacts": sorted(records, key=lambda item: item["path"])}
    return {"schema": "sentinel-edge-presentation-binding/1.0", **base, "binding_sha256": sha256_bytes(canonical_json_bytes(base))}


def verify_presentation_binding(binding: dict[str, Any], candidate: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    failures: list[str] = []
    if binding.get("schema") != "sentinel-edge-presentation-binding/1.0":
        failures.append("binding_schema_mismatch")
    if binding.get("candidate_id") != candidate.get("candidate_id"):
        failures.append("candidate_binding_mismatch")
    base = {key: binding.get(key) for key in ("candidate_id", "claim_registry_sha256", "artifacts")}
    if binding.get("binding_sha256") != sha256_bytes(canonical_json_bytes(base)):
        failures.append("binding_digest_mismatch")
    registry = root_path / "qualification/claim-registry.json"
    if not registry.is_file() or sha256_file(registry) != binding.get("claim_registry_sha256"):
        failures.append("claim_registry_digest_mismatch")
    for item in binding.get("artifacts", []):
        path = root_path / str(item.get("path", ""))
        if not path.is_file() or sha256_file(path) != item.get("sha256"):
            failures.append(f"artifact_mismatch:{item.get('path', '')}")
    return {"valid": not failures, "candidate_id": candidate.get("candidate_id"), "failures": failures}
