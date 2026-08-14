from sentinel_edge.collector.peer_security import PeerTrustRegistry


def test_peer_authentication_identity_and_replay() -> None:
    registry = PeerTrustRegistry({"node-a": b"a-secret", "node-b": b"b-secret"})
    payload = {"trigger": True}
    mac = registry.sign("node-a", 1, payload)
    first = registry.verify("node-a", 1, payload, mac)
    assert first.authenticated is True
    assert registry.verify("node-a", 1, payload, mac).reason_code == "replay_rejected"
    assert registry.verify("spoofed", 1, payload, "x").reason_code == "unknown_peer"
    assert registry.multi_node_trigger_allowed((first,)) is False


def test_corruption_is_not_authentication_and_revocation_blocks() -> None:
    registry = PeerTrustRegistry({"node-a": b"a-secret"})
    payload = {"trigger": True}
    assert registry.verify("node-a", 1, payload, "00").reason_code == "authentication_failed"
    registry.revoke("node-a")
    assert registry.verify("node-a", 2, payload, registry.sign("node-a", 2, payload)).reason_code == "peer_revoked"
