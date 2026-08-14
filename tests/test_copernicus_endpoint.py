import pytest

from sentinel_edge.integrations import validate_copernicus_endpoint


def test_copernicus_supported_stac_and_odata_endpoints_are_accepted() -> None:
    assert validate_copernicus_endpoint("https://catalogue.dataspace.copernicus.eu/stac/collections")
    assert validate_copernicus_endpoint("https://catalogue.dataspace.copernicus.eu/odata/v1/Products")


def test_copernicus_deprecated_endpoint_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported or deprecated"):
        validate_copernicus_endpoint("https://scihub.copernicus.eu/dhus/search")
