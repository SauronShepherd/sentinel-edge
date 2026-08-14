from __future__ import annotations

import json
import locale
import os
import platform
import re
import sys
from functools import lru_cache
from importlib import metadata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file

_EXCLUDED = {".git", ".idea", ".tmp", ".venv", "build", "dist", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", "node_modules"}
_GENERATED = {
    "release-candidate.json",
    "release-candidate.json.sig.json",
    "release-manifest.json",
    "build-provenance.json",
    "security-review.json",
    "THIRD_PARTY_NOTICES.md",
    "third-party-inventory.json",
    "sbom.cdx.json",
    "privacy-closure.json",
    "host-trust-report.json",
    "reproducibility-report.json",
    "release-governance-report.json",
    "independent-build-report.json",
    "network-isolation-report.json",
    "wheelhouse-report.json",
    "power-energy-report.json",
    "runtime-known-issue-report.json",
    "docs/release/CURRENT_SUBMISSION_READINESS.md",
}


@lru_cache(maxsize=8)
def _materials_cached(root_text: str) -> tuple[dict[str, Any], ...]:
    root = Path(root_text)
    materials = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in _EXCLUDED for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in _GENERATED:
            continue
        materials.append({"uri": rel, "digest": {"sha256": sha256_file(path)}, "bytes": path.stat().st_size})
    return tuple(materials)


def _materials(root: Path) -> list[dict[str, Any]]:
    return list(_materials_cached(str(root.resolve())))


def _secret_scan(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    patterns = (
        ("private_key_pem", re.compile(r"(?m)^-----BEGIN (?:OPENSSH )?PRIVATE KEY-----$")),
        ("aws_secret_assignment", re.compile(r"(?m)^(?:export\s+)?AWS_SECRET_ACCESS_KEY=\S+$")),
        ("sentinel_admin_token_assignment", re.compile(r"(?m)^(?:export\s+)?SENTINEL_EDGE_ADMIN_TOKEN=\S+$")),
    )
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in _EXCLUDED for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in _GENERATED or path.stat().st_size > 4 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for marker, pattern in patterns:
            if pattern.search(text):
                findings.append({"path": rel, "marker": marker})
    return {"passed": not findings, "findings": findings, "scope": "repository_text_files_under_4MiB"}


def build_provenance(root: str | Path, *, builder_id: str = "sentinel-edge-local-builder/v0.21.0") -> dict[str, Any]:
    root = Path(root).resolve()
    materials = _materials(root)
    source_digest = sha256_bytes(canonical_json_bytes(materials))
    source_revision = "archive-without-vcs-metadata"
    git_head = root / ".git" / "HEAD"
    if git_head.is_file():
        source_revision = git_head.read_text(encoding="utf-8").strip()
    secret_scan = _secret_scan(root)
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://slsa.dev/provenance/v1",
        "subject": [{"name": "sentinel-edge-source-tree", "digest": {"sha256": source_digest}}],
        "predicate": {
            "buildDefinition": {
                "buildType": "https://sentinel-edge.example/build-types/local-python-archive/v1",
                "externalParameters": {
                    "project_version": _project_version(root),
                    "source_revision": source_revision,
                    "build_path_policy": "relative_paths_only_for_subject_materials",
                    "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH"),
                    "dependency_lock": (
                        {"path": "requirements-release.lock.json", "sha256": sha256_file(root / "requirements-release.lock.json")}
                        if (root / "requirements-release.lock.json").is_file() else None
                    ),
                    "build_definition_digest": sha256_file(root / "pyproject.toml"),
                    "offline_wheelhouse": (
                        {"path": "wheelhouse-report.json", "sha256": sha256_file(root / "wheelhouse-report.json")}
                        if (root / "wheelhouse-report.json").is_file() else None
                    ),
                    "network_isolation": (
                        {"path": "network-isolation-report.json", "sha256": sha256_file(root / "network-isolation-report.json")}
                        if (root / "network-isolation-report.json").is_file() else None
                    ),
                    "independent_build": (
                        {"path": "independent-build-report.json", "sha256": sha256_file(root / "independent-build-report.json")}
                        if (root / "independent-build-report.json").is_file() else None
                    ),
                    "release_governance": (
                        {"path": "release-governance-report.json", "sha256": sha256_file(root / "release-governance-report.json")}
                        if (root / "release-governance-report.json").is_file() else None
                    ),
                    "power_energy": (
                        {"path": "power-energy-report.json", "sha256": sha256_file(root / "power-energy-report.json")}
                        if (root / "power-energy-report.json").is_file() else None
                    ),
                    "runtime_known_issues": (
                        {"path": "runtime-known-issue-report.json", "sha256": sha256_file(root / "runtime-known-issue-report.json")}
                        if (root / "runtime-known-issue-report.json").is_file() else None
                    ),
                },
                "internalParameters": {
                    "network_access": "dependency_install_rehearsed_no_index; source_bundle_python_guard; benchmark_namespace_probe_bound_separately",
                    "hermeticity": "not_claimed",
                    "reproducibility_class": "provenance_only",
                },
                "resolvedDependencies": materials,
            },
            "runDetails": {
                "builder": {"id": builder_id, "version": {"sentinel-edge": _project_version(root)}},
                "metadata": {
                    "invocationId": sha256_bytes(canonical_json_bytes({"subject": source_digest, "builder": builder_id})),
                    "startedOn": datetime.now(timezone.utc).isoformat(),
                    "finishedOn": datetime.now(timezone.utc).isoformat(),
                },
                "byproducts": [
                    {"name": "credential-output-scan", "content": secret_scan},
                    {
                        "name": "environment",
                        "content": {
                            "python": sys.version.split()[0],
                            "python_implementation": sys.implementation.name,
                            "platform": platform.platform(),
                            "machine": platform.machine(),
                            "locale": locale.setlocale(locale.LC_ALL, None),
                            "timezone": os.environ.get("TZ", "system-default"),
                        },
                    },
                    {
                        "name": "toolchain",
                        "content": {
                            "setuptools": _distribution_version("setuptools"),
                            "wheel": _distribution_version("wheel"),
                            "pip": _distribution_version("pip"),
                            "build_backend": "setuptools.build_meta",
                            "container_image_digest": os.environ.get("SENTINEL_BUILD_IMAGE_DIGEST"),
                        },
                    },
                ],
            },
        },
        "sentinel_edge": {
            "schema": "sentinel-edge-build-provenance/1.0",
            "alignment": "SLSA-v1-provenance-shape; no hermetic or reproducible-build claim",
            "subject_digest": source_digest,
            "secret_scan_passed": secret_scan["passed"],
        },
    }
    return statement


