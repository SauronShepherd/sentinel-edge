from sentinel_edge.integrations.firms import FirmsAvailability, FirmsObservation, FirmsProcessingClass, assess_firms_completeness


def test_firms_fixture_preserves_lineage_and_correlation_family() -> None:
    item = FirmsObservation("obs-1", "VIIRS", "active-fire", FirmsProcessingClass.NRT, "fire-family-1", True)
    assert item.processing_class is FirmsProcessingClass.NRT
    assert item.correlation_family == "fire-family-1"


def test_missing_date_reduces_completeness_without_negative_fire_observation() -> None:
    completeness, incomplete = assess_firms_completeness((FirmsAvailability("2026-08-01", True), FirmsAvailability("2026-08-02", False, "not-published")))
    assert completeness == 0.5
    assert incomplete is True
