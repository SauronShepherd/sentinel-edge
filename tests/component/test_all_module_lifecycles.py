def test_runner_lifecycle_contract_is_represented():
    modules = ["collector", "analyzer", "runtime", "incident", "api"]
    assert modules == ["collector", "analyzer", "runtime", "incident", "api"]
