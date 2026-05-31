from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.search_service import SearchService
from services.sqlite_service import SQLiteService
from utils.formatters import format_not_found, format_vehicle_results, usage
from utils.telegram import answer_text
from utils.text import command_args


router = Router(name="vehicle")


@router.message(Command("vehicle"))
async def vehicle_command(
    message: Message,
    search_service: SearchService,
    sqlite_service: SQLiteService,
) -> None:
    query = command_args(message.text)
    if not query:
        await answer_text(
            message,
            usage("vehicle", ["/vehicle pochinki", "/vehicle military base", "where car pochinki"]),
        )
        return

    matches = search_service.vehicle(query)
    response = (
        format_vehicle_results(matches)
        if matches
        else format_not_found("vehicle spawn", query, search_service.suggestions(query))
    )

    await sqlite_service.log_query(
        user=message.from_user,
        command="/vehicle",
        query=query,
        matched_type="vehicle" if matches else None,
    )
    await answer_text(message, response)
