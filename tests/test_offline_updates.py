from datetime import datetime, timedelta, timezone
from pathlib import Path
import zipfile
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.domain.models import RuntimeMode, UpdateBundleState
from sentinel_edge.update import OfflineUpdateManager, build_update_bundle


def make_bundle(tmp_path: Path, *, version: int = 1, expires_delta: timedelta = timedelta(days=1)) -> Any:
    source = tmp_path / "source"
    target = source / "src" / "sentinel_edge" / "__init__.py"
    target.parent.mkdir(parents=True)
    target.write_text('__version__ = "0.4.1"\n', encoding="utf-8")
    private = Ed25519PrivateKey.generate()
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    bundle = build_update_bundle(
        tmp_path / f"update-{version}.zip",
        source_root=source,
        target_paths=["src/sentinel_edge/__init__.py"],
        private_key=private,
        bundle_id="sentinel-field-update",
        version=version,
        created_at=now,
        expires_at=now + expires_delta,
        compatible_min_version="0.4.0",
        compatible_max_version="0.4.9",
    )
    return bundle, private, now


def test_signed_update_verifies_stages_activates_and_blocks_rollback(tmp_path: Path) -> None:
    bundle, private, now = make_bundle(tmp_path)
    manager = OfflineUpdateManager(
        tmp_path / "state",
        private.public_key(),
        current_project_version="0.4.0",
        mode=RuntimeMode.FIELD_LAB,
    )
    metadata, verified = manager.verify(bundle, now=now + timedelta(minutes=1))
    assert metadata.version == 1
    assert verified.state is UpdateBundleState.VERIFIED
    staged, stage_receipt = manager.stage(bundle, now=now + timedelta(minutes=1))
    assert stage_receipt.state is UpdateBundleState.STAGED
    result = manager.activate(staged, self_test=lambda root: (root / "src/sentinel_edge/__init__.py").is_file(), now=now + timedelta(minutes=2))
    assert result.state is UpdateBundleState.ACTIVATED
    assert manager.current_update_version() == 1
    with pytest.raises(ValueError, match="rollback or replay"):
        manager.verify(bundle, now=now + timedelta(minutes=3))


def test_update_rejects_tamper_expiry_wrong_key_and_immutable_modes(tmp_path: Path) -> None:
    bundle, private, now = make_bundle(tmp_path)
    judge = OfflineUpdateManager(
        tmp_path / "judge",
        private.public_key(),
        current_project_version="0.4.0",
        mode=RuntimeMode.JUDGE,
    )
    with pytest.raises(PermissionError, match="immutable"):
        judge.stage(bundle, now=now + timedelta(minutes=1))

    wrong = OfflineUpdateManager(
        tmp_path / "wrong",
        Ed25519PrivateKey.generate().public_key(),
        current_project_version="0.4.0",
        mode=RuntimeMode.FIELD_LAB,
    )
    with pytest.raises(ValueError, match="signature"):
        wrong.verify(bundle, now=now + timedelta(minutes=1))

    expired_bundle, private2, created = make_bundle(tmp_path / "expired", expires_delta=timedelta(minutes=1))
    expired = OfflineUpdateManager(
        tmp_path / "expired-state",
        private2.public_key(),
        current_project_version="0.4.0",
        mode=RuntimeMode.FIELD_LAB,
    )
    with pytest.raises(ValueError, match="expired"):
        expired.verify(expired_bundle, now=created + timedelta(minutes=2))

    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(bundle, "r") as original, zipfile.ZipFile(tampered, "w") as changed:
        for name in original.namelist():
            data = original.read(name)
            if name.endswith("__init__.py"):
                data += b"# tampered\n"
            changed.writestr(name, data)
    manager = OfflineUpdateManager(
        tmp_path / "tampered-state",
        private.public_key(),
        current_project_version="0.4.0",
        mode=RuntimeMode.FIELD_LAB,
    )
    with pytest.raises(ValueError, match="target verification"):
        manager.verify(tampered, now=now + timedelta(minutes=1))


def test_failed_update_self_test_preserves_active_pointer(tmp_path: Path) -> None:
    bundle, private, now = make_bundle(tmp_path)
    manager = OfflineUpdateManager(
        tmp_path / "state",
        private.public_key(),
        current_project_version="0.4.0",
        mode=RuntimeMode.FIELD_LAB,
    )
    staged, _ = manager.stage(bundle, now=now + timedelta(minutes=1))
    result = manager.activate(staged, self_test=lambda root: False, now=now + timedelta(minutes=2))
    assert result.state is UpdateBundleState.ROLLED_BACK
    assert manager.current_update_version() == 0
    assert not manager.pointer_path.exists()
