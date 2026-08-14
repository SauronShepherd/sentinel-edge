import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.release import (
    build_cyclonedx_sbom,
    sign_release_candidate,
    verify_release_signature,
)


def test_sbom_declares_runtime_dependencies_and_limitations() -> None:
    sbom = build_cyclonedx_sbom(".")
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.7"
    names = {item["name"] for item in sbom["components"]}
    assert {"fastapi", "pydantic", "PyYAML", "uvicorn", "cryptography"} <= names
    properties = {item["name"]: item["value"] for item in sbom["metadata"]["properties"]}
    assert properties["sentinel-edge:completeness"] == "does-not-prove-dynamic-or-os-dependency-completeness"
    assert all(item.get("hashes") for item in sbom["components"] if item["version"] != "unresolved")
    assert sbom["dependencies"][0]["dependsOn"] == [item["bom-ref"] for item in sbom["components"]]


def test_release_candidate_signature_detects_tamper(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"candidate_id": "abc", "release_admitted": False}) + "\n", encoding="utf-8")
    private = Ed25519PrivateKey.generate()
    signature = sign_release_candidate(candidate, private)
    valid = verify_release_signature(candidate, signature, private.public_key())
    assert valid["valid"] is True
    candidate.write_text(json.dumps({"candidate_id": "changed", "release_admitted": False}) + "\n", encoding="utf-8")
    invalid = verify_release_signature(candidate, signature, private.public_key())
    assert invalid["valid"] is False
    assert "candidate_digest_mismatch" in invalid["failures"]
    other = Ed25519PrivateKey.generate()
    untrusted = verify_release_signature(candidate, signature, other.public_key())
    assert untrusted["valid"] is False
    assert "signer_key_id_mismatch" in untrusted["failures"]
    assert "signature_invalid" in untrusted["failures"]


def test_third_party_inventory_is_explicit_about_unknowns() -> None:
    from sentinel_edge.release import build_third_party_inventory

    inventory = build_third_party_inventory(".")
    assert inventory["scope"] == "declared_runtime_dependencies"
    assert inventory["limitations"]
    assert {item["name"] for item in inventory["packages"]} >= {"fastapi", "cryptography"}


def test_third_party_notices_are_generated(tmp_path: Path) -> None:
    from sentinel_edge.release import write_third_party_notices

    output = write_third_party_notices(".", tmp_path / "THIRD_PARTY_NOTICES.md")
    text = output.read_text(encoding="utf-8")
    assert "# Third-party notices" in text
    assert "fastapi" in text
    assert "manual license verification" in text
