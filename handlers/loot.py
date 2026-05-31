from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.search_service import SearchService
from services.sqlite_service import SQLiteService
from utils.formatters import format_loot_results, format_not_found, usage
from utils.telegram import answer_text
from utils.text import command_args


router = Router(name="loot")


@router.message(Command("loot"))
async def loot_command(
    message: Message,
    search_service: SearchService,
    sqlite_service: SQLiteService,
) -> None:
    query = command_args(message.text)
    if not query:
        await answer_text(
            message,
            usage("loot", ["/loot school", "/loot military base", "loot pochinki"]),
        )
        return

    matches = search_service.loot(query)
    response = (
        format_loot_results(matches)
        if matches
        else format_not_found("ข้อมูล loot", query, search_service.suggestions(query))
    )

    await sqlite_service.log_query(
        user=message.from_user,
        command="/loot",
        query=query,
        matched_type="loot" if matches else None,
    )
    await answer_text(message, response)
