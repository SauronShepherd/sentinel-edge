import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.release.manifest import build_release_candidate_manifest, write_manifest
from sentinel_edge.release.signing import sign_release_manifest, verify_release_manifest_signature


def test_release_manifest_signature_binds_exact_manifest_bytes(tmp_path: Path) -> None:
    (tmp_path / "evidence.json").write_text('{"ok":true}\n', encoding="utf-8")
    manifest = write_manifest(tmp_path)
    private = Ed25519PrivateKey.generate()
    signature = sign_release_manifest(manifest, private)
    assert verify_release_manifest_signature(manifest, signature, private.public_key())["valid"]
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["files"].append({"path": "forged", "bytes": 1, "sha256": "0" * 64})
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = verify_release_manifest_signature(manifest, signature, private.public_key())
    assert not result["valid"]
    assert "manifest_digest_mismatch" in result["failures"]


def test_candidate_manifest_binds_candidate_and_inventory(tmp_path: Path) -> None:
    candidate = tmp_path / "release-candidate.json"
    candidate.write_text('{"candidate_id":"c1"}\n', encoding="utf-8")
    payload = build_release_candidate_manifest(tmp_path, candidate)
    assert payload["candidate_path"] == "release-candidate.json"
    assert payload["candidate_sha256"]
    assert payload["inventory_sha256"]