def _distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _project_version(root: Path) -> str:
    import tomllib

    return tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def write_provenance(root: str | Path, output: str | Path | None = None) -> Path:
    root = Path(root).resolve()
    output = Path(output) if output else root / "build-provenance.json"
    output.write_text(json.dumps(build_provenance(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_provenance(path: str | Path, root: str | Path, *, expected_builder_id: str | None = None) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    current = build_provenance(root)
    expected = current["sentinel_edge"]["subject_digest"]
    actual = payload.get("sentinel_edge", {}).get("subject_digest")
    failures = []
    if actual != expected:
        failures.append("source_subject_digest_mismatch")
    if not payload.get("sentinel_edge", {}).get("secret_scan_passed", False):
        failures.append("credential_output_scan_failed")
    builder_id = payload.get("predicate", {}).get("runDetails", {}).get("builder", {}).get("id")
    if expected_builder_id is not None and builder_id != expected_builder_id:
        failures.append("unexpected_builder_identity")
    if payload.get("predicate", {}).get("buildDefinition", {}).get("internalParameters", {}).get("hermeticity") != "not_claimed":
        failures.append("unsupported_hermeticity_claim")
    external = payload.get("predicate", {}).get("buildDefinition", {}).get("externalParameters", {})
    lock = external.get("dependency_lock")
    current_lock = Path(root) / "requirements-release.lock.json"
    if current_lock.is_file():
        if not lock or lock.get("sha256") != sha256_file(current_lock):
            failures.append("dependency_lock_not_bound")
    if not external.get("build_definition_digest"):
        failures.append("build_definition_not_bound")
    for report_name in ("offline_wheelhouse", "network_isolation", "independent_build", "release_governance", "power_energy", "runtime_known_issues"):
        bound = external.get(report_name)
        if bound:
            report_path = Path(root) / bound.get("path", "")
            if not report_path.is_file() or bound.get("sha256") != sha256_file(report_path):
                failures.append(f"{report_name}_not_bound")
    return {"valid": not failures, "subject_digest": actual, "builder_id": builder_id, "failures": failures}
