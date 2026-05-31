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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS image_cache (
                    cache_key TEXT PRIMARY KEY,
                    image_url TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
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

    async def get_image_file_id(self, cache_key: str) -> str | None:
        try:
            return await asyncio.to_thread(self._get_image_file_id_sync, cache_key)
        except sqlite3.Error as exc:
            logger.warning("Could not read Telegram image cache: %s", exc)
            return None

    def _get_image_file_id_sync(self, cache_key: str) -> str | None:
        with sqlite3.connect(self.sqlite_path) as conn:
            row = conn.execute(
                "SELECT file_id FROM image_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        return str(row[0]) if row else None

    async def save_image_file_id(self, *, cache_key: str, image_url: str, file_id: str) -> None:
        try:
            await asyncio.to_thread(
                self._save_image_file_id_sync,
                cache_key,
                image_url,
                file_id,
            )
        except sqlite3.Error as exc:
            logger.warning("Could not save Telegram image cache: %s", exc)

    def _save_image_file_id_sync(self, cache_key: str, image_url: str, file_id: str) -> None:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                INSERT INTO image_cache (cache_key, image_url, file_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    image_url = excluded.image_url,
                    file_id = excluded.file_id,
                    updated_at = excluded.updated_at
                """,
                (cache_key, image_url, file_id, now, now),
            )
