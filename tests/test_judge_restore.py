import pytest

from sentinel_edge.qualification.judge_restore import JudgeRestoreFixture


def test_judge_restore_runs_offline_from_synthetic_public_material() -> None:
    fixture = JudgeRestoreFixture("judge-restore-1", True, "public-key:fixture")
    assert fixture.restore_ready() is True


def test_hidden_private_decryption_requirement_is_rejected() -> None:
    with pytest.raises(ValueError, match="private decryption"):
        JudgeRestoreFixture("judge-restore-1", True, "public-key:fixture", private_decryption_requirement=True)
