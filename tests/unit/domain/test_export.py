"""Unit tests for domain export formatting."""

from property_hunter.domain.export import properties_to_csv, properties_to_kml
from property_hunter.domain.models import AnalyzedProperty


def test_csv_and_kml_exports(analyzed_property: AnalyzedProperty) -> None:
    """Format analyzed properties as CSV and KML."""
    # given
    properties = [analyzed_property]

    # when
    csv_document = properties_to_csv(properties)
    kml_document = properties_to_kml(properties)

    # then
    assert "parcel_id" in csv_document
    assert "141201_1.0001.12/3" in csv_document
    assert "<Placemark>" in kml_document
    assert "21.0000000,52.1000000,0" in kml_document
