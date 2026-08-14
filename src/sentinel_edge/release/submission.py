from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file

_EXCLUDED_PARTS = {
    ".git", ".idea", ".tmp", ".venv", ".uv-cache", ".pytest_cache",
    "__pycache__", ".mypy_cache", ".ruff_cache", "build", "dist", "node_modules",
}
RELEASE_GENERATED_FILES = frozenset({
    "release-candidate.json",
    "release-manifest.json",
    "release-candidate.json.sig.json",
    "qualification/submission-command-matrix.json",
    "qualification/emulated-arm64-benchmark.json",
    "qualification/claim-registry.json",
    "qualification/claim-table.md",
    "qualification/conformance-ledger.json",
    "qualification/release-acceptance-checklist.json",
    "qualification/uix-conformance.json",
    "registries/evidence.yaml",
    "docs/release/CURRENT_SUBMISSION_READINESS.md",
})
_EXCLUDED_FILES = RELEASE_GENERATED_FILES

REQUIRED_LOCAL_COMMANDS = (
    "setup",
    "doctor",
    "verify",
    "demo",
    "scenario",
    "test-all",
    "gates",
    "benchmark-replay",
    "claims",
)
REQUIRED_ARM64_COMMANDS = (
    "arm64-setup",
    "arm64-doctor",
    "arm64-test",
    "arm64-demo",
    "arm64-scenario",
    "arm64-benchmark",
)


def source_inventory(root: str | Path) -> list[dict[str, Any]]:
    root_path = Path(root).resolve()
    records: list[dict[str, Any]] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root_path)
        relative = relative_path.as_posix()
        if relative in _EXCLUDED_FILES:
            continue
        if relative.endswith(".pyc") or any(part in _EXCLUDED_PARTS or part.endswith(".egg-info") for part in relative_path.parts):
            continue
        records.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return records


def source_tree_digest(root: str | Path) -> str:
    return sha256_bytes(canonical_json_bytes(source_inventory(root)))


def verify_submission_command_matrix(root: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    path = root_path / "qualification/submission-command-matrix.json"
    if not path.is_file():
        return {"valid": False, "failures": ["submission_command_matrix_missing"], "present": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"valid": False, "failures": ["submission_command_matrix_invalid_json"], "present": True}
    failures: list[str] = []
    if payload.get("schema") != "sentinel-edge.submission-command-matrix.v1":
        failures.append("submission_command_matrix_schema_mismatch")
    if payload.get("release_profile") != "H0-EMULATED-AARCH64-20260813":
        failures.append("submission_command_matrix_profile_mismatch")
    if payload.get("source_tree_digest") != source_tree_digest(root_path):
        failures.append("submission_command_matrix_source_tree_mismatch")
    repository = payload.get("repository", {})
    if not isinstance(repository, dict) or repository.get("git_available") is not True:
        failures.append("submission_command_matrix_git_revision_unavailable")
    elif repository.get("dirty") is not False or not repository.get("revision"):
        failures.append("submission_command_matrix_repository_not_clean")
    commands = payload.get("commands", {})
    if not isinstance(commands, dict):
        failures.append("submission_command_matrix_commands_invalid")
        commands = {}
    for command in (*REQUIRED_LOCAL_COMMANDS, *REQUIRED_ARM64_COMMANDS):
        record = commands.get(command)
        if not isinstance(record, dict):
            failures.append(f"submission_command_missing:{command}")
            continue
        if record.get("status") != "pass" or int(record.get("exit_code", 1)) != 0:
            failures.append(f"submission_command_not_passed:{command}")
    if payload.get("overall_status") != "pass":
        failures.append("submission_command_matrix_not_green")
    return {
        "valid": not failures,
        "present": True,
        "failures": failures,
        "sha256": sha256_file(path),
        "payload": payload,
    }
