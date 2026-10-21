from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    openrouter_api_key: str = ""
    openrouter_model: str = "minimax/minimax-m3.1-flash:free"
    finnhub_api_key: str = ""
    alphavantage_api_key: str = ""

    alphavantage_daily_cap: int = 20
    llm_daily_cap: int = 100
    openstock_refresh_seconds: int = 300
    openstock_provider_mode: str = "live"  # live | fixtures
    openstock_db_path: str = str(BASE_DIR / "data" / "openstock.db")
    openstock_http_timeout: float = 20.0
    openstock_enable_background_prefetch: bool = True

    @property
    def fixtures_mode(self) -> bool:
        return self.openstock_provider_mode.strip().lower() == "fixtures"


@lru_cache
def get_settings() -> Settings:
    return Settings()
