from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    bot_token: str
    database_dir: Path
    sqlite_path: Path
    log_level: str = "INFO"
    gemini_api_key: str = ""
    gemini_zone_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(BASE_DIR / ".env")

        bot_token = os.getenv("BOT_TOKEN", "").strip()
        if not bot_token:
            raise RuntimeError("BOT_TOKEN is required. Copy .env.example to .env and set it.")

        database_dir = Path(os.getenv("DATABASE_DIR", "database"))
        if not database_dir.is_absolute():
            database_dir = BASE_DIR / database_dir

        sqlite_path = Path(os.getenv("SQLITE_PATH", "data/pubg_intel.sqlite3"))
        if not sqlite_path.is_absolute():
            sqlite_path = BASE_DIR / sqlite_path

        return cls(
            bot_token=bot_token,
            database_dir=database_dir,
            sqlite_path=sqlite_path,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_zone_model=os.getenv("GEMINI_ZONE_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash",
            gemini_timeout_seconds=_int_env("GEMINI_TIMEOUT_SECONDS", 30),
        )


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
