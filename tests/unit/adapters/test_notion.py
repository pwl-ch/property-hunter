"""Unit tests for the Notion adapter."""

from typing import Any

from property_hunter.adapters.notion import NotionPropertySync
from property_hunter.domain.models import AnalyzedProperty, SyncStatus


class FakePages:
    """Fake Notion pages client."""

    def __init__(self) -> None:
        """Create a fake pages client."""
        self.created_properties: dict[str, Any] | None = None

    def create(
        self,
        *,
        parent: dict[str, str],
        properties: dict[str, Any],
    ) -> dict[str, str]:
        """Record Notion page creation."""
        _ = parent
        self.created_properties = properties
        return {"id": "notion-page-1"}


class FakeClient:
    """Fake Notion client."""

    def __init__(self) -> None:
        """Create a fake Notion client."""
        self.pages = FakePages()


def test_notion_sync_writes_synced_status(
    analyzed_property: AnalyzedProperty,
) -> None:
    """Write the target synced state to Notion during successful sync."""
    # given
    sync = NotionPropertySync.__new__(NotionPropertySync)
    sync.client = FakeClient()
    sync.database_id = "database-1"

    # when
    page_id = sync.sync(analyzed_property)

    # then
    assert page_id == "notion-page-1"
    assert sync.client.pages.created_properties is not None
    assert sync.client.pages.created_properties["Status"]["select"]["name"] == (
        SyncStatus.SYNCED.value
    )
