"""PropertyHunter application use cases."""

from uuid import uuid4

from property_hunter.application.ports import (
    ExtractionAgent,
    NotionSync,
    ParcelLocator,
    PropertyRepository,
    RegulatoryAgent,
    UtilitySource,
)
from property_hunter.domain.geo import build_external_links
from property_hunter.domain.models import AnalyzedProperty, CapturedListing, SyncStatus
from property_hunter.settings import Settings, get_settings


class AnalyzeListingUseCase:
    """Orchestrate listing extraction, enrichment, and persistence."""

    def __init__(
        self,
        repository: PropertyRepository,
        extraction_agent: ExtractionAgent,
        regulatory_agent: RegulatoryAgent,
        parcel_locator: ParcelLocator | None = None,
        utility_source: UtilitySource | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Create an analyze-listing use case."""
        self.repository = repository
        self.extraction_agent = extraction_agent
        self.regulatory_agent = regulatory_agent
        self.parcel_locator = parcel_locator
        self.utility_source = utility_source
        self.settings = settings or get_settings()

    def execute(self, listing: CapturedListing) -> AnalyzedProperty:
        """Analyze and persist a captured listing."""
        extracted = self.extraction_agent.extract(listing)
        regulatory_summary = self.regulatory_agent.summarize(listing)
        geometry = None
        utilities = []
        if extracted.parcel_id and self.parcel_locator is not None:
            try:
                geometry = self.parcel_locator.locate(extracted.parcel_id)
            except Exception:
                geometry = None
        if geometry is not None and self.utility_source is not None:
            try:
                utilities = self.utility_source.assess(geometry)
            except Exception:
                utilities = []

        analyzed = AnalyzedProperty(
            id=uuid4().hex,
            listing=listing,
            extracted=extracted,
            geometry=geometry,
            utilities=utilities,
            regulatory_summary=regulatory_summary,
            external_links=build_external_links(
                extracted.parcel_id,
                geometry,
                self.settings,
            ),
        )
        return self.repository.save(analyzed)


class ExportPropertiesUseCase:
    """Load properties for export adapters."""

    def __init__(self, repository: PropertyRepository) -> None:
        """Create an export use case."""
        self.repository = repository

    def execute(self, *, limit: int = 1000, offset: int = 0) -> list[AnalyzedProperty]:
        """Return stored properties for export."""
        return self.repository.list(limit=limit, offset=offset)


class SyncNotionUseCase:
    """Synchronize one stored property to Notion idempotently."""

    def __init__(self, repository: PropertyRepository, notion: NotionSync) -> None:
        """Create a Notion synchronization use case."""
        self.repository = repository
        self.notion = notion

    def execute(self, property_id: str) -> AnalyzedProperty | None:
        """Sync a property and persist its resulting Notion page id."""
        property_ = self.repository.get(property_id)
        if property_ is None:
            return None
        try:
            page_id = self.notion.sync(property_)
        except Exception:
            updated = property_.model_copy(update={"sync_status": SyncStatus.FAILED})
            return self.repository.save(updated)
        updated = property_.model_copy(
            update={"sync_status": SyncStatus.SYNCED, "notion_page_id": page_id}
        )
        return self.repository.save(updated)
