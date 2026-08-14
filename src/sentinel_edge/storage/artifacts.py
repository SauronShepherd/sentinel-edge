from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sentinel_edge.domain.models import HealthState
from sentinel_edge.storage.health import StorageHealthReport, inspect_storage
from sentinel_edge.storage.artifact_governance import (
    ArtifactBudgetPolicy, ArtifactCatalog, ArtifactPolicy, ArtifactReferenceKind, ArtifactScope,
)


@dataclass(frozen=True)
class ArtifactRef:
    sha256: str
    relative_path: str
    bytes: int
    media_type: str


class ContentAddressedArtifactStore:
    """Atomic content-addressed evidence store with a critical reserve and visible health."""

    def __init__(
        self,
        root: str | Path,
        *,
        max_bytes: int = 64 * 1024 * 1024,
        reserve_bytes: int = 1024 * 1024,
        budget_policy: ArtifactBudgetPolicy | None = None,
    ) -> None:
        if max_bytes <= 0 or reserve_bytes < 0 or reserve_bytes >= max_bytes:
            raise ValueError("artifact capacity budget is invalid")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.metadata_root = self.root / ".metadata"
        self.metadata_root.mkdir(exist_ok=True)
        self.catalog = ArtifactCatalog(self.metadata_root / "artifacts.sqlite3", budgets=budget_policy)
        self.max_bytes = max_bytes
        self.reserve_bytes = reserve_bytes
        self._forced_read_only = False
        self._last_failure: str | None = None

    def close(self) -> None:
        """Release the catalog connection before its backing directory is removed."""
        self.catalog.close()

    def __enter__(self) -> "ContentAddressedArtifactStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        # Scenario fixtures may be garbage-collected after their TemporaryDirectory
        # finalizer has started; closing here prevents Windows file-lock warnings.
        try:
            self.close()
        except Exception:
            pass

    def _used_bytes(self) -> int:
        return sum(
            path.stat().st_size
            for path in self.root.rglob("*")
            if path.is_file() and ".tmp-" not in path.name and ".quarantine" not in path.parts and ".metadata" not in path.parts
        )

    def set_read_only(self, value: bool = True) -> None:
        self._forced_read_only = value
        if value:
            self._last_failure = "medium_read_only_or_unwritable"

    def health(self) -> StorageHealthReport:
        report = inspect_storage(
            self.root,
            configured_max_bytes=self.max_bytes,
            reserve_bytes=self.reserve_bytes,
            forced_read_only=self._forced_read_only,
        )
        used = self._used_bytes()
        if self._last_failure and self._last_failure not in report.reason_codes:
            return StorageHealthReport(
                state=HealthState.FAILED if self._forced_read_only else HealthState.DEGRADED,
                path=report.path,
                writable=report.writable,
                total_bytes=report.total_bytes,
                free_bytes=report.free_bytes,
                used_bytes=used,
                configured_max_bytes=report.configured_max_bytes,
                reserve_bytes=report.reserve_bytes,
                reason_codes=tuple(sorted(set(report.reason_codes + (self._last_failure,)))),
            )
        if report.state is HealthState.HEALTHY and used > self.max_bytes - self.reserve_bytes:
            return StorageHealthReport(
                state=HealthState.DEGRADED,
                path=report.path,
                writable=report.writable,
                total_bytes=report.total_bytes,
                free_bytes=report.free_bytes,
                used_bytes=used,
                configured_max_bytes=self.max_bytes,
                reserve_bytes=self.reserve_bytes,
                reason_codes=("artifact_reserve_in_use",),
            )
        return StorageHealthReport(
            state=report.state,
            path=report.path,
            writable=report.writable,
            total_bytes=report.total_bytes,
            free_bytes=report.free_bytes,
            used_bytes=used,
            configured_max_bytes=self.max_bytes,
            reserve_bytes=self.reserve_bytes,
            reason_codes=report.reason_codes,
        )

    def usage_report(self) -> dict[str, int | str | bool | tuple[str, ...]]:
        health = self.health()
        return {
            "state": health.state.value,
            "writable": health.writable,
            "used_bytes": health.used_bytes,
            "maximum_bytes": self.max_bytes,
            "reserve_bytes": self.reserve_bytes,
            "noncritical_budget_remaining_bytes": max(0, self.max_bytes - self.reserve_bytes - health.used_bytes),
            "critical_budget_remaining_bytes": max(0, self.max_bytes - health.used_bytes),
            "reason_codes": health.reason_codes,
        }

    def put_bytes(
        self,
        data: bytes,
        *,
        media_type: str = "application/octet-stream",
        critical: bool = False,
        policy: ArtifactPolicy,
        scope: ArtifactScope | None = None,
    ) -> ArtifactRef:
        if self._forced_read_only:
            raise OSError("artifact medium is read-only")
        scope = scope or ArtifactScope()
        digest = hashlib.sha256(data).hexdigest()
        relative = Path(digest[:2]) / digest[2:]
        destination = self.root / relative
        if destination.exists():
            existing = destination.read_bytes()
            if hashlib.sha256(existing).hexdigest() != digest:
                raise RuntimeError("content-address collision")
            self.catalog.register(
                sha256=digest, relative_path=relative.as_posix(), bytes_count=len(existing), media_type=media_type,
                policy=policy, scope=scope, critical=critical,
            )
            return ArtifactRef(digest, relative.as_posix(), len(existing), media_type)
        used = self._used_bytes()
        limit = self.max_bytes if critical else self.max_bytes - self.reserve_bytes
        if used + len(data) > limit:
            self._last_failure = "artifact_capacity_exhausted" if critical else "artifact_capacity_reserve_would_be_violated"
            raise OSError("artifact capacity exhausted" if critical else "artifact capacity reserve would be violated")
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".tmp-{digest[:12]}-", dir=destination.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, destination)
            # Durably publish the directory entry where the platform supports it.
            try:
                directory_fd = os.open(destination.parent, os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except (AttributeError, OSError):
                pass
        except OSError as exc:
            self._last_failure = f"artifact_write_failed:{type(exc).__name__}"
            raise
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        self.catalog.register(
            sha256=digest, relative_path=relative.as_posix(), bytes_count=len(data), media_type=media_type,
            policy=policy, scope=scope, critical=critical,
        )
        return ArtifactRef(digest, relative.as_posix(), len(data), media_type)

    def read_bytes(self, digest: str) -> bytes:
        """Read a content-addressed object only when its digest still matches."""
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("artifact digest must be a lowercase SHA-256 value")
        path = self.root / digest[:2] / digest[2:]
        if not path.is_file():
            raise FileNotFoundError(f"artifact not found for digest {digest}")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError("artifact digest mismatch after reference")
        return data

    def verify(self, ref: ArtifactRef) -> bool:
        path = self.root / ref.relative_path
        return path.is_file() and path.stat().st_size == ref.bytes and hashlib.sha256(path.read_bytes()).hexdigest() == ref.sha256


    def delete_digest(
        self,
        digest: str,
        *,
        actor: str = "artifact-delete",
        tombstone_authorized: bool = False,
        force: bool = False,
    ) -> dict[str, object]:
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
            raise ValueError("digest must be a lowercase SHA-256 hex value")
        relative = Path(digest[:2]) / digest[2:]
        path = self.root / relative
        try:
            policy = self.catalog.effective_policy(digest)
            blockers = list(self.catalog.references(digest))
            if blockers and not force:
                raise PermissionError("artifact deletion blocked by active references")
            if policy.deletion_policy.value == "tombstone_required" and not tombstone_authorized and not force:
                raise PermissionError("artifact deletion requires tombstone authorization")
            if policy.deletion_policy.value in {"hold_protected", "manual_only"} and not force:
                raise PermissionError(f"artifact deletion blocked by policy {policy.deletion_policy.value}")
        except KeyError:
            policy = None
        existed = path.is_file()
        bytes_removed = path.stat().st_size if existed else 0
        if existed:
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
            if observed != digest:
                raise RuntimeError("artifact digest mismatch before deletion")
            path.unlink()
            try:
                directory_fd = os.open(path.parent, os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except (AttributeError, OSError):
                pass
            try:
                path.parent.rmdir()
            except OSError:
                pass
        proof_payload = f"sentinel-artifact-delete-v1:{digest}:{int(existed)}:{bytes_removed}".encode("utf-8")
        result = {
            "artifact_sha256": digest,
            "existed": existed,
            "bytes_removed": bytes_removed,
            "deletion_proof_sha256": hashlib.sha256(proof_payload).hexdigest(),
            "relative_path": relative.as_posix(),
            "policy": policy.model_dump(mode="json") if policy is not None else None,
        }
        if policy is not None:
            self.catalog.record_gc_event(
                digest, action="deleted" if existed else "already_absent", actor=actor,
                reason_codes=("tombstone_authorized",) if tombstone_authorized else ("forced",) if force else ("policy_allowed",),
            )
        return result

    def add_reference(self, digest: str, *, kind: ArtifactReferenceKind, owner: str, reason: str, expires_at: datetime | None = None) -> Any:
        return self.catalog.add_reference(digest, kind=kind, owner=owner, reason=reason, expires_at=expires_at)

    def collect_garbage(self, *, actor: str = "artifact-gc", now: datetime | None = None) -> dict[str, object]:
        now = now or __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        deleted: list[str] = []
        blocked: dict[str, list[str]] = {}
        for digest in sorted({item.sha256 for item in self.catalog.records()}):
            policy = self.catalog.effective_policy(digest)
            if policy.retention_expires_at is None or policy.retention_expires_at > now:
                continue
            blockers = self.catalog.deletion_blockers(digest, now=now)
            if blockers:
                blocked[digest] = list(blockers)
                continue
            try:
                self.delete_digest(digest, actor=actor)
                deleted.append(digest)
            except PermissionError as exc:
                blocked[digest] = [str(exc)]
        return {"deleted": deleted, "blocked": blocked, "evaluated_at": now.isoformat()}

    def quarantine_incomplete(self) -> tuple[str, ...]:
        quarantined: list[str] = []
        quarantine = self.root / ".quarantine"
        quarantine.mkdir(exist_ok=True)
        candidates = [path for path in self.root.rglob(".tmp-*") if quarantine not in path.parents]
        for path in candidates:
            target = quarantine / path.name
            os.replace(path, target)
            quarantined.append(target.relative_to(self.root).as_posix())
        return tuple(sorted(quarantined))
