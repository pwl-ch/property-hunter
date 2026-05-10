"""Integration tests for the FastAPI adapter."""

from pathlib import Path

from fastapi.testclient import TestClient

from property_hunter.adapters.api import create_app
from property_hunter.domain.models import CapturedListing
from property_hunter.settings import Settings


def test_api_analyze_persists_result(
    tmp_path: Path,
    captured_listing: CapturedListing,
) -> None:
    """Persist an analyzed listing through the API."""
    # given
    settings = Settings(db_path=tmp_path / "api.db", agent_mode="heuristic")
    client = TestClient(create_app(settings))

    # when
    response = client.post(
        "/api/analyze",
        json=captured_listing.model_dump(mode="json"),
    )
    property_id = response.json()["id"]
    list_response = client.get("/api/properties")

    # then
    assert response.status_code == 200
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == property_id


def test_api_token_rejects_unauthorized_requests(tmp_path: Path) -> None:
    """Reject API requests when token is configured and missing."""
    # given
    settings = Settings(
        db_path=tmp_path / "api.db",
        api_token="secret",
        agent_mode="heuristic",
    )
    client = TestClient(create_app(settings))

    # when
    response = client.get("/api/properties")

    # then
    assert response.status_code == 401
