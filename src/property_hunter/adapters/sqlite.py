"""SQLite repository adapter."""

import logging
import sqlite3
from pathlib import Path

from property_hunter.domain.models import AnalyzedProperty

logger = logging.getLogger(__name__)


class SQLitePropertyRepository:
    """Persist analyzed properties in a local SQLite database."""

    def __init__(self, path: Path) -> None:
        """Create a repository backed by ``path``."""
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save(self, property_: AnalyzedProperty) -> AnalyzedProperty:
        """Insert or replace an analyzed property JSON document."""
        payload = property_.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO properties (id, created_at, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (property_.id, property_.created_at.isoformat(), payload),
            )
        logger.info("Saved property id=%s to sqlite path=%s", property_.id, self.path)
        return property_

    def get(self, property_id: str) -> AnalyzedProperty | None:
        """Return a property by id."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM properties WHERE id = ?",
                (property_id,),
            ).fetchone()
        if row is None:
            logger.info(
                "Property id=%s not found in sqlite path=%s",
                property_id,
                self.path,
            )
            return None
        return AnalyzedProperty.model_validate_json(row["payload"])

    def list(self, *, limit: int = 50, offset: int = 0) -> list[AnalyzedProperty]:
        """Return properties ordered by creation time descending."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload FROM properties
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [AnalyzedProperty.model_validate_json(row["payload"]) for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS properties (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection
