from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.update import key_id


def _candidate_bytes(path: str | Path) -> bytes:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return canonical_json_bytes(payload)


def sign_release_candidate(
    candidate_path: str | Path,
    private_key: Ed25519PrivateKey,
    output: str | Path | None = None,
) -> Path:
    candidate_path = Path(candidate_path)
    data = _candidate_bytes(candidate_path)
    signature = private_key.sign(data)
    payload = {
        "schema": "sentinel-edge-release-signature/1.0",
        "candidate_sha256": sha256_bytes(data),
        "signer_key_id": key_id(private_key.public_key()),
        "algorithm": "Ed25519",
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "signature": base64.b64encode(signature).decode("ascii"),
    }
    output = Path(output) if output else candidate_path.with_suffix(candidate_path.suffix + ".sig.json")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_release_signature(
    candidate_path: str | Path,
    signature_path: str | Path,
    public_key: Ed25519PublicKey,
) -> dict:
    data = _candidate_bytes(candidate_path)
    payload = json.loads(Path(signature_path).read_text(encoding="utf-8"))
    failures: list[str] = []
    if payload.get("algorithm") != "Ed25519":
        failures.append("unsupported_signature_algorithm")
    if payload.get("signer_key_id") != key_id(public_key):
        failures.append("signer_key_id_mismatch")
    if payload.get("candidate_sha256") != sha256_bytes(data):
        failures.append("candidate_digest_mismatch")
    try:
        signature = base64.b64decode(payload.get("signature", ""), validate=True)
        public_key.verify(signature, data)
    except (ValueError, InvalidSignature):
        failures.append("signature_invalid")
    return {
        "valid": not failures,
        "candidate_sha256": sha256_bytes(data),
        "signer_key_id": key_id(public_key),
        "failures": failures,
    }


def sign_release_manifest(
    manifest_path: str | Path,
    private_key: Ed25519PrivateKey,
    output: str | Path | None = None,
) -> Path:
    """Sign the exact canonical release manifest bytes and bind its digest."""
    manifest_path = Path(manifest_path)
    data = _candidate_bytes(manifest_path)
    payload = {
        "schema": "sentinel-edge-release-manifest-signature/1.0",
        "manifest_sha256": sha256_bytes(data),
        "signer_key_id": key_id(private_key.public_key()),
        "algorithm": "Ed25519",
        "signature": base64.b64encode(private_key.sign(data)).decode("ascii"),
    }
    output_path = Path(output) if output else manifest_path.with_suffix(manifest_path.suffix + ".sig.json")
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def verify_release_manifest_signature(
    manifest_path: str | Path,
    signature_path: str | Path,
    public_key: Ed25519PublicKey,
) -> dict:
    data = _candidate_bytes(manifest_path)
    payload = json.loads(Path(signature_path).read_text(encoding="utf-8"))
    failures: list[str] = []
    digest = sha256_bytes(data)
    if payload.get("schema") != "sentinel-edge-release-manifest-signature/1.0":
        failures.append("manifest_signature_schema_mismatch")
    if payload.get("algorithm") != "Ed25519":
        failures.append("unsupported_signature_algorithm")
    if payload.get("signer_key_id") != key_id(public_key):
        failures.append("signer_key_id_mismatch")
    if payload.get("manifest_sha256") != digest:
        failures.append("manifest_digest_mismatch")
    try:
        public_key.verify(base64.b64decode(payload.get("signature", ""), validate=True), data)
    except (ValueError, InvalidSignature):
        failures.append("signature_invalid")
    return {"valid": not failures, "manifest_sha256": digest, "signer_key_id": key_id(public_key), "failures": failures}
