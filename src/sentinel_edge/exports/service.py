from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.domain.models import EvidenceContentState, EvidenceRightsMode, EvidenceRetentionState
from sentinel_edge.evidence import EvidenceTrustService
from sentinel_edge.authority import AuthorityWatermark
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.storage.artifacts import ContentAddressedArtifactStore
from sentinel_edge.storage.artifact_governance import ArtifactClassification, ArtifactExportPolicy
from sentinel_edge.exports.scanner import ExportAudience, ExportLeakScanner


_CLASS_ORDER = {
    ArtifactClassification.PUBLIC: 0,
    ArtifactClassification.INTERNAL: 1,
    ArtifactClassification.RESTRICTED: 2,
    ArtifactClassification.SECRET_PROHIBITED: 3,
}


def export_manifest_payload_sha256(payload: dict[str, Any]) -> str:
    stable = {
        "schema": payload.get("schema", "sentinel-edge-evidence-export/1.0"),
        "incident_ids": payload.get("incident_ids", []),
        "members": payload.get("members", []),
        "source_graph_sha256": payload.get("source_graph_sha256", {}),
        "completeness": payload.get("completeness", "closed_over_declared_members"),
        "secret_values_persisted": bool(payload.get("secret_values_persisted", False)),
        "audience": payload.get("audience", "internal"),
        "leak_scan_sha256": payload.get("leak_scan_sha256"),
        "authority_epoch_id": payload.get("authority_epoch_id", "unknown"),
        "authority_watermark": int(payload.get("authority_watermark", 0)),
        "authority_watermark_record": payload.get("authority_watermark_record"),
    }
    return sha256_bytes(canonical_json_bytes(stable))


class EvidenceExportSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: UUID
    classification: ArtifactClassification
    include_content: bool = False
    redaction_profile: str | None = None


class DerivedArtifactSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_evidence_id: UUID
    artifact_sha256: str
    media_type: str
    classification: ArtifactClassification
    transformation: str
    redactions: tuple[str, ...] = ()

    @field_validator("artifact_sha256")
    @classmethod
    def digest_valid(cls, value: str) -> str:
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
            raise ValueError("artifact_sha256 must be a lowercase SHA-256 digest")
        return value


