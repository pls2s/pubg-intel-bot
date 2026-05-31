from __future__ import annotations

from aiogram.types import Message


TELEGRAM_MESSAGE_LIMIT = 4096
SAFE_CHUNK_SIZE = 3800


async def answer_text(message: Message, text: str) -> None:
    """Send long responses safely without exceeding Telegram's message limit."""

    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        await message.answer(text)
        return

    chunks = _split_text(text)
    for chunk in chunks:
        await message.answer(chunk)


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
        current = block

    if current:
        chunks.append(current[:SAFE_CHUNK_SIZE])

    return chunks
