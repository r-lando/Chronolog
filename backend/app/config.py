"""
Application configuration.

All values come from environment variables (see .env.example). Nothing
secret is hardcoded here. pydantic-settings validates types and fails
fast at startup if a required variable is missing, rather than silently
running with an insecure default.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Auth / JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # App
    environment: str = "development"
    cors_origins: str = "http://localhost:5173"
    cookie_secure: bool = False

    # Single-user control
    allow_single_user_only: bool = True

    # File uploads
    evidence_storage_path: str = "/app/storage/evidence"
    max_upload_size_mb: int = 25

    # Rate limiting
    rate_limit_login: str = "5/minute"
    rate_limit_upload: str = "20/minute"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    # Cached so we parse the environment once per process, not per request.
    return Settings()
