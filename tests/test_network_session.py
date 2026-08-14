import pytest

from sentinel_edge.security.network_session import NetworkMode, NetworkModeSessionGuard


def test_network_mode_change_expires_existing_write_session() -> None:
    guard = NetworkModeSessionGuard()
    lease = guard.issue("admin")
    guard.authorize_write(lease)
    assert guard.change_mode(NetworkMode.TRUSTED_LAN) == 1
    with pytest.raises(PermissionError, match="revalidation"):
        guard.authorize_write(lease)
    refreshed = guard.issue("admin")
    guard.authorize_write(refreshed)


def test_same_mode_does_not_rotate_epoch() -> None:
    guard = NetworkModeSessionGuard(NetworkMode.TRUSTED_LAN)
    assert guard.change_mode(NetworkMode.TRUSTED_LAN) == 0
