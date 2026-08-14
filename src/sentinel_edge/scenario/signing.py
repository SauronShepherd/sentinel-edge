from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


def sign_scenario(manifest: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    payload = canonical_json_bytes(manifest)
    return {
        "schema": "sentinel-edge-signed-scenario/1.0",
        "manifest": manifest,
        "manifest_sha256": sha256_bytes(payload),
        "algorithm": "Ed25519",
        "signature_b64": base64.b64encode(private_key.sign(payload)).decode("ascii"),
    }


def verify_signed_scenario(envelope: dict[str, Any], public_key: Ed25519PublicKey) -> dict[str, Any]:
    if envelope.get("schema") != "sentinel-edge-signed-scenario/1.0":
        raise ValueError("unsupported scenario envelope")
    if envelope.get("algorithm") != "Ed25519":
        raise ValueError("unsupported scenario signature algorithm")
    manifest = envelope.get("manifest")
    if not isinstance(manifest, dict):
        raise ValueError("scenario manifest missing")
    payload = canonical_json_bytes(manifest)
    if envelope.get("manifest_sha256") != sha256_bytes(payload):
        raise ValueError("scenario manifest hash mismatch")
    try:
        signature = base64.b64decode(str(envelope.get("signature_b64", "")), validate=True)
        public_key.verify(signature, payload)
    except (ValueError, InvalidSignature) as exc:
        raise ValueError("scenario signature invalid") from exc
    return {"manifest": manifest, "manifest_sha256": envelope["manifest_sha256"]}


def load_signed_scenario(path: str | Path, public_key: Ed25519PublicKey) -> tuple[dict[str, Any], str]:
    envelope = json.loads(Path(path).read_text(encoding="utf-8"))
    verified = verify_signed_scenario(envelope, public_key)
    return verified["manifest"], verified["manifest_sha256"]
