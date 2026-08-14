from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file

_PRIVATE_KEY = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |ED25519 )?PRIVATE KEY-----")
_CREDENTIAL_ASSIGNMENT = re.compile(
    rb"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_./+\-=]{16,}[\"']",
    re.IGNORECASE,
)
_EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "tests"}


def scan_repository_for_private_material(root: str | Path) -> tuple[dict[str, str], ...]:
    root_path = Path(root).resolve()
    findings: list[dict[str, str]] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file() or any(part in _EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.parts):
            continue
        if path.suffix in {".pyc", ".zip"}:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        relative = path.relative_to(root_path).as_posix()
        if _PRIVATE_KEY.search(data):
            findings.append({"path": relative, "category": "private_signing_key"})
        if _CREDENTIAL_ASSIGNMENT.search(data):
            findings.append({"path": relative, "category": "credential_assignment"})
    return tuple(findings)


def _disposition_summary(engine: Any) -> dict[str, Any]:
    requests = engine.disposition.requests()
    statuses = Counter(item.status.value for item in requests)
    unresolved_states = {"restricted", "in_progress", "external_recipient_pending", "failed"}
    unresolved = [str(item.request_id) for item in requests if item.status.value in unresolved_states]
    explicit_exceptions = [
        str(item.request_id)
        for item in requests
        if item.status.value == "retained_exception" and item.legal_exception_reason
    ]
    return {
        "request_count": len(requests),
        "by_status": dict(sorted(statuses.items())),
        "unresolved_request_ids": sorted(unresolved),
        "explicit_retained_exception_ids": sorted(explicit_exceptions),
    }


def _secret_summary(engine: Any) -> dict[str, Any]:
    metadata = engine.secrets.metadata()
    states = Counter(item.state.value for item in metadata)
    live_states = {"active", "overlap", "staged"}
    live = [f"{item.reference_id}@{item.version}" for item in metadata if item.state.value in live_states]
    return {
        "reference_count": len(metadata),
        "by_state": dict(sorted(states.items())),
        "live_reference_keys": sorted(live),
        "secret_values_persisted": False,
        "metadata_database_sha256": sha256_file(engine.secrets.path) if engine.secrets.path != ":memory:" and Path(engine.secrets.path).is_file() else None,
    }


def _protected_state_summary(engine: Any) -> dict[str, Any]:
    metrics = engine.protected_state.metrics()
    grants = engine.protected_state.grants()
    active = [str(item.grant_id) for item in grants if item.state.value == "active"]
    return {
        "grant_count": len(grants),
        "active_grant_ids": sorted(active),
        "protected_cache_entries": int(metrics["protected_cache_entries"]),
        "queued_authority_items": int(metrics["queued_authority_items"]),
        "values_encrypted_at_rest": bool(metrics["values_encrypted_at_rest"]),
        "release_eligible": bool(metrics["release_eligible"]),
        "limitation": metrics["limitation"],
    }


def build_privacy_closure(engine: Any, *, repository_root: str | Path, generated_at: datetime | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc)
    records = engine.artifacts.catalog.records()
    classifications = Counter(item.policy.classification.value for item in records)
    unclassified = [str(item.registration_id) for item in records if not item.policy.classification.value]
    secret_prohibited = [
        str(item.registration_id) for item in records if item.policy.classification.value == "secret_prohibited"
    ]
    disposition = _disposition_summary(engine)
    secrets = _secret_summary(engine)
    protected_state = _protected_state_summary(engine)
    repository_findings = list(scan_repository_for_private_material(repository_root))
    base = {
        "schema": "sentinel-edge-privacy-closure/1.0",
        "generated_at": generated_at.isoformat(),
        "artifact_catalog": {
            "registration_count": len(records),
            "by_classification": dict(sorted(classifications.items())),
            "unclassified_registration_ids": sorted(unclassified),
            "secret_prohibited_registration_ids": sorted(secret_prohibited),
            "usage": engine.artifacts.catalog.usage(),
        },
        "disposition": disposition,
        "secrets": secrets,
        "protected_local_state": protected_state,
        "repository_private_material_findings": repository_findings,
        "claims": {
            "all_content_addressed_artifact_writes_require_explicit_policy": True,
            "disposition_lineage_is_registration_based": True,
            "external_recipient_deletion_requires_receipt": True,
            "secret_values_are_process_memory_only": True,
            "independent_privacy_review_complete": False,
        },
    }
    failures: list[str] = []
    if unclassified:
        failures.append("unclassified_artifact_registrations")
    if secret_prohibited:
        failures.append("secret_prohibited_artifact_persisted")
    if disposition["unresolved_request_ids"]:
        failures.append("unresolved_disposition_requests")
    if secrets["secret_values_persisted"]:
        failures.append("secret_values_persisted")
    if secrets["live_reference_keys"]:
        failures.append("live_secret_references_present_in_candidate_state")
    if protected_state["active_grant_ids"]:
        failures.append("active_protected_local_grants_present")
    if protected_state["protected_cache_entries"]:
        failures.append("protected_cache_entries_present")
    if protected_state["queued_authority_items"]:
        failures.append("queued_protected_authority_present")
    if repository_findings:
        failures.append("repository_private_material_detected")
    base["privacy_state_complete"] = not failures
    base["release_eligible"] = not failures
    base["failures"] = sorted(failures)
    base["limitations"] = [
        "lineage closure covers registered descendants and declared external recipients only",
        "secure erasure from flash remanence, filesystem journals, backups and controllers is not claimed",
        "protected local state lacks an approved at-rest encryption profile and must be empty at candidate freeze",
        "independent privacy assessment is not complete",
    ]
    base["report_sha256"] = sha256_bytes(canonical_json_bytes(base))
    return base


def verify_privacy_closure(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    claimed = payload.pop("report_sha256", None)
    observed = sha256_bytes(canonical_json_bytes(payload))
    failures: list[str] = []
    if claimed != observed:
        failures.append("privacy_closure_digest_mismatch")
    if payload.get("schema") != "sentinel-edge-privacy-closure/1.0":
        failures.append("privacy_closure_schema_unsupported")
    return {
        "valid": not failures,
        "privacy_state_complete": payload.get("privacy_state_complete") is True,
        "release_eligible": payload.get("release_eligible") is True,
        "failures": failures,
        "report_sha256": claimed,
    }


def write_privacy_closure(
    engine: Any,
    *,
    repository_root: str | Path,
    output: str | Path,
    generated_at: datetime | None = None,
) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_privacy_closure(engine, repository_root=repository_root, generated_at=generated_at)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
