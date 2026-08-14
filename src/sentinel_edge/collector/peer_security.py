"""Stable peer identity, HMAC authentication, and replay protection."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class PeerIdentity:
    peer_id: str
    issuer: str
    enrollment_method: str
    revoked: bool = False


@dataclass(frozen=True)
class PeerVerification:
    peer_id: str
    authenticated: bool
    transport_integrity: bool
    replayed: bool
    reason_code: str


class PeerTrustRegistry:
    def __init__(self, peers: dict[str, bytes]) -> None:
        self._keys = dict(peers)
        self._identities = {peer: PeerIdentity(peer, "local-root", "pre_shared_key") for peer in peers}
        self._seen: dict[str, int] = {}

    def identity(self, peer_id: str) -> PeerIdentity:
        try:
            return self._identities[peer_id]
        except KeyError as exc:
            raise ValueError("unknown_peer") from exc

    def revoke(self, peer_id: str) -> None:
        self.identity(peer_id)
        self._identities[peer_id] = self._identities[peer_id].__class__(peer_id, "local-root", "pre_shared_key", True)

    def sign(self, peer_id: str, sequence: int, payload: dict[str, object]) -> str:
        key = self._keys[peer_id]
        body = json.dumps({"peer_id": peer_id, "sequence": sequence, "payload": payload}, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(key, body, hashlib.sha256).hexdigest()

    def verify(self, peer_id: str, sequence: int, payload: dict[str, object], mac: str) -> PeerVerification:
        if peer_id not in self._keys:
            return PeerVerification(peer_id, False, False, False, "unknown_peer")
        identity = self._identities[peer_id]
        if identity.revoked:
            return PeerVerification(peer_id, False, False, False, "peer_revoked")
        if sequence <= self._seen.get(peer_id, -1):
            return PeerVerification(peer_id, False, True, True, "replay_rejected")
        expected = self.sign(peer_id, sequence, payload)
        if not hmac.compare_digest(expected, mac):
            return PeerVerification(peer_id, False, True, False, "authentication_failed")
        self._seen[peer_id] = sequence
        return PeerVerification(peer_id, True, True, False, "authenticated")

    def multi_node_trigger_allowed(self, verifications: tuple[PeerVerification, ...]) -> bool:
        return len(verifications) >= 2 and all(item.authenticated and not item.replayed for item in verifications)
