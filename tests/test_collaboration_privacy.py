import pytest

from sentinel_edge.collaboration import coarsen_domain, pseudonymous_node_id


def test_privacy_transformer_returns_opaque_domain_and_pseudonym():
    domain = coarsen_domain(kind="spatial_cell", latitude=40.4168, longitude=-3.7038)
    assert domain.id.startswith("domain:")
    assert "40.4168" not in domain.id and "-3.7038" not in domain.id
    assert len(pseudonymous_node_id(local_secret="hardware-secret")) == 32


def test_privacy_transformer_rejects_invalid_or_missing_identity():
    with pytest.raises(ValueError, match="NODE_SECRET_REQUIRED"):
        pseudonymous_node_id(local_secret="")
    with pytest.raises(ValueError, match="DOMAIN_COORDINATES_INVALID"):
        coarsen_domain(kind="spatial_cell", latitude=91, longitude=0)
    with pytest.raises(ValueError, match="DOMAIN_COORDINATES_REQUIRED"):
        coarsen_domain(kind="spatial_cell")
