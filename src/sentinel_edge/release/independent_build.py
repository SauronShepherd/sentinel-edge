from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.update import key_id


def build_attestation(
    *,
    builder_id: str,
    host_fingerprint: str,
    environment_digest: str,
    source_digest: str,
    artifact_digest: str,
    private_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    body = {
        "schema": "sentinel-edge-independent-build-attestation/1.0",
        "builder_id": builder_id,
        "host_fingerprint": host_fingerprint,
        "environment_digest": environment_digest,
        "source_digest": source_digest,
        "artifact_digest": artifact_digest,
        "signer_key_id": key_id(private_key.public_key()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    signature = private_key.sign(canonical_json_bytes(body))
    return {**body, "signature": base64.b64encode(signature).decode("ascii")}


def verify_attestation(
    attestation: dict[str, Any],
    public_key: Ed25519PublicKey,
    *,
    expected_builder_id: str | None = None,
    expected_policy_version: str | None = None,
) -> list[str]:
    failures: list[str] = []
    if attestation.get("schema") != "sentinel-edge-independent-build-attestation/1.0":
        failures.append("unsupported_build_attestation_schema")
    if attestation.get("signer_key_id") != key_id(public_key):
        failures.append("build_attestation_signer_mismatch")
    if expected_builder_id is not None and attestation.get("builder_id") != expected_builder_id:
        failures.append("build_attestation_builder_policy_mismatch")
    if expected_policy_version is not None and attestation.get("policy_version") != expected_policy_version:
        failures.append("build_attestation_policy_mismatch")
    body = {key: value for key, value in attestation.items() if key != "signature"}
    try:
        signature = base64.b64decode(attestation.get("signature", ""), validate=True)
        public_key.verify(signature, canonical_json_bytes(body))
    except (ValueError, InvalidSignature):
        failures.append("build_attestation_signature_invalid")
    for field in ("builder_id", "host_fingerprint", "environment_digest", "source_digest", "artifact_digest"):
        if not attestation.get(field):
            failures.append(f"build_attestation_{field}_missing")
    return failures


def build_independent_build_report(
    attestations: list[dict[str, Any]],
    public_keys: dict[str, Ed25519PublicKey],
    *,
    release_signer_key_id: str | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    verification: list[dict[str, Any]] = []
    for item in attestations:
        signer = item.get("signer_key_id")
        public_key = public_keys.get(str(signer))
        item_failures = ["independent_builder_public_key_missing"] if public_key is None else verify_attestation(item, public_key)
        verification.append({"builder_id": item.get("builder_id"), "signer_key_id": signer, "failures": item_failures, "valid": not item_failures})
        failures.extend(item_failures)
    builders = {item.get("builder_id") for item in attestations if item.get("builder_id")}
    hosts = {item.get("host_fingerprint") for item in attestations if item.get("host_fingerprint")}
    environments = {item.get("environment_digest") for item in attestations if item.get("environment_digest")}
    source_digests = {item.get("source_digest") for item in attestations if item.get("source_digest")}
    artifact_digests = {item.get("artifact_digest") for item in attestations if item.get("artifact_digest")}
    signer_ids = {item.get("signer_key_id") for item in attestations if item.get("signer_key_id")}
    if len(attestations) < 2:
        failures.append("fewer_than_two_build_attestations")
    if len(builders) < 2:
        failures.append("builder_identity_not_independent")
    if len(hosts) < 2:
        failures.append("builder_host_not_independent")
    if len(environments) < 2:
        failures.append("builder_environment_not_independent")
    if len(source_digests) != 1:
        failures.append("source_digest_disagreement")
    if len(artifact_digests) != 1:
        failures.append("artifact_digest_disagreement")
    if release_signer_key_id and release_signer_key_id in signer_ids:
        failures.append("release_signer_reused_as_independent_builder")
    base = {
        "schema": "sentinel-edge-independent-build-report/1.0",
        "attestations": attestations,
        "verification": verification,
        "builder_count": len(builders),
        "host_count": len(hosts),
        "environment_count": len(environments),
        "source_digest": next(iter(source_digests)) if len(source_digests) == 1 else None,
        "artifact_digest": next(iter(artifact_digests)) if len(artifact_digests) == 1 else None,
        "independent": not failures,
        "release_eligible": not failures,
        "failures": sorted(set(failures)),
        "limitations": [
            "Independence is proven only from the registered builder, host, environment and signer identities.",
            "A dishonest builder can still misreport its host unless the attestation is anchored in separately trusted infrastructure.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def write_independent_build_report(path: str | Path, report: dict[str, Any]) -> Path:
    output = Path(path)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_independent_build_report(path: str | Path, public_keys: dict[str, Ed25519PublicKey], *, release_signer_key_id: str | None = None) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    claimed = payload.get("report_digest")
    regenerated = build_independent_build_report(payload.get("attestations", []), public_keys, release_signer_key_id=release_signer_key_id)
    failures: list[str] = []
    if payload.get("schema") != "sentinel-edge-independent-build-report/1.0":
        failures.append("unsupported_independent_build_report_schema")
    if claimed != regenerated.get("report_digest"):
        failures.append("independent_build_report_digest_mismatch")
    if payload.get("failures") != regenerated.get("failures"):
        failures.append("independent_build_report_failure_set_mismatch")
    return {"valid": not failures, "release_eligible": regenerated.get("release_eligible", False) and not failures, "failures": failures}
