from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification.upload_admission import UploadAdmission, create_upload_session
from sentinel_edge.qualification.upload_grants import UploadGrantAuthority


def test_upload_session_is_created_only_after_all_admission_controls() -> None:
    now = datetime(2026, 8, 13, tzinfo=timezone.utc)
    authority = UploadGrantAuthority(boot_id="boot")
    allowed = UploadAdmission(True, True, True, True, True)
    grant = create_upload_session(authority=authority, principal_id="p", scope="upload", expires_at=now + timedelta(minutes=1), max_bytes=10, admission=allowed)
    assert grant is not None
    for field in ("authenticated", "authorized", "quota_available", "consent_valid", "source_policy_allowed"):
        denied = allowed.__class__(**{**allowed.__dict__, field: False})
        assert create_upload_session(authority=authority, principal_id="p", scope="upload", expires_at=now + timedelta(minutes=1), max_bytes=10, admission=denied) is None
