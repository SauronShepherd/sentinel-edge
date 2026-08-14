from __future__ import annotations

import base64
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.update import key_id


class RuntimeIssueDisposition(StrEnum):
    DENY = "deny"
    REWRITE = "rewrite"
    FALLBACK = "fallback"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    EXCEPTION = "exception"


class RuntimeIssueMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runtime_name: str | None = None
    runtime_version: str | None = None
    provider: str | None = None
    compiler: str | None = None
    architecture: str | None = None
    operator: str | None = None
    attribute_name: str | None = None
    attribute_value: str | None = None
    graph_sha256: str | None = None

    @model_validator(mode="after")
    def at_least_one_scope(self) -> "RuntimeIssueMatch":
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("runtime known issue requires at least one exact scope")
        if self.graph_sha256 is not None and len(self.graph_sha256) != 64:
            raise ValueError("graph_sha256 must be a SHA-256 digest")
        return self


class RuntimeKnownIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issue_id: str
    title: str
    match: RuntimeIssueMatch
    default_disposition: RuntimeIssueDisposition
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    introduced_at: datetime
    reviewed_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_issue(self) -> "RuntimeKnownIssue":
        if not self.issue_id.strip() or not self.title.strip():
            raise ValueError("runtime issue identity and title must not be blank")
        if not self.introduced_at <= self.reviewed_at < self.expires_at:
            raise ValueError("runtime issue review timeline is invalid")
        return self


class RuntimeKnownIssueRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: str = Field(default="sentinel-edge-runtime-known-issue-registry/1.0", alias="schema")
    registry_id: str
    version: int = Field(ge=1)
    reviewed_at: datetime
    expires_at: datetime
    issues: tuple[RuntimeKnownIssue, ...]

    @model_validator(mode="after")
    def validate_registry(self) -> "RuntimeKnownIssueRegistry":
        if self.expires_at <= self.reviewed_at:
            raise ValueError("registry expiry must follow review")
        issue_ids = [item.issue_id for item in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            raise ValueError("runtime issue IDs must be unique")
        return self


class SignedRuntimeKnownIssueRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: str = Field(default="sentinel-edge-signed-runtime-known-issue-registry/1.0", alias="schema")
    registry: RuntimeKnownIssueRegistry
    registry_sha256: str
    signer_key_id: str
    signed_at: datetime
    algorithm: str = "Ed25519"
    signature_b64: str


class RuntimeIssueContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str
    runtime_name: str
    runtime_version: str
    provider: str
    compiler: str
    architecture: str
    graph_sha256: str
    operators: tuple[str, ...] = ()
    attributes: dict[str, str] = {}


class RuntimeIssueException(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    exception_id: str
    issue_id: str
    profile_id: str
    graph_sha256: str
    owner: str
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    rollback_plan: str
    created_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_exception(self) -> "RuntimeIssueException":
        if self.expires_at <= self.created_at:
            raise ValueError("runtime issue exception must expire")
        if len(self.graph_sha256) != 64:
            raise ValueError("runtime issue exception graph digest is invalid")
        for value in (self.exception_id, self.issue_id, self.profile_id, self.owner, self.rollback_plan):
            if not value.strip():
                raise ValueError("runtime issue exception fields must not be blank")
        return self


def sign_runtime_issue_registry(
    registry: RuntimeKnownIssueRegistry,
    private_key: Ed25519PrivateKey,
    *,
    signed_at: datetime | None = None,
) -> SignedRuntimeKnownIssueRegistry:
    payload = canonical_json_bytes(registry.model_dump(mode="json"))
    return SignedRuntimeKnownIssueRegistry(
        registry=registry,
        registry_sha256=sha256_bytes(payload),
        signer_key_id=key_id(private_key.public_key()),
        signed_at=signed_at or datetime.now(timezone.utc),
        signature_b64=base64.b64encode(private_key.sign(payload)).decode("ascii"),
    )


def verify_runtime_issue_registry(
    envelope: SignedRuntimeKnownIssueRegistry | dict[str, Any],
    public_key: Ed25519PublicKey,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    signed = envelope if isinstance(envelope, SignedRuntimeKnownIssueRegistry) else SignedRuntimeKnownIssueRegistry.model_validate(envelope)
    payload = canonical_json_bytes(signed.registry.model_dump(mode="json"))
    failures: list[str] = []
    if sha256_bytes(payload) != signed.registry_sha256:
        failures.append("runtime_issue_registry_digest_mismatch")
    if key_id(public_key) != signed.signer_key_id:
        failures.append("runtime_issue_registry_signer_mismatch")
    try:
        public_key.verify(base64.b64decode(signed.signature_b64, validate=True), payload)
    except (ValueError, InvalidSignature):
        failures.append("runtime_issue_registry_signature_invalid")
    if signed.signed_at < signed.registry.reviewed_at:
        failures.append("runtime_issue_registry_signed_before_review")
    if now >= signed.registry.expires_at:
        failures.append("runtime_issue_registry_stale")
    base = {
        "schema": "sentinel-edge-runtime-known-issue-registry-verification/1.0",
        "registry_id": signed.registry.registry_id,
        "registry_version": signed.registry.version,
        "reviewed_at": signed.registry.reviewed_at.isoformat(),
        "expires_at": signed.registry.expires_at.isoformat(),
        "registry_sha256": signed.registry_sha256,
        "signer_key_id": signed.signer_key_id,
        "valid": not failures,
        "fresh": now < signed.registry.expires_at,
        "failures": sorted(set(failures)),
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def _matches(match: RuntimeIssueMatch, context: RuntimeIssueContext) -> bool:
    exact = {
        "runtime_name": context.runtime_name,
        "runtime_version": context.runtime_version,
        "provider": context.provider,
        "compiler": context.compiler,
        "architecture": context.architecture,
        "graph_sha256": context.graph_sha256,
    }
    for name, observed in exact.items():
        expected = getattr(match, name)
        if expected is not None and expected != observed:
            return False
    if match.operator is not None and match.operator not in context.operators:
        return False
    if match.attribute_name is not None:
        if context.attributes.get(match.attribute_name) != match.attribute_value:
            return False
    return True


def evaluate_runtime_known_issues(
    envelope: SignedRuntimeKnownIssueRegistry | dict[str, Any],
    public_key: Ed25519PublicKey,
    context: RuntimeIssueContext,
    *,
    exceptions: tuple[RuntimeIssueException, ...] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    signed = envelope if isinstance(envelope, SignedRuntimeKnownIssueRegistry) else SignedRuntimeKnownIssueRegistry.model_validate(envelope)
    verification = verify_runtime_issue_registry(signed, public_key, now=now)
    failures: list[str] = list(verification["failures"])
    matched: list[dict[str, Any]] = []
    used_exceptions: list[str] = []
    if verification["valid"]:
        for issue in signed.registry.issues:
            if not _matches(issue.match, context):
                continue
            disposition = issue.default_disposition
            exception = next((item for item in exceptions if item.issue_id == issue.issue_id), None)
            exception_valid = False
            if exception is not None:
                exception_valid = (
                    exception.profile_id == context.profile_id
                    and exception.graph_sha256 == context.graph_sha256
                    and now < exception.expires_at
                    and bool(exception.evidence_refs)
                    and bool(exception.rollback_plan.strip())
                )
                if exception_valid:
                    disposition = RuntimeIssueDisposition.EXCEPTION
                    used_exceptions.append(exception.exception_id)
                else:
                    failures.append(f"runtime_issue_exception_invalid:{issue.issue_id}")
            matched.append({
                "issue_id": issue.issue_id,
                "title": issue.title,
                "disposition": disposition.value,
                "exception_id": exception.exception_id if exception_valid and exception else None,
                "evidence_refs": list(issue.evidence_refs),
            })
            if disposition is RuntimeIssueDisposition.DENY:
                failures.append(f"applicable_runtime_issue_denied:{issue.issue_id}")
    base = {
        "schema": "sentinel-edge-runtime-known-issue-evaluation/1.0",
        "profile_id": context.profile_id,
        "graph_sha256": context.graph_sha256,
        "registry_id": signed.registry.registry_id,
        "registry_version": signed.registry.version,
        "registry_reviewed_at": signed.registry.reviewed_at.isoformat(),
        "registry_expires_at": signed.registry.expires_at.isoformat(),
        "matched_issues": matched,
        "used_exceptions": sorted(used_exceptions),
        "activation_allowed": not failures,
        "target_qualified": False,
        "failures": sorted(set(failures)),
        "limitations": [
            "The registry matcher proves only the exact runtime, provider, compiler, architecture, operator, attribute and graph scopes represented in the context.",
            "Target qualification still requires exact target runtime introspection and released graph inventory evidence.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}
