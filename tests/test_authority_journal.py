from sentinel_edge.audit.authority_journal import AuthorityJournal


def test_accepted_mutations_have_unique_ordered_positions_and_predecessor_chain() -> None:
    journal = AuthorityJournal()
    first = journal.accept()
    second = journal.accept()
    assert first != second
    assert second.predecessor == (first.epoch, first.ordinal, first.sequence)
    assert journal.verify() is True
