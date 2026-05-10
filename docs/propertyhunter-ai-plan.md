# PropertyHunter AI Implementation Plan

## Summary

Build the full PRD as a local-first Python application using hexagonal architecture. FastAPI will be the primary adapter for orchestration APIs, Pydantic AI will power local agents, Ollama will be the default model provider, SQLite will handle persistence, Streamlit will provide the local dashboard, and a Tampermonkey/Violentmonkey userscript will capture listing data.

One correction to the PRD wording: use GUGiK **ULDK** for parcel lookup, not "ULIC". ULDK supports `GetParcelById` and geometry responses for cadastral parcels. KIUT is available as a national integration service for utility infrastructure, but its public documentation emphasizes WMS; implementation should verify usable WFS/GetFeature support during the MediaChecker phase.

## Architecture

- Use hexagonal architecture:
  - Domain: pure models, value objects, distance rules, export formatting rules, orchestration state.
  - Application: use cases such as analyze listing, resolve parcel, assess utilities, export properties, sync Notion.
  - Ports: repository, LLM agent, parcel locator, utility source, Notion sync, clock/id generator.
  - Adapters: FastAPI, Streamlit, SQLite, Pydantic AI/Ollama, ULDK HTTP, KIUT HTTP, Notion API, userscript payload.
- Use functional style where it keeps behavior simple and testable:
  - parsing, validation, enrichment transforms, distance classification, link generation, KML/CSV generation.
- Use OOP where it is more feasible:
  - adapters with external state/config, repositories, API clients, Pydantic AI agent wrappers, orchestration services.

## Public Interfaces

- CLI:
  - `property_hunter serve --host 127.0.0.1 --port 8765`
  - `property_hunter dashboard`
  - `property_hunter export --format kml|csv --output <path>`
- FastAPI:
  - `POST /api/analyze`: accepts captured listing payload, runs orchestration, stores result.
  - `GET /api/properties`: paginated historical results.
  - `GET /api/properties/{id}`: full enriched property object.
  - `POST /api/properties/{id}/sync/notion`: sync one record.
  - `GET /api/export.kml` and `GET /api/export.csv`: selected/all property export.
  - `GET /health`: local service readiness.
- Core Pydantic models:
  - `CapturedListing`: source site, URL, title, raw text, optional raw HTML, captured timestamp.
  - `ExtractedProperty`: price, price per sqm, area, parcel id, city, street, regulatory text summary.
  - `ParcelGeometry`: parcel id, centroid EPSG:2180, centroid WGS84, WKT geometry.
  - `UtilityAssessment`: network type, status `green|yellow|red|unknown`, distance meters, source layer.
  - `AnalyzedProperty`: extracted info, geometry, utilities, regulatory summary, external links, sync status.

## Implementation Changes

- Replace the generated hello-world package with layered modules:
  - `domain`: Pydantic models, value objects, pure classification/link/export helpers.
  - `application`: use cases and ports.
  - `adapters`: FastAPI, Streamlit, SQLite, Pydantic AI agents, ULDK/KIUT clients, Notion client.
  - `settings`: `pydantic-settings` config for model provider, SQLite path, Notion, retry policy.
- Add dependencies: `fastapi`, `uvicorn`, `pydantic-ai`, `pydantic-settings`, `httpx`, `tenacity`, `sqlmodel`, `shapely`, `pyproj`, `streamlit`, `notion-client`.
- Pydantic AI agents:
  - Extraction agent returns `ExtractedProperty`.
  - Regulatory agent returns a structured regulatory summary from listing text.
  - Default provider uses Ollama at `http://127.0.0.1:11434`.
  - LM Studio remains available through an OpenAI-compatible endpoint at `http://127.0.0.1:1234/v1`.
- Spatial enrichment:
  - Call `https://uldk.gugik.gov.pl/?request=GetParcelById&id=<parcel>&result=geom_wkt`.
  - Parse WKT with Shapely, compute centroid in EPSG:2180, transform to WGS84 for maps.
  - Generate Google Maps and Geoportal links.
- MediaChecker:
  - Query KIUT-compatible utility layers around parcel centroid with retry/backoff.
  - Compute nearest geometry distance in meters.
  - Use thresholds: green `<= 10m`, yellow `>10m and <=100m`, red `>100m`, unknown when service/layer unavailable.
- Userscript:
  - Match `otodom.pl`, `olx.pl`, `adresowo.pl`.
  - Add floating `Analizuj w PropertyHunter` button.
  - Send captured listing payload to `http://127.0.0.1:8765/api/analyze`.
- Streamlit dashboard:
  - Table, filters, map preview, detail panel, utility status indicators, export buttons.
- Notion:
  - Append/update rows using `NOTION_TOKEN` and `NOTION_DATABASE_ID`.
  - Store Notion page id in SQLite for idempotent resync.

## Test Plan

- Unit tests:
  - Domain model validation and pure helper functions.
  - Pydantic AI agent adapters with mocked model responses.
  - ULDK client success/error/malformed geometry handling.
  - Utility distance classification.
  - KML/CSV export formatting.
- Application tests:
  - Analyze-listing use case with fake ports.
  - Notion sync idempotency with fake repository and sync adapter.
  - Export use case using stored properties.
- API tests:
  - `POST /api/analyze` persists a complete result with mocked use case.
  - API binds/configures only `127.0.0.1`.
  - optional token rejects unauthorized requests when configured.
- Quality gates:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run ty check`

## Assumptions

- Implement all PRD phases, but keep adapters optional so core analysis can run without KIUT, Notion, or external MPZP ingestion configured.
- Ollama is the default local model provider.
- Streamlit is the dashboard stack.
- SQLite lives at `~/.property_hunter/property_hunter.db` by default, overridable with `PROPERTY_HUNTER_DB_PATH`.
- No external LLM APIs are added.
- Official references used for planning: GUGiK ULDK docs at <https://uldk.gugik.gov.pl/opis.html> and Geoportal KIUT/GESUT information at <https://www.geoportal.gov.pl/pl/dane/uzbrojenie-terenu-gesut/>.
