"""Runtime settings for the local PropertyHunter application."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(
        env_prefix="PROPERTY_HUNTER_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8765
    api_base_url: str = "http://127.0.0.1:8765"
    db_path: Path = Field(
        default_factory=lambda: Path.home() / ".property_hunter" / "property_hunter.db"
    )
    agent_mode: Literal["llm", "heuristic"] = "llm"
    llm_provider: Literal["lm_studio", "ollama"] = "lm_studio"
    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    uldk_base_url: str = "https://uldk.gugik.gov.pl/"
    google_maps_url_template: str = (
        "https://www.google.com/maps?q={latitude},{longitude}"
    )
    geoportal_url_template: str = (
        "https://mapy.geoportal.gov.pl/imap/Imgp_2.html?identifyParcel={parcel_id}"
    )
    userscript_namespace_url: str = "http://127.0.0.1:8765/"
    userscript_analyze_url: str = "http://127.0.0.1:8765/api/analyze"
    userscript_connect_host: str = "127.0.0.1"
    userscript_match_patterns: list[str] = Field(
        default_factory=lambda: [
            "https://*.otodom.pl/*",
            "https://*.olx.pl/*",
            "https://*.adresowo.pl/*",
        ]
    )
    model_name: str = "google/gemma-4-e4b"
    llm_api_key: str = "lm-studio"
    api_token: str | None = None
    notion_token: str | None = None
    notion_database_id: str | None = None
    request_timeout_seconds: float = 15.0


def get_settings() -> Settings:
    """Return settings loaded from environment and defaults."""
    return Settings()
