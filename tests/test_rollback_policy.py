from sentinel_edge.update.rollback_policy import UpdateBundle, evaluate_update


def bundle(version, floor=1, digest=None):
    return UpdateBundle("application", version, floor, digest or f"d{version}")


def test_older_vulnerable_update_is_rejected():
    result = evaluate_update(active=bundle(3, 3), candidate=bundle(2), canary_passed=True)
    assert (result.accepted, result.reason) == (False, "anti_rollback_floor")


def test_failed_canary_restores_last_known_good():
    result = evaluate_update(active=bundle(3), candidate=bundle(4), canary_passed=False)
    assert result.action == "restore_last_known_good"
