from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.search_service import SearchService
from services.sqlite_service import SQLiteService
from utils.formatters import format_not_found, usage
from utils.secret_responses import answer_secret_matches
from utils.telegram import answer_text
from utils.text import command_args


router = Router(name="secret")


@router.message(Command("secret"))
async def secret_command(
    message: Message,
    search_service: SearchService,
    sqlite_service: SQLiteService,
) -> None:
    query = command_args(message.text)
    if not query:
        await answer_text(
            message,
            usage("secret", ["/secret vikendi", "/secret taego", "secret room vikendi"]),
        )
        return

    matches = search_service.secret(query)
    await sqlite_service.log_query(
        user=message.from_user,
        command="/secret",
        query=query,
        matched_type="secret" if matches else None,
    )
    if matches:
        await answer_secret_matches(message, matches, sqlite_service)
    else:
        await answer_text(
            message,
            format_not_found("ห้องลับ/จุดพิเศษ", query, search_service.suggestions(query)),
        )
