"""Unit tests for analyze-listing orchestration."""

from pathlib import Path

from tests.conftest import (
    FakeExtractionAgent,
    FakeParcelLocator,
    FakeRegulatoryAgent,
    FakeUtilitySource,
)

from property_hunter.adapters.sqlite import SQLitePropertyRepository
from property_hunter.application.use_cases import AnalyzeListingUseCase
from property_hunter.domain.models import CapturedListing, UtilityStatus


def test_analyze_listing_use_case_with_fake_ports(
    tmp_path: Path,
    captured_listing: CapturedListing,
) -> None:
    """Analyze a listing without external services."""
    # given
    repository = SQLitePropertyRepository(tmp_path / "properties.db")
    use_case = AnalyzeListingUseCase(
        repository=repository,
        extraction_agent=FakeExtractionAgent(),
        regulatory_agent=FakeRegulatoryAgent(),
        parcel_locator=FakeParcelLocator(),
        utility_source=FakeUtilitySource(),
    )

    # when
    result = use_case.execute(captured_listing)

    # then
    assert result.extracted.parcel_id == "141201_1.0001.12/3"
    assert result.geometry is not None
    assert result.utilities[0].status is UtilityStatus.GREEN
    assert repository.get(result.id) == result
