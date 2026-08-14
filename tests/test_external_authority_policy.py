import pytest

from sentinel_edge.qualification.external_authority import (
    DocumentedAuthorityEndpoint, resolve_documented_authority,
)


def test_funvisis_documented_endpoint_is_reference_only() -> None:
    endpoint = DocumentedAuthorityEndpoint(
        authority="FUNVISIS", endpoint="https://www.funvisis.gob.ve/catalog",
        documentation_url="https://www.funvisis.gob.ve/",)
    allowed = resolve_documented_authority(endpoint, requested_endpoint=endpoint.endpoint)
    assert allowed.permitted is True
    assert allowed.reference_only is True
    assert allowed.reason == "documented_endpoint_allowlisted"


def test_undocumented_funvisis_endpoint_is_rejected() -> None:
    endpoint = DocumentedAuthorityEndpoint(
        authority="FUNVISIS", endpoint="https://www.funvisis.gob.ve/catalog",
        documentation_url="https://www.funvisis.gob.ve/",)
    denied = resolve_documented_authority(endpoint, requested_endpoint="https://evil.example/api")
    assert denied.permitted is False
    assert denied.reason == "undocumented_endpoint_rejected"


def test_authority_endpoint_requires_https_documentation() -> None:
    with pytest.raises(ValueError):
        DocumentedAuthorityEndpoint(authority="FUNVISIS", endpoint="http://bad", documentation_url="https://docs")
