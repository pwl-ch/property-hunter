"""Notion synchronization adapter."""

import logging
from typing import Any, cast

from notion_client import Client

from property_hunter.domain.models import AnalyzedProperty, SyncStatus

logger = logging.getLogger(__name__)


class NotionPropertySync:
    """Append or update analyzed property rows in a Notion database."""

    def __init__(self, token: str, database_id: str) -> None:
        """Create a Notion sync adapter."""
        self.client = Client(auth=token)
        self.database_id = database_id

    def sync(self, property_: AnalyzedProperty) -> str:
        """Create a Notion page for a property and return its page id."""
        logger.info("Syncing property id=%s to Notion", property_.id)
        properties: dict[str, Any] = {
            "Name": {"title": [{"text": {"content": property_.listing.title}}]},
            "URL": {"url": str(property_.listing.url)},
            "Status": {"select": {"name": SyncStatus.SYNCED.value}},
        }
        if property_.extracted.price is not None:
            properties["Price"] = {"number": property_.extracted.price}
        if property_.notion_page_id:
            self.client.pages.update(
                page_id=property_.notion_page_id,
                properties=properties,
            )
            logger.info("Updated Notion page for property id=%s", property_.id)
            return property_.notion_page_id
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
        )
        page = cast("dict[str, Any]", response)
        logger.info("Created Notion page for property id=%s", property_.id)
        return str(page["id"])
