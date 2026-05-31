from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from services.search_service import SearchService
from services.sqlite_service import SQLiteService
from services.zone_service import ZoneService
from utils.formatters import (
    format_drop_recommendation,
    format_loot_results,
    format_map_overview,
    format_not_found,
    format_vehicle_results,
)
from utils.secret_responses import answer_secret_matches
from utils.telegram import answer_text
from utils.zone_responses import answer_zone_prediction


router = Router(name="search")


@router.message(F.text)
async def natural_language_search(
    message: Message,
    search_service: SearchService,
    zone_service: ZoneService,
    sqlite_service: SQLiteService,
) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    if text.startswith("/"):
        await answer_text(message, "ไม่รู้จักคำสั่งนี้ พิมพ์ /help เพื่อดูคำสั่งที่ใช้ได้")
        return

    intent = search_service.infer_intent(text)
    matched_type: str | None = intent

    if intent == "vehicle":
        matches = search_service.vehicle(text)
        response = (
            format_vehicle_results(matches)
            if matches
            else format_not_found("จุดเกิดรถ", text, search_service.suggestions(text))
        )
    elif intent == "zone":
        prediction = zone_service.predict(text)
        matched_type = "zone" if prediction.map_data or prediction.phase else None
        await sqlite_service.log_query(
            user=message.from_user,
            command="natural_language",
            query=text,
            matched_type=matched_type,
        )
        await answer_zone_prediction(message, prediction)
        return
    elif intent == "secret":
        matches = search_service.secret(text)
        if matches:
            await sqlite_service.log_query(
                user=message.from_user,
                command="natural_language",
                query=text,
                matched_type=matched_type,
            )
            await answer_secret_matches(message, matches, sqlite_service)
            return
        response = format_not_found("ห้องลับ/จุดพิเศษ", text, search_service.suggestions(text))
    elif intent == "loot":
        matches = search_service.loot(text)
        response = (
            format_loot_results(matches)
            if matches
            else format_not_found("ข้อมูล loot", text, search_service.suggestions(text))
        )
    elif intent == "drop":
        lookup = search_service.drop(text)
        response = (
            format_drop_recommendation(lookup.map_data, lookup.risk_hint)
            if lookup.map_data
            else format_not_found("คำแนะนำจุดลง", text, search_service.suggestions(text))
        )
    else:
        matches = search_service.overview(text)
        matched_type = "overview" if matches else None
        response = (
            "\n\n".join(format_map_overview(match) for match in matches)
            if matches
            else format_not_found("ข้อมูลแผนที่", text, search_service.suggestions(text))
        )

    await sqlite_service.log_query(
        user=message.from_user,
        command="natural_language",
        query=text,
        matched_type=matched_type,
    )
    await answer_text(message, response)
