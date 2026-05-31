from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class SQLiteService:
    """Small SQLite adapter used for query analytics and future persistence."""

    def __init__(self, sqlite_path: Path | str) -> None:
        self.sqlite_path = Path(sqlite_path)

    async def init(self) -> None:
        await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    command TEXT NOT NULL,
                    query TEXT NOT NULL,
                    matched_type TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_queries_created_at
                ON user_queries(created_at)
                """
            )

    async def log_query(
        self,
        *,
        user: Any,
        command: str,
        query: str,
        matched_type: str | None = None,
    ) -> None:
        try:
            await asyncio.to_thread(
                self._log_query_sync,
                getattr(user, "id", None),
                getattr(user, "username", None),
                command,
                query,
                matched_type,
            )
        except sqlite3.Error as exc:
            # Analytics must never break a Telegram response.
            logger.warning("Could not log query to SQLite: %s", exc)

    def _log_query_sync(
        self,
        user_id: int | None,
        username: str | None,
        command: str,
        query: str,
        matched_type: str | None,
    ) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                INSERT INTO user_queries (user_id, username, command, query, matched_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    command,
                    query,
                    matched_type,
                    datetime.now(UTC).isoformat(),
                ),
            )
