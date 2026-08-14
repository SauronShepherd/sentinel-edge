import pytest

from sentinel_edge.security.admin_bootstrap import LocalAdminBootstrap


def test_admin_bootstrap_and_recovery_are_local_physical_and_audited() -> None:
    manager = LocalAdminBootstrap()
    first = manager.bootstrap(actor="operator-1", physical_presence=True)
    second = manager.recover(actor="operator-1", physical_presence=True)
    assert first != second
    assert [item.action for item in manager.audit()] == ["bootstrap", "recovery"]
    assert all(item.physical_presence for item in manager.audit())
    assert all(len(item.token_digest) == 64 for item in manager.audit())


def test_bootstrap_rejects_remote_or_repeated_setup() -> None:
    manager = LocalAdminBootstrap()
    with pytest.raises(PermissionError):
        manager.bootstrap(actor="remote", physical_presence=False)
    manager.bootstrap(actor="local", physical_presence=True)
    with pytest.raises(RuntimeError):
        manager.bootstrap(actor="local", physical_presence=True)
    with pytest.raises(PermissionError):
        manager.recover(actor="remote", physical_presence=False)
