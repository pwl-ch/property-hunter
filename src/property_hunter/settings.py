"""Runtime settings for the local PropertyHunter application."""

from pathlib import Path

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
    db_path: Path = Field(
        default_factory=lambda: Path.home() / ".property_hunter" / "property_hunter.db"
    )
    ollama_base_url: str = "http://127.0.0.1:11434"
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    model_name: str = "llama3.1"
    api_token: str | None = None
    notion_token: str | None = None
    notion_database_id: str | None = None
    request_timeout_seconds: float = 15.0


def get_settings() -> Settings:
    """Return settings loaded from environment and defaults."""
    return Settings()
