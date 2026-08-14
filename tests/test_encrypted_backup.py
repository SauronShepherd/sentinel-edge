import pytest

from sentinel_edge.storage.encrypted_backup import decrypt_backup_bytes, encrypt_backup_bytes


def test_encrypted_backup_hides_content_and_requires_separate_recovery_key() -> None:
    plaintext = b"restricted/private evidence"
    key = b"r" * 32
    envelope = encrypt_backup_bytes(backup_bytes=plaintext, recovery_key=key,
        recovery_key_reference="recovery-authority:v3")
    assert plaintext not in envelope.as_bytes()
    assert decrypt_backup_bytes(envelope, recovery_key=key) == plaintext
    with pytest.raises(Exception):
        decrypt_backup_bytes(envelope, recovery_key=b"x" * 32)


def test_encryption_requires_key_reference_and_does_not_accept_node_secret_shape() -> None:
    with pytest.raises(ValueError):
        encrypt_backup_bytes(backup_bytes=b"x", recovery_key=b"k" * 32, recovery_key_reference="")
