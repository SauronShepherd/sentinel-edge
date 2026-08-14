"""Typed evidence-target binding and explicit content availability states."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EvidenceBindingState(StrEnum):
    BOUND = "bound"
    UNBOUND_TARGET = "unbound_target"
    DIGEST_PROFILE_UNKNOWN = "digest_profile_unknown"
    PROFILE_MISMATCH = "profile_mismatch"
    CONTENT_UNAVAILABLE = "content_unavailable"
    LATER_REDACTED = "later_redacted"


@dataclass(frozen=True)
class EvidenceTarget:
    kind: str
    identifier: str
    digest_profile: str | None
    content_sha256: str | None
    governed_external: bool = False


@dataclass(frozen=True)
class EvidenceRegistryEntry:
    evidence_id: str
    target: EvidenceTarget | None
    state: EvidenceBindingState

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id is required")
        if self.target is not None and (not self.target.kind.strip() or not self.target.identifier.strip()):
            raise ValueError("typed evidence target requires kind and identifier")
        if self.state is EvidenceBindingState.BOUND:
            if self.target is None or not self.target.digest_profile or not self.target.content_sha256:
                raise ValueError("bound evidence requires target, digest profile and content digest")
        elif self.state is EvidenceBindingState.UNBOUND_TARGET and self.target is not None:
            raise ValueError("unbound_target cannot carry a target")


def bind_evidence(evidence_id: str, target: EvidenceTarget | None, *, digest_profile_known: bool = True, content_available: bool = True, later_redacted: bool = False) -> EvidenceRegistryEntry:
    if target is None:
        return EvidenceRegistryEntry(evidence_id, None, EvidenceBindingState.UNBOUND_TARGET)
    if later_redacted:
        state = EvidenceBindingState.LATER_REDACTED
    elif not digest_profile_known:
        state = EvidenceBindingState.DIGEST_PROFILE_UNKNOWN
    elif not content_available:
        state = EvidenceBindingState.CONTENT_UNAVAILABLE
    elif not target.digest_profile:
        state = EvidenceBindingState.DIGEST_PROFILE_UNKNOWN
    elif not target.content_sha256:
        state = EvidenceBindingState.CONTENT_UNAVAILABLE
    else:
        state = EvidenceBindingState.BOUND
    return EvidenceRegistryEntry(evidence_id, target, state)
