from __future__ import annotations

from aiogram.types import Message

from models.map_data import SecretRoomMatch
from services.sqlite_service import SQLiteService
from utils.formatters import format_secret_image_caption, format_secret_results
from utils.telegram import answer_photo, answer_text


async def answer_secret_matches(
    message: Message,
    matches: list[SecretRoomMatch],
    sqlite_service: SQLiteService | None = None,
) -> None:
    """Prefer map images for secret-room answers, then fall back to text."""

    text_only: list[SecretRoomMatch] = []
    sent_any_photo = False

    for match in matches:
        if not match.secret_room.image_url:
            text_only.append(match)
            continue

        sent = await answer_photo(
            message,
            match.secret_room.image_url,
            format_secret_image_caption(match),
            sqlite_service=sqlite_service,
        )
        if sent:
            sent_any_photo = True
        else:
            text_only.append(match)

    if text_only:
        await answer_text(message, format_secret_results(text_only))
    elif not sent_any_photo:
        await answer_text(message, format_secret_results(matches))
