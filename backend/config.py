from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Cribbage"
    cors_origins: List[str] = ["http://localhost:5173"]
    session_timeout_seconds: int = 7200  # 2 hours
    stats_db_path: str = "data/cribbage_stats.db"


settings = Settings()
