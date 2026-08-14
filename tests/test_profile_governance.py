from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification.profile_governance import ProfileGovernance


def test_expired_profile_cannot_remain_indefinitely_under_review() -> None:
    now = datetime.now(timezone.utc)
    policy = ProfileGovernance("profile-1", "owner-1", now - timedelta(seconds=1), "abstain", "fallback-1")
    assert policy.decision(now) == "rollback:fallback-1"
