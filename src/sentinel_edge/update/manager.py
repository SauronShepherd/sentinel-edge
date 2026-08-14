from __future__ import annotations

import base64
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from sentinel_edge.domain.models import (
    OfflineUpdateMetadata,
    OfflineUpdateTarget,
    OfflineUpdateVerification,
    RuntimeMode,
    UpdateBundleState,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file
from sentinel_edge.privacy import build_tombstone_journal
from sentinel_edge.storage.sqlite_store import IncidentJournalStore

_METADATA = "metadata.json"
_SIGNATURE = "metadata.ed25519"
_ALLOWED_CONTROL_FILES = {_METADATA, _SIGNATURE}
_PROTECTED_TARGET_PREFIXES = ("artifacts/", "evidence/", "backups/", "privacy/", "state/")


def _version_tuple(value: str) -> tuple[int, ...]:
    try:
        parts = value.split("+")[0].split("-")[0].split(".")
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise ValueError(f"invalid semantic version: {value}") from exc


def key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return sha256_bytes(raw)[:32]


def generate_keypair(private_path: str | Path, public_path: str | Path) -> tuple[Path, Path]:
    private = Ed25519PrivateKey.generate()
    private_path = Path(private_path)
    public_path = Path(public_path)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    os.chmod(private_path, 0o600)
    public_path.write_bytes(
        private.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path, public_path


def load_private_key(path: str | Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("update signing key is not Ed25519")
    return key


def load_public_key(path: str | Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(Path(path).read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("update verification key is not Ed25519")
    return key


def build_update_bundle(
    output: str | Path,
    *,
    source_root: str | Path,
    target_paths: Iterable[str],
    private_key: Ed25519PrivateKey,
    bundle_id: str,
    version: int,
    created_at: datetime,
    expires_at: datetime,
    compatible_min_version: str,
    compatible_max_version: str,
    minimum_tombstone_authority_position: int = 0,
    required_tombstone_journal_sha256: str | None = None,
) -> Path:
    source_root = Path(source_root).resolve()
    targets: list[OfflineUpdateTarget] = []
    normalized_paths: list[str] = []
    for raw in sorted(set(target_paths)):
        target = OfflineUpdateTarget(path=raw, length=0, sha256="0" * 64)
        path = (source_root / target.path).resolve()
        try:
            path.relative_to(source_root)
        except ValueError as exc:
            raise ValueError("update target escapes source root") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        if target.path.startswith(_PROTECTED_TARGET_PREFIXES):
            raise ValueError("update targets cannot overwrite protected state, evidence, backup, or privacy paths")
        normalized_paths.append(target.path)
        targets.append(OfflineUpdateTarget(path=target.path, length=path.stat().st_size, sha256=sha256_file(path)))
    metadata = OfflineUpdateMetadata(
        bundle_id=bundle_id,
        version=version,
        created_at=created_at,
        expires_at=expires_at,
        compatible_min_version=compatible_min_version,
        compatible_max_version=compatible_max_version,
        targets=tuple(targets),
        root_key_id=key_id(private_key.public_key()),
        minimum_tombstone_authority_position=minimum_tombstone_authority_position,
        required_tombstone_journal_sha256=required_tombstone_journal_sha256,
    )
    metadata_bytes = canonical_json_bytes(metadata.model_dump(mode="json"))
    signature = private_key.sign(metadata_bytes)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(_METADATA, metadata_bytes)
        archive.writestr(_SIGNATURE, base64.b64encode(signature))
        for relative in normalized_paths:
            archive.write(source_root / relative, arcname=relative)
    return output


class OfflineUpdateManager:
    """TUF-inspired offline bundle verification and activation pointer manager.

    This does not replace an OS package manager or verified boot. It proves exact
    application bundle identity and safely stages an already-approved field-lab update.
    """

    def __init__(
        self,
        state_dir: str | Path,
        public_key: Ed25519PublicKey,
        *,
        current_project_version: str,
        mode: RuntimeMode,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.public_key = public_key
        self.current_project_version = current_project_version
        self.mode = mode
        self.update_root = self.state_dir / "updates"
        self.staged_root = self.update_root / "staged"
        self.activated_root = self.update_root / "activated"
        self.pointer_path = self.update_root / "active.json"
        self.staged_root.mkdir(parents=True, exist_ok=True)
        self.activated_root.mkdir(parents=True, exist_ok=True)

    def current_update_version(self) -> int:
        if not self.pointer_path.exists():
            return 0
        return int(json.loads(self.pointer_path.read_text(encoding="utf-8"))["version"])

    def _current_tombstone_status(self) -> tuple[int, str]:
        incidents_path = self.state_dir / "incidents.sqlite3"
        if not incidents_path.is_file():
            return 0, sha256_bytes(canonical_json_bytes({"schema": "sentinel-edge-privacy-tombstones/empty"}))
        journal = build_tombstone_journal(IncidentJournalStore(incidents_path))
        return journal.source_authority_position, journal.payload_sha256

    def _verify_tombstone_requirement(self, metadata: OfflineUpdateMetadata) -> tuple[str, ...]:
        current_position, current_digest = self._current_tombstone_status()
        if current_position < metadata.minimum_tombstone_authority_position:
            raise ValueError("update requires a newer privacy tombstone watermark")
        if (
            metadata.required_tombstone_journal_sha256 is not None
            and current_position == metadata.minimum_tombstone_authority_position
            and current_digest != metadata.required_tombstone_journal_sha256
        ):
            raise ValueError("update tombstone journal digest does not match the required watermark")
        return (
            f"tombstone_position:{current_position}",
            "tombstone_requirement_satisfied",
        )

    def verify(self, bundle_path: str | Path, *, now: datetime | None = None) -> tuple[OfflineUpdateMetadata, OfflineUpdateVerification]:
        now = now or datetime.now(timezone.utc)
        reasons: list[str] = []
        with zipfile.ZipFile(bundle_path, "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("update bundle contains duplicate archive members")
            for name in names:
                safe = OfflineUpdateTarget(path=name, length=0, sha256="0" * 64).path
                if safe != name:
                    raise ValueError("update archive member is not canonical")
            if _METADATA not in names or _SIGNATURE not in names:
                raise ValueError("update bundle is missing signed metadata")
            metadata_bytes = archive.read(_METADATA)
            try:
                signature = base64.b64decode(archive.read(_SIGNATURE), validate=True)
                self.public_key.verify(signature, metadata_bytes)
            except (InvalidSignature, ValueError) as exc:
                raise ValueError("update metadata signature is invalid") from exc
            metadata = OfflineUpdateMetadata.model_validate(json.loads(metadata_bytes))
            if key_id(self.public_key) != metadata.root_key_id:
                raise ValueError("update root key identifier mismatch")
            if canonical_json_bytes(metadata.model_dump(mode="json")) != metadata_bytes:
                raise ValueError("update metadata is not canonical")
            if metadata.expires_at <= now:
                raise ValueError("update metadata is expired")
            if metadata.created_at > now:
                raise ValueError("update metadata creation time is in the future")
            current = _version_tuple(self.current_project_version)
            if current < _version_tuple(metadata.compatible_min_version) or current > _version_tuple(metadata.compatible_max_version):
                raise ValueError("update bundle is incompatible with the current project version")
            if metadata.version <= self.current_update_version():
                raise ValueError("update rollback or replay detected")
            declared = {item.path for item in metadata.targets}
            extras = set(names) - declared - _ALLOWED_CONTROL_FILES
            missing = declared - set(names)
            if extras or missing:
                raise ValueError("update archive members differ from signed targets")
            for target in metadata.targets:
                if target.path.startswith(_PROTECTED_TARGET_PREFIXES):
                    raise ValueError("update metadata targets a protected state or privacy path")
                data = archive.read(target.path)
                if len(data) != target.length or sha256_bytes(data) != target.sha256:
                    raise ValueError(f"update target verification failed: {target.path}")
            reasons.extend(("ed25519_signature_valid", "expiry_valid", "rollback_check_passed", "targets_verified"))
            reasons.extend(self._verify_tombstone_requirement(metadata))
        verification = OfflineUpdateVerification(
            bundle_id=metadata.bundle_id,
            version=metadata.version,
            state=UpdateBundleState.VERIFIED,
            verified_at=now,
            metadata_sha256=sha256_bytes(metadata_bytes),
            signer_key_id=metadata.root_key_id,
            reason_codes=tuple(reasons),
        )
        return metadata, verification

    def stage(self, bundle_path: str | Path, *, now: datetime | None = None) -> tuple[Path, OfflineUpdateVerification]:
        if self.mode in {RuntimeMode.JUDGE, RuntimeMode.BENCHMARK}:
            raise PermissionError("judge and benchmark modes are immutable")
        metadata, verification = self.verify(bundle_path, now=now)
        destination = self.staged_root / f"{metadata.bundle_id}-{metadata.version}"
        if destination.exists():
            shutil.rmtree(destination)
        temp = Path(tempfile.mkdtemp(prefix="sentinel-update-", dir=self.staged_root))
        try:
            with zipfile.ZipFile(bundle_path, "r") as archive:
                for target in metadata.targets:
                    path = temp / target.path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read(target.path))
                    if sha256_file(path) != target.sha256:
                        raise ValueError("staged target digest mismatch")
            (temp / _METADATA).write_bytes(canonical_json_bytes(metadata.model_dump(mode="json")))
            os.replace(temp, destination)
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise
        return destination, verification.model_copy(update={"state": UpdateBundleState.STAGED})

    def activate(
        self,
        staged_path: str | Path,
        *,
        self_test: Callable[[Path], bool],
        now: datetime | None = None,
    ) -> OfflineUpdateVerification:
        if self.mode is not RuntimeMode.FIELD_LAB:
            raise PermissionError("offline update activation is field-lab only")
        now = now or datetime.now(timezone.utc)
        staged_path = Path(staged_path).resolve()
        try:
            staged_path.relative_to(self.staged_root.resolve())
        except ValueError as exc:
            raise ValueError("staged update is outside the update root") from exc
        metadata = OfflineUpdateMetadata.model_validate(json.loads((staged_path / _METADATA).read_text(encoding="utf-8")))
        self._verify_tombstone_requirement(metadata)
        if metadata.version <= self.current_update_version():
            raise ValueError("update rollback or replay detected")
        for target in metadata.targets:
            path = staged_path / target.path
            if not path.is_file() or path.stat().st_size != target.length or sha256_file(path) != target.sha256:
                raise ValueError("staged update target no longer matches signed metadata")
        if not self_test(staged_path):
            return OfflineUpdateVerification(
                bundle_id=metadata.bundle_id,
                version=metadata.version,
                state=UpdateBundleState.ROLLED_BACK,
                verified_at=now,
                metadata_sha256=sha256_file(staged_path / _METADATA),
                signer_key_id=metadata.root_key_id,
                reason_codes=("self_test_failed", "previous_active_pointer_preserved"),
            )
        activated = self.activated_root / f"{metadata.bundle_id}-{metadata.version}"
        if activated.exists():
            shutil.rmtree(activated)
        shutil.copytree(staged_path, activated)
        pointer = {
            "bundle_id": metadata.bundle_id,
            "version": metadata.version,
            "path": activated.relative_to(self.state_dir).as_posix(),
            "metadata_sha256": sha256_file(activated / _METADATA),
            "activated_at": now.isoformat(),
        }
        temp_pointer = self.pointer_path.with_suffix(".tmp")
        temp_pointer.write_text(json.dumps(pointer, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # Keep the descriptor writable on Windows; fsync on a read-only
        # pathlib handle can fail with EBADF even after the file was written.
        with temp_pointer.open("r+b") as handle:
            os.fsync(handle.fileno())
        os.replace(temp_pointer, self.pointer_path)
        return OfflineUpdateVerification(
            bundle_id=metadata.bundle_id,
            version=metadata.version,
            state=UpdateBundleState.ACTIVATED,
            verified_at=now,
            metadata_sha256=pointer["metadata_sha256"],
            signer_key_id=metadata.root_key_id,
            reason_codes=("self_test_passed", "activation_pointer_committed"),
        )
