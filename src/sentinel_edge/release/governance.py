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

REVIEW_TYPES = {"security", "privacy", "accessibility"}
TERMINAL_FINDING_STATES = {"resolved", "accepted_risk", "not_applicable"}


def sign_review_packet(packet: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    body = dict(packet)
    body.setdefault("schema", "sentinel-edge-independent-review-packet/1.0")
    body["signer_key_id"] = key_id(private_key.public_key())
    body.setdefault("signed_at", datetime.now(timezone.utc).isoformat())
    signature = private_key.sign(canonical_json_bytes(body))
    return {**body, "signature": base64.b64encode(signature).decode("ascii")}


def verify_review_packet(packet: dict[str, Any], public_key: Ed25519PublicKey, *, builder_ids: set[str], release_signer_key_id: str | None = None) -> dict[str, Any]:
    failures: list[str] = []
    if packet.get("schema") != "sentinel-edge-independent-review-packet/1.0":
        failures.append("unsupported_review_packet_schema")
    if packet.get("review_type") not in REVIEW_TYPES:
        failures.append("unsupported_review_type")
    if packet.get("signer_key_id") != key_id(public_key):
        failures.append("review_signer_key_mismatch")
    if release_signer_key_id and packet.get("signer_key_id") == release_signer_key_id:
        failures.append("release_signer_cannot_self_review")
    reviewer_id = packet.get("reviewer_id")
    if not reviewer_id or reviewer_id in builder_ids:
        failures.append("reviewer_not_independent_from_builder")
    body = {key: value for key, value in packet.items() if key != "signature"}
    try:
        public_key.verify(base64.b64decode(packet.get("signature", ""), validate=True), canonical_json_bytes(body))
    except (ValueError, InvalidSignature):
        failures.append("review_signature_invalid")
    now = datetime.now(timezone.utc)
    for finding in packet.get("findings", []):
        state = finding.get("state")
        if state not in TERMINAL_FINDING_STATES:
            failures.append("review_finding_open")
        if state == "accepted_risk":
            expiry = finding.get("waiver_expires_at")
            if not expiry:
                failures.append("review_waiver_expiry_missing")
            else:
                try:
                    parsed = datetime.fromisoformat(str(expiry).replace("Z", "+00:00"))
                    if parsed <= now:
                        failures.append("review_waiver_expired")
                except ValueError:
                    failures.append("review_waiver_expiry_invalid")
        if not finding.get("evidence_refs"):
            failures.append("review_finding_evidence_missing")
    return {"valid": not failures, "release_eligible": not failures, "failures": sorted(set(failures)), "review_type": packet.get("review_type")}


def build_release_governance_report(
    *,
    packets: list[dict[str, Any]],
    reviewer_public_keys: dict[str, Ed25519PublicKey],
    builder_ids: set[str],
    release_signer_key_id: str | None,
    credential_profile: dict[str, Any],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for packet in packets:
        signer_id = str(packet.get("signer_key_id", ""))
        public_key = reviewer_public_keys.get(signer_id)
        result = {"valid": False, "release_eligible": False, "failures": ["review_public_key_missing"], "review_type": packet.get("review_type")}
        if public_key is not None:
            result = verify_review_packet(packet, public_key, builder_ids=builder_ids, release_signer_key_id=release_signer_key_id)
        results.append(result)
        failures.extend(result["failures"])
    passed_types = {result.get("review_type") for result in results if result.get("release_eligible")}
    missing_types = sorted(REVIEW_TYPES - passed_types)
    if missing_types:
        failures.append("required_independent_reviews_missing")
    credential_failures: list[str] = []
    if credential_profile.get("schema") != "sentinel-edge-release-credential-profile/1.0":
        credential_failures.append("unsupported_release_credential_profile")
    if credential_profile.get("private_key_storage") not in {"external_hsm", "external_offline_key"}:
        credential_failures.append("release_private_key_not_external")
    if credential_profile.get("development_bearer_tokens_present") is not False:
        credential_failures.append("development_credentials_present")
    purpose_ids = credential_profile.get("purpose_key_ids", {})
    nonempty = [value for value in purpose_ids.values() if value]
    if len(nonempty) != len(set(nonempty)):
        credential_failures.append("release_key_purpose_reuse_detected")
    if not credential_profile.get("rotation_tested"):
        credential_failures.append("release_credential_rotation_not_tested")
    failures.extend(credential_failures)
    base = {
        "schema": "sentinel-edge-release-governance-report/1.0",
        "review_packets": packets,
        "review_results": results,
        "review_types_passed": sorted(str(item) for item in passed_types if item),
        "review_types_missing": missing_types,
        "credential_profile": credential_profile,
        "credential_failures": credential_failures,
        "release_credentials_proven": not credential_failures,
        "independent_reviews_complete": not missing_types and all(result.get("release_eligible") for result in results),
        "release_eligible": not failures,
        "failures": sorted(set(failures)),
        "limitations": [
            "Reviewer independence is checked against declared builder and signer identities, not employment or financial relationships outside the packet.",
            "External key storage is represented by an operational profile; hardware security properties require deployment evidence.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def write_release_governance_report(path: str | Path, report: dict[str, Any]) -> Path:
    output = Path(path)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_release_governance_report(path: str | Path, reviewer_public_keys: dict[str, Ed25519PublicKey], *, builder_ids: set[str], release_signer_key_id: str | None) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    regenerated = build_release_governance_report(
        packets=payload.get("review_packets", []),
        reviewer_public_keys=reviewer_public_keys,
        builder_ids=builder_ids,
        release_signer_key_id=release_signer_key_id,
        credential_profile=payload.get("credential_profile", {}),
    )
    failures = []
    if payload.get("report_digest") != regenerated.get("report_digest"):
        failures.append("release_governance_report_digest_mismatch")
    if payload.get("failures") != regenerated.get("failures"):
        failures.append("release_governance_failure_set_mismatch")
    return {"valid": not failures, "release_eligible": regenerated.get("release_eligible", False) and not failures, "failures": failures}
