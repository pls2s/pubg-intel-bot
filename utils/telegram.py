from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

if TYPE_CHECKING:
    from services.sqlite_service import SQLiteService


TELEGRAM_MESSAGE_LIMIT = 4096
SAFE_CHUNK_SIZE = 3800
logger = logging.getLogger(__name__)


async def answer_text(message: Message, text: str) -> None:
    """Send long responses safely without exceeding Telegram's message limit."""

    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        await message.answer(text)
        return

    chunks = _split_text(text)
    for chunk in chunks:
        await message.answer(chunk)


async def answer_photo(
    message: Message,
    image_url: str,
    caption: str,
    *,
    sqlite_service: "SQLiteService | None" = None,
    cache_key: str | None = None,
) -> bool:
    """Send a photo and cache Telegram's file_id after the first successful send."""

    key = cache_key or image_url
    cached_file_id = await sqlite_service.get_image_file_id(key) if sqlite_service else None

    if cached_file_id:
        try:
            await message.answer_photo(photo=cached_file_id, caption=caption)
            return True
        except TelegramAPIError as exc:
            logger.warning("Could not send cached image %s: %s", key, exc)

    try:
        sent_message = await message.answer_photo(photo=image_url, caption=caption)
    except TelegramAPIError as exc:
        logger.warning("Could not send image %s: %s", image_url, exc)
        return False

    file_id = _extract_photo_file_id(sent_message)
    if sqlite_service and file_id:
        await sqlite_service.save_image_file_id(
            cache_key=key,
            image_url=image_url,
            file_id=file_id,
        )

    return True


def _split_text(text: str) -> list[str]:
    chunks: list[str] = []
    current = ""

    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}".strip() if current else block
        if len(candidate) <= SAFE_CHUNK_SIZE:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(block) <= SAFE_CHUNK_SIZE:
            current = block
            continue

        # Very long blocks are rare, but split them without dropping data.
        start = 0
        while start < len(block):
            chunks.append(block[start : start + SAFE_CHUNK_SIZE])
            start += SAFE_CHUNK_SIZE
        current = ""

    if current:
        chunks.append(current)

    return chunks


def _extract_photo_file_id(message: Message) -> str | None:
    photos = getattr(message, "photo", None) or []
    if not photos:
        return None
    return photos[-1].file_id
