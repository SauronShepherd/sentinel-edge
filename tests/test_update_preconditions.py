import pytest

from sentinel_edge.update.preconditions import ActivationPreconditions


def test_all_activation_preconditions_must_pass() -> None:
    assert ActivationPreconditions(True, True, True).require_safe() == ("power_ok", "storage_ok", "compatibility_ok")


@pytest.mark.parametrize("field", ["power_ok", "storage_ok", "compatible"])
def test_unsafe_precondition_fails_closed(field: str) -> None:
    values = {"power_ok": True, "storage_ok": True, "compatible": True}
    values[field] = False
    with pytest.raises(ValueError, match="activation preconditions failed"):
        ActivationPreconditions(**values).require_safe()
