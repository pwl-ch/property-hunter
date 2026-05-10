"""Tests for PropertyHunter."""

from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from property_hunter import __version__
from property_hunter.adapters.api import create_app
from property_hunter.adapters.sqlite import SQLitePropertyRepository
from property_hunter.application.use_cases import AnalyzeListingUseCase
from property_hunter.cli import app
from property_hunter.domain.export import properties_to_csv, properties_to_kml
from property_hunter.domain.geo import build_external_links, classify_utility_distance
from property_hunter.domain.models import (
    AnalyzedProperty,
    CapturedListing,
    ExtractedProperty,
    ParcelGeometry,
    RegulatorySummary,
    UtilityAssessment,
    UtilityStatus,
)
from property_hunter.settings import Settings

runner = CliRunner()


def test_version() -> None:
    """Test that version is defined."""
    assert __version__


def test_cli_version() -> None:
    """Test CLI version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_userscript_prints_capture_button() -> None:
    """Test CLI userscript output."""
    result = runner.invoke(app, ["userscript"])
    assert result.exit_code == 0
    assert "Analizuj w PropertyHunter" in result.stdout
    assert "127.0.0.1:8765/api/analyze" in result.stdout


def test_utility_distance_classification() -> None:
    """Test utility threshold classification."""
    assert classify_utility_distance(None) is UtilityStatus.UNKNOWN
    assert classify_utility_distance(10) is UtilityStatus.GREEN
    assert classify_utility_distance(10.1) is UtilityStatus.YELLOW
    assert classify_utility_distance(100) is UtilityStatus.YELLOW
    assert classify_utility_distance(100.1) is UtilityStatus.RED


def test_external_links_from_geometry() -> None:
    """Test map link generation."""
    geometry = ParcelGeometry(
        parcel_id="141201_1.0001.12/3",
        centroid_2180=(500000, 400000),
        centroid_wgs84=(52.1, 21.0),
        wkt="POLYGON((0 0, 0 1, 1 1, 0 0))",
    )
    links = build_external_links("141201_1.0001.12/3", geometry)
    assert links.google_maps is not None
    assert "52.1000000,21.0000000" in str(links.google_maps)
    assert links.geoportal is not None
    assert links.uldk is not None


def test_csv_and_kml_exports() -> None:
    """Test export formatting."""
    property_ = _analyzed_property()
    csv_document = properties_to_csv([property_])
    kml_document = properties_to_kml([property_])
    assert "parcel_id" in csv_document
    assert "141201_1.0001.12/3" in csv_document
    assert "<Placemark>" in kml_document
    assert "21.0000000,52.1000000,0" in kml_document


def test_sqlite_repository_roundtrip(tmp_path: Path) -> None:
    """Test SQLite persistence roundtrip."""
    repository = SQLitePropertyRepository(tmp_path / "properties.db")
    saved = repository.save(_analyzed_property())
    loaded = repository.get(saved.id)
    assert loaded == saved
    assert repository.list()[0] == saved


def test_analyze_listing_use_case_with_fake_ports(tmp_path: Path) -> None:
    """Test analyze orchestration without external services."""
    repository = SQLitePropertyRepository(tmp_path / "properties.db")
    use_case = AnalyzeListingUseCase(
        repository=repository,
        extraction_agent=FakeExtractionAgent(),
        regulatory_agent=FakeRegulatoryAgent(),
        parcel_locator=FakeParcelLocator(),
        utility_source=FakeUtilitySource(),
    )
    result = use_case.execute(_listing())
    assert result.extracted.parcel_id == "141201_1.0001.12/3"
    assert result.geometry is not None
    assert result.utilities[0].status is UtilityStatus.GREEN
    assert repository.get(result.id) == result


def test_api_analyze_persists_result(tmp_path: Path) -> None:
    """Test POST /api/analyze stores and returns an analysis result."""
    settings = Settings(db_path=tmp_path / "api.db")
    client = TestClient(create_app(settings))
    response = client.post(
        "/api/analyze",
        json=_listing().model_dump(mode="json"),
    )
    assert response.status_code == 200
    property_id = response.json()["id"]
    list_response = client.get("/api/properties")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == property_id


def test_api_token_rejects_unauthorized_requests(tmp_path: Path) -> None:
    """Test optional API token enforcement."""
    settings = Settings(db_path=tmp_path / "api.db", api_token="secret")
    client = TestClient(create_app(settings))
    response = client.get("/api/properties")
    assert response.status_code == 401


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
        return _geometry(parcel_id)


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


def _listing() -> CapturedListing:
    return CapturedListing.model_validate(
        {
            "source_site": "otodom.pl",
            "url": "https://www.otodom.pl/pl/oferta/test",
            "title": "Dzialka 1000 m2 za 100 000 zl",
            "raw_text": "Dzialka 1000 m2 za 100 000 zl. MPZP dopuszcza zabudowe.",
        }
    )


def _geometry(parcel_id: str = "141201_1.0001.12/3") -> ParcelGeometry:
    return ParcelGeometry(
        parcel_id=parcel_id,
        centroid_2180=(500000, 400000),
        centroid_wgs84=(52.1, 21.0),
        wkt="POLYGON((0 0, 0 1, 1 1, 0 0))",
    )


def _analyzed_property() -> AnalyzedProperty:
    return AnalyzedProperty(
        id="property-1",
        listing=_listing(),
        extracted=ExtractedProperty(
            price=100000,
            price_per_sqm=100,
            area_sqm=1000,
            parcel_id="141201_1.0001.12/3",
        ),
        geometry=_geometry(),
        regulatory_summary=RegulatorySummary(summary="MPZP mentioned."),
    )