class ExportMember(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    bytes: int = Field(ge=0)
    sha256: str
    media_type: str
    classification: ArtifactClassification
    source_evidence_id: UUID
    target_binding: str
    transformation: str
    rights_decision: str
    lifecycle_state: EvidenceContentState
    redactions: tuple[str, ...] = ()

    @field_validator("path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        candidate = PurePosixPath(value)
        first_part = candidate.parts[0] if candidate.parts else ""
        if (
            candidate.is_absolute()
            or ".." in candidate.parts
            or not value.strip()
            or "\\" in value
            or (len(first_part) == 2 and first_part[1] == ":")
        ):
            raise ValueError("export member path must be a safe relative path")
        return value


class EvidenceExportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: str = Field(default="sentinel-edge-evidence-export/1.0", alias="schema")
    export_id: UUID
    created_at: datetime
    incident_ids: tuple[UUID, ...]
    members: tuple[ExportMember, ...]
    source_graph_sha256: dict[str, str]
    completeness: str = "closed_over_declared_members"
    secret_values_persisted: bool = False
    audience: ExportAudience = ExportAudience.INTERNAL
    research_warning: str = (
        "Research monitoring and decision support; not an official warning service."
    )
    leak_scan_sha256: str | None = None
    authority_epoch_id: str = "unknown"
    authority_watermark: int = Field(default=0, ge=0)
    authority_watermark_record: AuthorityWatermark
    manifest_payload_sha256: str

    @model_validator(mode="before")
    @classmethod
    def validate_payload_digest(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        observed = payload.pop("manifest_payload_sha256", None)
        expected = export_manifest_payload_sha256(payload)
        if observed != expected:
            raise ValueError("export manifest payload digest mismatch")
        return value

    @model_validator(mode="after")
    def validate_manifest(self) -> "EvidenceExportManifest":
        paths = [item.path for item in self.members]
        if len(paths) != len(set(paths)):
            raise ValueError("export member paths must be unique")
        if any(item.classification is ArtifactClassification.SECRET_PROHIBITED for item in self.members):
            raise ValueError("secret-prohibited artifacts cannot be exported")
        if self.authority_watermark_record.epoch_id != self.authority_epoch_id:
            raise ValueError("authority watermark epoch mismatch")
        if self.authority_watermark_record.highest_contiguous_position != self.authority_watermark:
            raise ValueError("authority watermark position mismatch")
        if not self.authority_watermark_record.valid:
            raise ValueError("export requires a valid authority watermark")
        return self


class EvidenceExportService:
    """Rights-aware, content-addressed evidence export with exact member closure."""

    def __init__(
        self,
        evidence: EvidenceTrustService,
        artifacts: ContentAddressedArtifactStore,
        disposition=None,
        *,
        authority_watermark_supplier: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self.evidence = evidence
        self.artifacts = artifacts
        self.disposition = disposition
        if authority_watermark_supplier is not None:
            self.authority_watermark_supplier = authority_watermark_supplier
        elif hasattr(evidence.store, "authority_conformance"):
            self.authority_watermark_supplier = evidence.store.authority_conformance
        else:
            self.authority_watermark_supplier = None
        self.scanner = ExportLeakScanner()

    def _artifact_bytes(self, digest: str) -> bytes:
        path = self.artifacts.root / digest[:2] / digest[2:]
        if not path.is_file():
            raise FileNotFoundError(f"artifact not found for digest {digest}")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError("artifact digest mismatch during export")
        return data

    @staticmethod
    def _metadata_payload(item: Any, classification: ArtifactClassification, redaction_profile: str | None) -> tuple[bytes, tuple[str, ...]]:
        payload = item.model_dump(mode="json")
        redactions: list[str] = []
        if classification is ArtifactClassification.RESTRICTED:
            payload["claim_text"] = "[REDACTED]"
            payload["source_id"] = f"source-sha256:{sha256_bytes(str(item.source_id).encode())[:16]}"
            payload["origin_key"] = f"origin-sha256:{sha256_bytes(str(item.origin_key).encode())[:16]}"
            redactions.extend(("claim_text", "source_id", "origin_key"))
        if redaction_profile:
            redactions.append(f"profile:{redaction_profile}")
        return canonical_json_bytes(payload), tuple(sorted(set(redactions)))

    def create(
        self,
        output_zip: str | Path,
        *,
        selections: tuple[EvidenceExportSelection, ...],
        derivatives: tuple[DerivedArtifactSelection, ...] = (),
        created_at: datetime | None = None,
        audience: ExportAudience = ExportAudience.INTERNAL,
    ) -> EvidenceExportManifest:
        if not selections:
            raise ValueError("export requires at least one evidence selection")
        created_at = created_at or datetime.now(timezone.utc)
        evidence_by_id = {item.evidence_id: item for item in self.evidence.store.evidence()}
        selection_by_id = {item.evidence_id: item for item in selections}
        if len(selection_by_id) != len(selections):
            raise ValueError("duplicate evidence selection")
        missing = set(selection_by_id) - set(evidence_by_id)
        if missing:
            raise KeyError(f"unknown evidence selections: {sorted(str(item) for item in missing)}")
        if any(item.classification is ArtifactClassification.SECRET_PROHIBITED for item in selections):
            raise ValueError("secret-prohibited artifacts cannot be finalized or exported")

        incident_ids = tuple(sorted({evidence_by_id[item.evidence_id].incident_id for item in selections}, key=str))
        graph_digests = {str(incident_id): self.evidence.graph_digest(incident_id) for incident_id in incident_ids}
        seed = {
            "created_at": created_at.isoformat(),
            "selections": [item.model_dump(mode="json") for item in selections],
            "derivatives": [item.model_dump(mode="json") for item in derivatives],
            "graphs": graph_digests,
        }
        export_id = uuid5(NAMESPACE_URL, f"sentinel-export:{sha256_bytes(canonical_json_bytes(seed))}")
        output_zip = Path(output_zip)
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        members: list[ExportMember] = []
        payloads: dict[str, bytes] = {}

        for selection in sorted(selections, key=lambda item: str(item.evidence_id)):
            item = evidence_by_id[selection.evidence_id]
            if self.disposition is not None and self.disposition.is_restricted(item.evidence_id):
                raise PermissionError("evidence is restricted by an active disposition request")
            lifecycle = self.evidence.lifecycle(item.evidence_id)
            if selection.include_content and (not lifecycle.readable or not lifecycle.rights_active):
                raise PermissionError(f"evidence content is not exportable in state {lifecycle.state.value}")
            try:
                effective_policy = self.artifacts.catalog.effective_policy(item.content_sha256)
            except KeyError:
                effective_policy = None
            if effective_policy is not None:
                if effective_policy.export_policy is ArtifactExportPolicy.PROHIBITED and selection.include_content:
                    raise PermissionError("artifact policy prohibits content export")
                if _CLASS_ORDER[selection.classification] < _CLASS_ORDER[effective_policy.classification]:
                    raise PermissionError("export classification cannot be less restrictive than artifact catalog policy")
            metadata, redactions = self._metadata_payload(item, selection.classification, selection.redaction_profile)
            metadata_path = f"evidence/{item.evidence_id}/metadata.json"
            payloads[metadata_path] = metadata
            members.append(ExportMember(
                path=metadata_path,
                bytes=len(metadata),
                sha256=sha256_bytes(metadata),
                media_type="application/json",
                classification=selection.classification,
                source_evidence_id=item.evidence_id,
                target_binding=f"evidence:{item.evidence_id}",
                transformation="canonical_metadata_export_v1",
                rights_decision=f"{item.rights_mode.value}:{lifecycle.state.value}",
                lifecycle_state=lifecycle.state,
                redactions=redactions,
            ))
            if selection.include_content:
                if not lifecycle.readable or not lifecycle.rights_active:
                    raise PermissionError(f"evidence content is not exportable in state {lifecycle.state.value}")
                if item.retention_state is not EvidenceRetentionState.RETAINED or item.rights_mode is not EvidenceRightsMode.RETAIN_BYTES:
                    raise PermissionError("evidence content retention policy does not permit byte export")
                data = self._artifact_bytes(item.content_sha256)
                content_path = f"evidence/{item.evidence_id}/content.bin"
                payloads[content_path] = data
                members.append(ExportMember(
                    path=content_path,
                    bytes=len(data),
                    sha256=item.content_sha256,
                    media_type="application/octet-stream",
                    classification=selection.classification,
                    source_evidence_id=item.evidence_id,
                    target_binding=f"artifact-sha256:{item.content_sha256}",
                    transformation="identity_content_export",
                    rights_decision="retain_bytes_rights_active",
                    lifecycle_state=lifecycle.state,
                ))

        for derivative in sorted(derivatives, key=lambda item: (str(item.source_evidence_id), item.artifact_sha256)):
            if derivative.classification is ArtifactClassification.SECRET_PROHIBITED:
                raise ValueError("secret-prohibited derivatives cannot be exported")
            source_selection = selection_by_id.get(derivative.source_evidence_id)
            source_item = evidence_by_id.get(derivative.source_evidence_id)
            if source_selection is None or source_item is None:
                raise ValueError("derivative source evidence must be selected")
            source_lifecycle = self.evidence.lifecycle(source_item.evidence_id)
            if source_lifecycle.state in {EvidenceContentState.EXPIRED, EvidenceContentState.DELETED, EvidenceContentState.MISSING_EXTERNAL}:
                raise PermissionError("derivative cannot bypass source lifecycle restriction")
            if _CLASS_ORDER[derivative.classification] < _CLASS_ORDER[source_selection.classification]:
                raise PermissionError("derivative classification cannot be less restrictive than its source")
            data = self._artifact_bytes(derivative.artifact_sha256)
            path = f"derivatives/{derivative.source_evidence_id}/{derivative.artifact_sha256}.bin"
            payloads[path] = data
            members.append(ExportMember(
                path=path,
                bytes=len(data),
                sha256=derivative.artifact_sha256,
                media_type=derivative.media_type,
                classification=derivative.classification,
                source_evidence_id=derivative.source_evidence_id,
                target_binding=f"artifact-sha256:{derivative.artifact_sha256}",
                transformation=derivative.transformation,
                rights_decision=f"inherits:{source_item.rights_mode.value}:{source_lifecycle.state.value}",
                lifecycle_state=source_lifecycle.state,
                redactions=derivative.redactions,
            ))

        findings = self.scanner.scan(payloads.items(), audience=audience)
        if findings:
            summary = ",".join(f"{item.category}:{item.member}" for item in findings[:8])
            raise PermissionError(f"export leak scan rejected bundle: {summary}")
        leak_scan_sha256 = sha256_bytes(canonical_json_bytes({
            "audience": audience.value,
            "research_warning": (
                "Research monitoring and decision support; not an official warning service."
            ),
            "findings": [],
            "members": sorted(payloads),
        }))
        authority = self.authority_watermark_supplier() if self.authority_watermark_supplier else {
            "epoch_id": "unknown", "highest_contiguous_position": 0, "event_count": 0, "valid": False,
            "failures": ("authority_supplier_missing",),
        }
        watermark_record = AuthorityWatermark.from_conformance(authority)
        if not watermark_record.valid:
            raise RuntimeError("authority journal is not conformant for export")
        base = {
            "schema": "sentinel-edge-evidence-export/1.0",
            "export_id": str(export_id),
            "created_at": created_at.isoformat(),
            "incident_ids": [str(item) for item in incident_ids],
            "members": [item.model_dump(mode="json") for item in members],
            "source_graph_sha256": graph_digests,
            "completeness": "closed_over_declared_members",
            "secret_values_persisted": False,
            "audience": audience.value,
            "leak_scan_sha256": leak_scan_sha256,
            "authority_epoch_id": watermark_record.epoch_id,
            "authority_watermark": watermark_record.highest_contiguous_position,
            "authority_watermark_record": watermark_record.model_dump(mode="json"),
        }
        manifest = EvidenceExportManifest.model_validate({
            **base,
            "manifest_payload_sha256": export_manifest_payload_sha256(base),
        })
        manifest_bytes = canonical_json_bytes(manifest.model_dump(mode="json"))
        fd, temp_name = tempfile.mkstemp(prefix=".tmp-export-", suffix=".zip", dir=output_zip.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", manifest_bytes)
                for path, data in sorted(payloads.items()):
                    archive.writestr(path, data)
            os.replace(temp_name, output_zip)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return manifest

    def verify(self, export_zip: str | Path) -> dict[str, object]:
        errors: list[str] = []
        with zipfile.ZipFile(export_zip) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                errors.append("duplicate_member")
            for name in names:
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts:
                    errors.append(f"unsafe_member:{name}")
            if "manifest.json" not in names:
                return {"valid": False, "errors": ["manifest_missing"]}
            try:
                manifest = EvidenceExportManifest.model_validate(json.loads(archive.read("manifest.json")))
            except (ValueError, json.JSONDecodeError) as exc:
                return {"valid": False, "errors": [f"manifest_invalid:{exc}"]}
            declared = {"manifest.json", *(item.path for item in manifest.members)}
            if set(names) != declared:
                errors.append("member_closure_failed")
            for member in manifest.members:
                if member.path not in names:
                    errors.append(f"member_missing:{member.path}")
                    continue
                data = archive.read(member.path)
                if len(data) != member.bytes:
                    errors.append(f"member_size_mismatch:{member.path}")
                if sha256_bytes(data) != member.sha256:
                    errors.append(f"member_digest_mismatch:{member.path}")
                if member.classification is ArtifactClassification.SECRET_PROHIBITED:
                    errors.append(f"secret_prohibited_member:{member.path}")
            return {
                "valid": not errors,
                "errors": sorted(errors),
                "export_id": str(manifest.export_id),
                "manifest": manifest.model_dump(mode="json"),
            }
