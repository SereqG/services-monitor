from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


APP_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = APP_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")

    app_name: str = "Services Monitor API"
    debug: bool = False

    http_timeout: float = 30.0
    http_max_redirects: int = 10
    user_agent: str = "ServiceMonitorBot/1.0 (+https://services-monitor.io/bot)"

    discovery_max_urls: int = 500
    discovery_max_depth: int = 3
    discovery_max_duration_seconds: int = 120
    discovery_max_requests: int = 1000

    audit_max_duration_seconds: int = 240
    audit_max_pages: int = 50
    audit_default_pages: int = 15

    openrouter_api_key: str | None = None
    ai_summary_enabled: bool = True
    ai_summary_model: str = "google/gemini-2.5-flash"
    ai_summary_timeout_seconds: float = 45.0
    ai_summary_max_tokens: int = 8192
    ai_summary_max_tool_iterations: int = 4
    ai_storage_dir: str = ""
    summaries_dir: str = ""


settings = Settings()
