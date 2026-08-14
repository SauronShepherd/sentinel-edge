from sentinel_edge.security.identifier_authority import IdentifierKind, IdentifierRef, authorize_by_identifier


def test_all_identifier_kinds_are_non_authoritative() -> None:
    for kind in IdentifierKind:
        identifier = IdentifierRef(kind, "opaque-value")
        assert identifier.grants_capability() is False
        assert authorize_by_identifier(identifier) is False
