from sentinel_edge.collaboration.privacy import location_trust_decision


def test_exact_location_does_not_verify_source():
    assert location_trust_decision(location_present=True, source_verified=False) == (False, "location_cannot_verify_source")


def test_independent_source_verification_is_separate_from_location():
    assert location_trust_decision(location_present=True, source_verified=True) == (True, "source_verified_independently")
