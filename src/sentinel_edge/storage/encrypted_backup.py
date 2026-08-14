"""Authenticated encryption envelope for removable backup media.

The key is supplied by a separate recovery authority and is never embedded in
the backup payload or ordinary node image.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class EncryptedBackupEnvelope:
    schema: str
    recovery_key_reference: str
    nonce_b64: str
    ciphertext_b64: str

    def as_bytes(self) -> bytes:
        return (json.dumps(self.__dict__, sort_keys=True, separators=(",", ":")) + "\n").encode()


def encrypt_backup_bytes(*, backup_bytes: bytes, recovery_key: bytes,
                         recovery_key_reference: str) -> EncryptedBackupEnvelope:
    if len(recovery_key) not in (16, 24, 32) or not recovery_key_reference.strip():
        raise ValueError("separate recovery authority key and reference are required")
    nonce = os.urandom(12)
    ciphertext = AESGCM(recovery_key).encrypt(nonce, backup_bytes, recovery_key_reference.encode())
    return EncryptedBackupEnvelope("sentinel-edge-encrypted-backup/1.0", recovery_key_reference,
        base64.b64encode(nonce).decode(), base64.b64encode(ciphertext).decode())


def decrypt_backup_bytes(envelope: EncryptedBackupEnvelope, *, recovery_key: bytes) -> bytes:
    if len(recovery_key) not in (16, 24, 32):
        raise ValueError("invalid recovery authority key")
    return AESGCM(recovery_key).decrypt(
        base64.b64decode(envelope.nonce_b64, validate=True),
        base64.b64decode(envelope.ciphertext_b64, validate=True),
        envelope.recovery_key_reference.encode(),
    )
