from sentinel_edge.qualification.acquisition import AcquisitionRoute, evaluate_acquisition


def test_unsupported_scraping_and_download_are_recorded_as_denied() -> None:
    for route in (AcquisitionRoute.SCRAPE, AcquisitionRoute.ARBITRARY_DOWNLOAD):
        result = evaluate_acquisition(route)
        assert result.permitted is False
        assert result.code == "acquisition_not_permitted"


def test_only_declared_routes_are_permitted_with_required_authorization() -> None:
    assert evaluate_acquisition(AcquisitionRoute.FIXTURE).permitted is True
    assert evaluate_acquisition(AcquisitionRoute.SUPPLIED_UPLOAD, enrolled=False).permitted is False
    assert evaluate_acquisition(AcquisitionRoute.SUPPLIED_UPLOAD, enrolled=True).permitted is True
    assert evaluate_acquisition(AcquisitionRoute.DOCUMENTED_API, documented=False).permitted is False
    assert evaluate_acquisition(AcquisitionRoute.DOCUMENTED_API, documented=True).permitted is True
