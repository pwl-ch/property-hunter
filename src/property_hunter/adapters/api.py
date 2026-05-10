"""FastAPI adapter for local orchestration APIs."""

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status

from property_hunter.adapters.agents import (
    HeuristicExtractionAgent,
    HeuristicRegulatoryAgent,
)
from property_hunter.adapters.kiut import KIUTUtilitySource
from property_hunter.adapters.notion import NotionPropertySync
from property_hunter.adapters.sqlite import SQLitePropertyRepository
from property_hunter.adapters.uldk import ULDKParcelLocator
from property_hunter.application.use_cases import (
    AnalyzeListingUseCase,
    ExportPropertiesUseCase,
    SyncNotionUseCase,
)
from property_hunter.domain.export import properties_to_csv, properties_to_kml
from property_hunter.domain.models import AnalyzedProperty, CapturedListing
from property_hunter.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the local PropertyHunter FastAPI app."""
    settings = settings or get_settings()
    repository = SQLitePropertyRepository(Path(settings.db_path))
    analyze_use_case = AnalyzeListingUseCase(
        repository=repository,
        extraction_agent=HeuristicExtractionAgent(),
        regulatory_agent=HeuristicRegulatoryAgent(),
        parcel_locator=ULDKParcelLocator(
            timeout_seconds=settings.request_timeout_seconds
        ),
        utility_source=KIUTUtilitySource(),
    )
    export_use_case = ExportPropertiesUseCase(repository)

    app = FastAPI(title="PropertyHunter", version="0.1.0")

    def require_token(
        authorization: str | None = Header(default=None),
    ) -> None:
        if settings.api_token is None:
            return
        expected = f"Bearer {settings.api_token}"
        if authorization != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
            )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return local service readiness."""
        return {"status": "ok"}

    @app.post(
        "/api/analyze",
        response_model=AnalyzedProperty,
        dependencies=[Depends(require_token)],
    )
    def analyze(listing: CapturedListing) -> AnalyzedProperty:
        """Analyze a captured listing and store the result."""
        return analyze_use_case.execute(listing)

    @app.get(
        "/api/properties",
        response_model=list[AnalyzedProperty],
        dependencies=[Depends(require_token)],
    )
    def list_properties(limit: int = 50, offset: int = 0) -> list[AnalyzedProperty]:
        """List historical analysis results."""
        return repository.list(limit=limit, offset=offset)

    @app.get(
        "/api/properties/{property_id}",
        response_model=AnalyzedProperty,
        dependencies=[Depends(require_token)],
    )
    def get_property(property_id: str) -> AnalyzedProperty:
        """Return a single analyzed property."""
        property_ = repository.get(property_id)
        if property_ is None:
            raise HTTPException(status_code=404, detail="Property not found")
        return property_

    @app.post(
        "/api/properties/{property_id}/sync/notion",
        response_model=AnalyzedProperty,
        dependencies=[Depends(require_token)],
    )
    def sync_notion(property_id: str) -> AnalyzedProperty:
        """Sync one property to Notion."""
        if not settings.notion_token or not settings.notion_database_id:
            raise HTTPException(status_code=400, detail="Notion is not configured")
        use_case = SyncNotionUseCase(
            repository,
            NotionPropertySync(settings.notion_token, settings.notion_database_id),
        )
        result = use_case.execute(property_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Property not found")
        return result

    @app.get("/api/export.csv", dependencies=[Depends(require_token)])
    def export_csv() -> Response:
        """Export stored properties as CSV."""
        return Response(
            properties_to_csv(export_use_case.execute()),
            media_type="text/csv",
        )

    @app.get("/api/export.kml", dependencies=[Depends(require_token)])
    def export_kml() -> Response:
        """Export stored properties as KML."""
        return Response(
            properties_to_kml(export_use_case.execute()),
            media_type="application/vnd.google-earth.kml+xml",
        )

    return app
