from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.qualification import (
    RuntimeIssueContext,
    RuntimeIssueDisposition,
    RuntimeIssueException,
    RuntimeIssueMatch,
    RuntimeKnownIssue,
    RuntimeKnownIssueRegistry,
    evaluate_runtime_known_issues,
    sign_runtime_issue_registry,
    verify_runtime_issue_registry,
)

NOW = datetime(2026, 8, 3, 9, 30, tzinfo=timezone.utc)


def _registry() -> RuntimeKnownIssueRegistry:
    return RuntimeKnownIssueRegistry(
        registry_id="sentinel-runtime-known-issues",
        version=3,
        reviewed_at=NOW,
        expires_at=NOW + timedelta(days=30),
        issues=(
            RuntimeKnownIssue(
                issue_id="RKI-CPU-FALLBACK-001",
                title="Unexpected CPU fallback on exact graph",
                match=RuntimeIssueMatch(
                    runtime_name="sentinel-edge",
                    runtime_version="0.19.0",
                    provider="CPUExecutionProvider",
                    architecture="x86_64",
                    graph_sha256="a" * 64,
                    operator="Sigmoid",
                ),
                default_disposition=RuntimeIssueDisposition.DENY,
                evidence_refs=("tests/test_runtime_known_issues_v019.py",),
                introduced_at=NOW - timedelta(days=1),
                reviewed_at=NOW,
                expires_at=NOW + timedelta(days=30),
            ),
        ),
    )


def _context() -> RuntimeIssueContext:
    return RuntimeIssueContext(
        profile_id="wildfire-linear-v1",
        runtime_name="sentinel-edge",
        runtime_version="0.19.0",
        provider="CPUExecutionProvider",
        compiler="python-3.13",
        architecture="x86_64",
        graph_sha256="a" * 64,
        operators=("MatMul", "Add", "Sigmoid"),
        attributes={"quantization": "none"},
    )


def test_signed_runtime_issue_registry_is_fresh_and_digest_bound() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_runtime_issue_registry(_registry(), key, signed_at=NOW + timedelta(seconds=1))
    verified = verify_runtime_issue_registry(signed, key.public_key(), now=NOW + timedelta(days=1))
    assert verified["valid"] is True
    assert verified["registry_version"] == 3
    assert verified["reviewed_at"] == NOW.isoformat()


def test_applicable_runtime_issue_defaults_to_deny() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_runtime_issue_registry(_registry(), key, signed_at=NOW + timedelta(seconds=1))
    result = evaluate_runtime_known_issues(signed, key.public_key(), _context(), now=NOW + timedelta(days=1))
    assert result["activation_allowed"] is False
    assert result["matched_issues"][0]["disposition"] == "deny"
    assert "applicable_runtime_issue_denied:RKI-CPU-FALLBACK-001" in result["failures"]


def test_exact_expiring_exception_requires_owner_evidence_and_rollback() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_runtime_issue_registry(_registry(), key, signed_at=NOW + timedelta(seconds=1))
    exception = RuntimeIssueException(
        exception_id="EX-001",
        issue_id="RKI-CPU-FALLBACK-001",
        profile_id="wildfire-linear-v1",
        graph_sha256="a" * 64,
        owner="runtime-owner",
        evidence_refs=("evidence/runtime-exception-review.json",),
        rollback_plan="disable profile and restore prior signed profile",
        created_at=NOW,
        expires_at=NOW + timedelta(days=2),
    )
    result = evaluate_runtime_known_issues(
        signed, key.public_key(), _context(), exceptions=(exception,), now=NOW + timedelta(days=1)
    )
    assert result["activation_allowed"] is True
    assert result["used_exceptions"] == ["EX-001"]
    assert result["matched_issues"][0]["disposition"] == "exception"


def test_wildcard_or_stale_exception_cannot_bypass_issue() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_runtime_issue_registry(_registry(), key, signed_at=NOW + timedelta(seconds=1))
    stale = RuntimeIssueException(
        exception_id="EX-STALE",
        issue_id="RKI-CPU-FALLBACK-001",
        profile_id="other-profile",
        graph_sha256="b" * 64,
        owner="runtime-owner",
        evidence_refs=("evidence/review.json",),
        rollback_plan="restore",
        created_at=NOW - timedelta(days=3),
        expires_at=NOW - timedelta(days=1),
    )
    result = evaluate_runtime_known_issues(
        signed, key.public_key(), _context(), exceptions=(stale,), now=NOW + timedelta(days=1)
    )
    assert result["activation_allowed"] is False
    assert "runtime_issue_exception_invalid:RKI-CPU-FALLBACK-001" in result["failures"]


def test_stale_registry_blocks_activation_even_without_matching_issue() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_runtime_issue_registry(_registry(), key, signed_at=NOW + timedelta(seconds=1))
    context = _context().model_copy(update={"graph_sha256": "c" * 64, "operators": ("Add",)})
    result = evaluate_runtime_known_issues(
        signed, key.public_key(), context, now=NOW + timedelta(days=31)
    )
    assert result["activation_allowed"] is False
    assert "runtime_issue_registry_stale" in result["failures"]


def test_signature_substitution_is_rejected() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_runtime_issue_registry(_registry(), key, signed_at=NOW + timedelta(seconds=1))
    other = Ed25519PrivateKey.generate()
    verified = verify_runtime_issue_registry(signed, other.public_key(), now=NOW + timedelta(days=1))
    assert verified["valid"] is False
    assert "runtime_issue_registry_signer_mismatch" in verified["failures"]
