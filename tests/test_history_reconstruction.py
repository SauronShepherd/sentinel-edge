from sentinel_edge.audit.history_reconstruction import import_history


def test_imported_history_is_explicitly_incomplete_without_authority_positions():
    history = import_history([{"event": "accepted"}], exact_authority_positions=False)
    assert history.state == "reconstructed_incomplete"
    assert history.as_metadata()["exact_authority_positions"] is False


def test_exact_import_retains_original_label():
    assert import_history([], exact_authority_positions=True).state == "original"
