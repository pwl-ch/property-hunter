"""Integration tests for SQLite persistence."""

from pathlib import Path

from property_hunter.adapters.sqlite import SQLitePropertyRepository
from property_hunter.domain.models import AnalyzedProperty


def test_sqlite_repository_roundtrip(
    tmp_path: Path,
    analyzed_property: AnalyzedProperty,
) -> None:
    """Persist and load a property through SQLite."""
    # given
    repository = SQLitePropertyRepository(tmp_path / "properties.db")

    # when
    saved = repository.save(analyzed_property)
    loaded = repository.get(saved.id)
    listed = repository.list()

    # then
    assert loaded == saved
    assert listed[0] == saved
