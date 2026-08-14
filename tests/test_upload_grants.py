from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification.upload_grants import UploadGrantAuthority


def test_upload_grant_is_scoped_single_use_same_boot_and_expiring() -> None:
    now = datetime(2026, 8, 13, tzinfo=timezone.utc)
    authority = UploadGrantAuthority(boot_id="boot-a")
    grant = authority.issue(principal_id="user-a", scope="evidence:upload", expires_at=now + timedelta(minutes=1), max_bytes=1024)
    assert authority.consume(grant.grant_id, principal_id="user-a", scope="wrong", now=now).code == "grant_scope_mismatch"
    accepted = authority.consume(grant.grant_id, principal_id="user-a", scope="evidence:upload", now=now)
    assert accepted.accepted
    assert authority.consume(grant.grant_id, principal_id="user-a", scope="evidence:upload", now=now).code == "grant_already_consumed"


def test_upload_grant_rejects_wrong_principal_and_expiry() -> None:
    now = datetime(2026, 8, 13, tzinfo=timezone.utc)
    authority = UploadGrantAuthority(boot_id="boot-a")
    grant = authority.issue(principal_id="user-a", scope="upload", expires_at=now, max_bytes=1)
    assert authority.consume(grant.grant_id, principal_id="user-b", scope="upload", now=now).code == "grant_principal_mismatch"
    assert authority.consume(grant.grant_id, principal_id="user-a", scope="upload", now=now).code == "grant_expired"


def test_upload_grant_is_invalid_after_reboot() -> None:
    now = datetime(2026, 8, 13, tzinfo=timezone.utc)
    first_boot = UploadGrantAuthority(boot_id="boot-a")
    grant = first_boot.issue(principal_id="user-a", scope="upload", expires_at=now + timedelta(minutes=1), max_bytes=1)
    second_boot = UploadGrantAuthority(boot_id="boot-b")
    second_boot._grants[grant.grant_id] = grant
    assert second_boot.consume(grant.grant_id, principal_id="user-a", scope="upload", now=now).code == "grant_boot_mismatch"
