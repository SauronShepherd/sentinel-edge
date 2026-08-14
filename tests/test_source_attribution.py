from sentinel_edge.qualification import load_source_observation, load_source_policy, qualify_source


def test_source_health_exposes_attribution_and_license() -> None:
    policy = load_source_policy("fixtures/sources/meteoalarm-fixture.policy.json")
    observation = load_source_observation("fixtures/sources/meteoalarm-fixture.observation.json")
    report = qualify_source(policy, observation)
    assert report.attribution == policy.owner
    assert report.license_id == policy.license_id
    assert report.canonical_url == policy.canonical_url
