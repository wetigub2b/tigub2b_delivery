from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

# Load shared and service-specific .env files so direct VM runs pick up credentials.
load_dotenv(BASE_DIR / ".env", override=False)
load_dotenv(BASE_DIR / "bff" / ".env", override=False)


def _normalize_origins(raw: str) -> List[str]:
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    parts = [item.strip() for item in value.split(",") if item.strip()]
    return [part.strip('"').strip("'") for part in parts]


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    app_name: str = Field(default="Tigu Delivery BFF", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api", alias="API_V1_PREFIX")
    secret_key: str = Field(default="insecure-development-key", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 7, alias="REFRESH_TOKEN_EXPIRE_MINUTES")

    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_database: str = Field(default="tigu_b2b", alias="MYSQL_DATABASE")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="password", alias="MYSQL_PASSWORD")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    allowed_origins: List[str] | str = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="ALLOWED_ORIGINS"
    )
    google_maps_api_key: Optional[str] = Field(default=None, alias="GOOGLE_MAPS_API_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    python_bin: str = Field(default="python3", alias="PYTHON_BIN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        json_loads=lambda value: value  # deliver raw values; custom parsing below
    )

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = (
                f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
                f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            )
        return self

    @model_validator(mode="after")
    def normalize_origins(self) -> "Settings":
        if isinstance(self.allowed_origins, str):
            self.allowed_origins = _normalize_origins(self.allowed_origins)
        return self

    @property
    def allowed_origins_list(self) -> List[str]:
        if isinstance(self.allowed_origins, str):
            return _normalize_origins(self.allowed_origins)
        return list(self.allowed_origins)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if isinstance(settings.allowed_origins, str):
        settings.allowed_origins = _normalize_origins(settings.allowed_origins)
    return settings
