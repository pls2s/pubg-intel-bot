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
        )
