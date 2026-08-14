from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from typing import Any
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from subprocess import CompletedProcess

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.qualification.network_isolation import (
    evaluate_network_namespace_observation,
    probe_linux_network_namespace,
    verify_network_isolation_report,
)
from sentinel_edge.release.governance import (
    build_release_governance_report,
    sign_review_packet,
)
from sentinel_edge.release.independent_build import (
    build_attestation,
    build_independent_build_report,
)
from sentinel_edge.release.wheelhouse import inspect_wheel, verify_wheelhouse
from sentinel_edge.update import key_id


def _wheel_record_line(path: str, data: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
    return f"{path},sha256={digest},{len(data)}"


def _make_wheel(directory: Path, name: str = "demo-pkg", version: str = "1.2.3") -> Path:
    normalized = name.replace("-", "_")
    filename = f"{normalized}-{version}-py3-none-any.whl"
    path = directory / filename
    dist_info = f"{normalized}-{version}.dist-info"
    files = {
        f"{normalized}/__init__.py": f"__version__ = '{version}'\n".encode(),
        f"{dist_info}/METADATA": f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n\n".encode(),
        f"{dist_info}/WHEEL": b"Wheel-Version: 1.0\nGenerator: sentinel-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    record_path = f"{dist_info}/RECORD"
    lines = [_wheel_record_line(member, data) for member, data in files.items()]
    lines.append(f"{record_path},,")
    files[record_path] = ("\n".join(lines) + "\n").encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for member, data in files.items():
            archive.writestr(member, data)
    return path


def test_offline_wheelhouse_exact_lock_and_rehearsal(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    wheel = _make_wheel(wheelhouse)
    inspected = inspect_wheel(wheel)
    assert inspected["valid"] is True
    lock = {
        "schema": "sentinel-edge-release-lock/1.0",
        "resolved": [{"name": "demo-pkg", "version": "1.2.3", "state": "resolved"}],
    }
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    report = verify_wheelhouse(lock_path, wheelhouse, compatible_tags={"py3-none-any"}, install_rehearsal=True)
    assert report["complete"] is True
    assert report["release_eligible"] is True
    assert report["install_rehearsal"]["success"] is True


def test_wheelhouse_rejects_missing_locked_package(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    _make_wheel(wheelhouse)
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps({"resolved": [{"name": "other", "version": "9", "state": "resolved"}]}), encoding="utf-8")
    report = verify_wheelhouse(lock_path, wheelhouse)
    assert report["release_eligible"] is False
    assert "locked_wheels_missing" in report["failures"]


def test_linux_network_namespace_observation_proves_below_application_denial() -> None:
    def runner(*args: Any, **kwargs: Any) -> Any:
        payload = {
            "child_namespace": "net:[222]",
            "dns_probe_blocked": True,
            "tcp_probe_blocked": True,
            "misbehaving_adapter_blocked": True,
        }
        return CompletedProcess(args=args[0], returncode=0, stdout=json.dumps(payload), stderr="")

    observation = probe_linux_network_namespace(runner=runner)
    observation["parent_namespace"] = "net:[111]"
    report = evaluate_network_namespace_observation(observation)
    assert report["below_application_layer_proven"] is True
    assert report["release_eligible"] is True


def test_linux_network_namespace_rejects_same_namespace() -> None:
    observation = {
        "schema": "sentinel-edge-network-isolation-observation/1.0",
        "supported": True,
        "parent_namespace": "net:[1]",
        "child_namespace": "net:[1]",
        "dns_probe_blocked": True,
        "tcp_probe_blocked": True,
        "misbehaving_adapter_blocked": True,
    }
    report = evaluate_network_namespace_observation(observation)
    assert report["release_eligible"] is False
    assert "network_namespace_not_distinct" in report["failures"]


def test_independent_build_requires_distinct_builder_host_environment() -> None:
    key_a = Ed25519PrivateKey.generate()
    key_b = Ed25519PrivateKey.generate()
    a = build_attestation(builder_id="builder-a", host_fingerprint="host-a", environment_digest="env-a", source_digest="source", artifact_digest="artifact", private_key=key_a)
    b = build_attestation(builder_id="builder-b", host_fingerprint="host-b", environment_digest="env-b", source_digest="source", artifact_digest="artifact", private_key=key_b)
    report = build_independent_build_report(
        [a, b],
        {key_id(key_a.public_key()): key_a.public_key(), key_id(key_b.public_key()): key_b.public_key()},
        release_signer_key_id="release-key",
    )
    assert report["independent"] is True
    assert report["release_eligible"] is True


def test_independent_build_rejects_same_host_and_release_signer() -> None:
    key = Ed25519PrivateKey.generate()
    signer = key_id(key.public_key())
    a = build_attestation(builder_id="builder-a", host_fingerprint="host", environment_digest="env-a", source_digest="source", artifact_digest="artifact", private_key=key)
    b = build_attestation(builder_id="builder-b", host_fingerprint="host", environment_digest="env-b", source_digest="source", artifact_digest="artifact", private_key=key)
    report = build_independent_build_report([a, b], {signer: key.public_key()}, release_signer_key_id=signer)
    assert report["release_eligible"] is False
    assert "builder_host_not_independent" in report["failures"]
    assert "release_signer_reused_as_independent_builder" in report["failures"]


def _review(review_type: str, reviewer_id: str, key: Ed25519PrivateKey, *, state: str = "resolved") -> dict:
    finding = {
        "finding_id": f"{review_type}-1",
        "severity": "medium",
        "state": state,
        "evidence_refs": ["evidence/test.json"],
    }
    if state == "accepted_risk":
        finding["waiver_expires_at"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    return sign_review_packet(
        {
            "review_type": review_type,
            "reviewer_id": reviewer_id,
            "reviewer_organization": f"org-{reviewer_id}",
            "scope_digest": "scope",
            "findings": [finding],
        },
        key,
    )


def test_release_governance_requires_three_independent_reviews_and_external_credentials() -> None:
    keys = {kind: Ed25519PrivateKey.generate() for kind in ("security", "privacy", "accessibility")}
    packets = [_review(kind, f"reviewer-{kind}", key) for kind, key in keys.items()]
    public = {key_id(key.public_key()): key.public_key() for key in keys.values()}
    credential_profile = {
        "schema": "sentinel-edge-release-credential-profile/1.0",
        "private_key_storage": "external_offline_key",
        "development_bearer_tokens_present": False,
        "rotation_tested": True,
        "purpose_key_ids": {"release": "release", "audit": "audit", "update": "update", "boot": "boot"},
    }
    report = build_release_governance_report(
        packets=packets,
        reviewer_public_keys=public,
        builder_ids={"builder-a", "builder-b"},
        release_signer_key_id="release",
        credential_profile=credential_profile,
    )
    assert report["independent_reviews_complete"] is True
    assert report["release_credentials_proven"] is True
    assert report["release_eligible"] is True


def test_release_governance_rejects_self_review_and_development_credentials() -> None:
    key = Ed25519PrivateKey.generate()
    packet = _review("security", "builder-a", key)
    report = build_release_governance_report(
        packets=[packet],
        reviewer_public_keys={key_id(key.public_key()): key.public_key()},
        builder_ids={"builder-a"},
        release_signer_key_id=key_id(key.public_key()),
        credential_profile={
            "schema": "sentinel-edge-release-credential-profile/1.0",
            "private_key_storage": "repository_file",
            "development_bearer_tokens_present": True,
            "rotation_tested": False,
            "purpose_key_ids": {"release": "same", "audit": "same"},
        },
    )
    assert report["release_eligible"] is False
    assert "required_independent_reviews_missing" in report["failures"]
    assert "release_private_key_not_external" in report["failures"]
