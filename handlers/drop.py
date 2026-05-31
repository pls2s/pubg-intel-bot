from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.search_service import SearchService
from services.sqlite_service import SQLiteService
from utils.formatters import format_drop_recommendation, format_not_found, usage
from utils.telegram import answer_text
from utils.text import command_args


router = Router(name="drop")


@router.message(Command("drop"))
async def drop_command(
    message: Message,
    search_service: SearchService,
    sqlite_service: SQLiteService,
) -> None:
    query = command_args(message.text)
    if not query:
        await answer_text(
            message,
            usage("drop", ["/drop erangel", "/drop miramar", "safe drop sanhok"]),
        )
        return

    lookup = search_service.drop(query)
    response = (
        format_drop_recommendation(lookup.map_data, lookup.risk_hint)
        if lookup.map_data
        else format_not_found("drop recommendation", query, search_service.suggestions(query))
    )

    await sqlite_service.log_query(
        user=message.from_user,
        command="/drop",
        query=query,
        matched_type="drop" if lookup.map_data else None,
    )
    await answer_text(message, response)
