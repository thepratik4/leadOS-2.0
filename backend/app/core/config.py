from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "LeadOS"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database: Default to sqlite+aiosqlite for local self-contained runs, or postgresql+asyncpg for production
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./leados.db",
        description="Async SQLAlchemy database connection URL",
    )

    # Search Provider configuration
    SEARCH_PROVIDER: Literal["ddgs", "brave", "serpapi", "tavily"] = "ddgs"
    BRAVE_SEARCH_API_KEY: str | None = None
    SERPAPI_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None

    # Optional Gemini AI key for assisted extraction
    GEMINI_API_KEY: str | None = None

    # Source retrieval security and resource limits
    SOURCE_FETCH_TIMEOUT_SECONDS: float = 8.0
    MAX_SOURCE_BYTES: int = 2 * 1024 * 1024  # 2MB
    MAX_CONCURRENT_FETCHES: int = 5
    USER_AGENT: str = "LeadOS-Crawler/1.0 (+https://leados.internal/bot; verification-only)"


settings = Settings()
