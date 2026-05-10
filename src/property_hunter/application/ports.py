"""Application port protocols."""

from typing import Protocol

from property_hunter.domain.models import (
    AnalyzedProperty,
    CapturedListing,
    ExtractedProperty,
    ParcelGeometry,
    RegulatorySummary,
    UtilityAssessment,
)


class PropertyRepository(Protocol):
    """Persistence port for analyzed properties."""

    def save(self, property_: AnalyzedProperty) -> AnalyzedProperty:
        """Persist or update an analyzed property."""

    def get(self, property_id: str) -> AnalyzedProperty | None:
        """Return a property by local id."""

    def list(self, *, limit: int = 50, offset: int = 0) -> list[AnalyzedProperty]:
        """Return properties ordered by creation time descending."""


class ExtractionAgent(Protocol):
    """LLM or heuristic adapter for listing fact extraction."""

    def extract(self, listing: CapturedListing) -> ExtractedProperty:
        """Extract structured facts from a captured listing."""


class RegulatoryAgent(Protocol):
    """LLM or heuristic adapter for planning text summarization."""

    def summarize(self, listing: CapturedListing) -> RegulatorySummary:
        """Summarize regulatory content in a captured listing."""


class ParcelLocator(Protocol):
    """Cadastral parcel lookup port."""

    def locate(self, parcel_id: str) -> ParcelGeometry | None:
        """Resolve a parcel id to geometry."""


class UtilitySource(Protocol):
    """Utility infrastructure assessment port."""

    def assess(self, geometry: ParcelGeometry) -> list[UtilityAssessment]:
        """Assess nearby utility networks for a resolved parcel."""


class NotionSync(Protocol):
    """External Notion synchronization port."""

    def sync(self, property_: AnalyzedProperty) -> str:
        """Create or update a Notion page and return its page id."""
