"""Shared pytest fixtures and fakes."""

import pytest

from property_hunter.domain.models import (
    AnalyzedProperty,
    CapturedListing,
    ExtractedProperty,
    ParcelGeometry,
    RegulatorySummary,
    UtilityAssessment,
    UtilityStatus,
)


class FakeExtractionAgent:
    """Fake extraction agent for application tests."""

    def extract(self, listing: CapturedListing) -> ExtractedProperty:
        """Return a deterministic extracted property."""
        _ = listing
        return ExtractedProperty(parcel_id="141201_1.0001.12/3", price=100000)


class FakeRegulatoryAgent:
    """Fake regulatory agent for application tests."""

    def summarize(self, listing: CapturedListing) -> RegulatorySummary:
        """Return a deterministic regulatory summary."""
        _ = listing
        return RegulatorySummary(summary="MPZP mentioned.", mpzp_status="mentioned")


class FakeParcelLocator:
    """Fake parcel locator for application tests."""

    def locate(self, parcel_id: str) -> ParcelGeometry:
        """Return deterministic parcel geometry."""
        return make_geometry(parcel_id)


class FakeUtilitySource:
    """Fake utility source for application tests."""

    def assess(self, geometry: ParcelGeometry) -> list[UtilityAssessment]:
        """Return deterministic utility assessments."""
        _ = geometry
        return [
            UtilityAssessment(
                network_type="water",
                status=UtilityStatus.GREEN,
                distance_meters=5,
                source_layer="fake",
            )
        ]


@pytest.fixture
def captured_listing() -> CapturedListing:
    """Provide a captured listing fixture."""
    return make_listing()


@pytest.fixture
def parcel_geometry() -> ParcelGeometry:
    """Provide a parcel geometry fixture."""
    return make_geometry()


@pytest.fixture
def analyzed_property() -> AnalyzedProperty:
    """Provide an analyzed property fixture."""
    return make_analyzed_property()


def make_listing() -> CapturedListing:
    """Build a deterministic listing model for tests."""
    return CapturedListing.model_validate(
        {
            "source_site": "otodom.pl",
            "url": "https://www.otodom.pl/pl/oferta/test",
            "title": "Dzialka 1000 m2 za 100 000 zl",
            "raw_text": "Dzialka 1000 m2 za 100 000 zl. MPZP dopuszcza zabudowe.",
        }
    )


def make_geometry(parcel_id: str = "141201_1.0001.12/3") -> ParcelGeometry:
    """Build deterministic parcel geometry for tests."""
    return ParcelGeometry(
        parcel_id=parcel_id,
        centroid_2180=(500000, 400000),
        centroid_wgs84=(52.1, 21.0),
        wkt="POLYGON((0 0, 0 1, 1 1, 0 0))",
    )


def make_analyzed_property() -> AnalyzedProperty:
    """Build a deterministic analyzed property for tests."""
    return AnalyzedProperty(
        id="property-1",
        listing=make_listing(),
        extracted=ExtractedProperty(
            price=100000,
            price_per_sqm=100,
            area_sqm=1000,
            parcel_id="141201_1.0001.12/3",
        ),
        geometry=make_geometry(),
        regulatory_summary=RegulatorySummary(summary="MPZP mentioned."),
    )
