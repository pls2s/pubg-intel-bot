from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from services.search_service import SearchService
from services.sqlite_service import SQLiteService
from utils.formatters import (
    format_drop_recommendation,
    format_loot_results,
    format_map_overview,
    format_not_found,
    format_secret_results,
    format_vehicle_results,
)
from utils.telegram import answer_text


router = Router(name="search")


@router.message(F.text)
async def natural_language_search(
    message: Message,
    search_service: SearchService,
    sqlite_service: SQLiteService,
) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    if text.startswith("/"):
        await answer_text(message, "Unknown command. Use /help to see available commands.")
        return

    intent = search_service.infer_intent(text)
    matched_type: str | None = intent

    if intent == "vehicle":
        matches = search_service.vehicle(text)
        response = (
            format_vehicle_results(matches)
            if matches
            else format_not_found("vehicle spawn", text, search_service.suggestions(text))
        )
    elif intent == "secret":
        matches = search_service.secret(text)
        response = (
            format_secret_results(matches)
            if matches
            else format_not_found("secret room", text, search_service.suggestions(text))
        )
    elif intent == "loot":
        matches = search_service.loot(text)
        response = (
            format_loot_results(matches)
            if matches
            else format_not_found("loot", text, search_service.suggestions(text))
        )
    elif intent == "drop":
        lookup = search_service.drop(text)
        response = (
            format_drop_recommendation(lookup.map_data, lookup.risk_hint)
            if lookup.map_data
            else format_not_found("drop recommendation", text, search_service.suggestions(text))
        )
    else:
        matches = search_service.overview(text)
        matched_type = "overview" if matches else None
        response = (
            "\n\n".join(format_map_overview(match) for match in matches)
            if matches
            else format_not_found("map intel", text, search_service.suggestions(text))
        )

    await sqlite_service.log_query(
        user=message.from_user,
        command="natural_language",
        query=text,
        matched_type=matched_type,
    )
    await answer_text(message, response)
