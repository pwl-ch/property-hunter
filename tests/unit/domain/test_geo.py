"""Unit tests for domain geographic helpers."""

from property_hunter.domain.geo import build_external_links, classify_utility_distance
from property_hunter.domain.models import ParcelGeometry, UtilityStatus


def test_utility_distance_classification() -> None:
    """Classify utility distances into traffic-light statuses."""
    # given
    unknown_distance = None

    # when
    unknown_status = classify_utility_distance(unknown_distance)
    green_status = classify_utility_distance(10)
    yellow_status_above_green = classify_utility_distance(10.1)
    yellow_status_at_limit = classify_utility_distance(100)
    red_status = classify_utility_distance(100.1)

    # then
    assert unknown_status is UtilityStatus.UNKNOWN
    assert green_status is UtilityStatus.GREEN
    assert yellow_status_above_green is UtilityStatus.YELLOW
    assert yellow_status_at_limit is UtilityStatus.YELLOW
    assert red_status is UtilityStatus.RED


def test_external_links_from_geometry(parcel_geometry: ParcelGeometry) -> None:
    """Build external map links from resolved geometry."""
    # given
    parcel_id = "141201_1.0001.12/3"

    # when
    links = build_external_links(parcel_id, parcel_geometry)

    # then
    assert links.google_maps is not None
    assert "52.1000000,21.0000000" in str(links.google_maps)
    assert links.geoportal is not None
    assert links.uldk is not None
