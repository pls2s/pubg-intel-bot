from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from services.gemini_zone_service import GeminiZoneService
from services.sqlite_service import SQLiteService
from services.zone_service import ZoneService
from utils.formatters import format_zone_phase_table
from utils.telegram import answer_text
from utils.text import command_args
from utils.zone_responses import answer_zone_image_prediction, answer_zone_prediction


router = Router(name="zone")
logger = logging.getLogger(__name__)


@router.message(Command("zone"), F.text)
async def zone_command(
    message: Message,
    zone_service: ZoneService,
    sqlite_service: SQLiteService,
) -> None:
    query = command_args(message.text)
    if not query:
        await answer_text(
            message,
            "\n".join(
                [
                    "วิธีใช้: /zone <แผนที่> phase <เลข> <จุดที่วงกิน>",
                    "",
                    "ตัวอย่าง:",
                    "- /zone erangel phase 4 school roz",
                    "- /zone phase 5",
                    "- วง 3 Erangel กลางวง School กิน Rozhok",
                ]
            ),
        )
        return

    prediction = zone_service.predict(query)
    if prediction.phase and not prediction.map_data:
        response = None
    elif not prediction.map_data and not prediction.phase:
        response = format_zone_phase_table(zone_service.all_phases())
    else:
        response = None

    await sqlite_service.log_query(
        user=message.from_user,
        command="/zone",
        query=query,
        matched_type="zone" if prediction.map_data or prediction.phase else None,
    )
    if response:
        await answer_text(message, response)
    else:
        await answer_zone_prediction(message, prediction)


@router.message(F.photo)
async def zone_photo(
    message: Message,
    bot: Bot,
    zone_service: ZoneService,
    zone_ai_service: GeminiZoneService | None,
    sqlite_service: SQLiteService,
) -> None:
    image_bytes = await _download_largest_photo(message, bot)
    if not image_bytes:
        await answer_text(message, "ดาวน์โหลดรูปไม่ได้ ลองส่งรูปวงอีกครั้ง")
        return

    await _answer_zone_image(message, image_bytes, zone_service, zone_ai_service, sqlite_service)


@router.message(F.document)
async def zone_image_document(
    message: Message,
    bot: Bot,
    zone_service: ZoneService,
    zone_ai_service: GeminiZoneService | None,
    sqlite_service: SQLiteService,
) -> None:
    document = message.document
    if not document or not (document.mime_type or "").startswith("image/"):
        return

    output = BytesIO()
    await bot.download(document, destination=output)
    image_bytes = output.getvalue()
    if not image_bytes:
        await answer_text(message, "ดาวน์โหลดรูปไม่ได้ ลองส่งรูปวงอีกครั้ง")
        return

    await _answer_zone_image(message, image_bytes, zone_service, zone_ai_service, sqlite_service)


async def _answer_zone_image(
    message: Message,
    image_bytes: bytes,
    zone_service: ZoneService,
    zone_ai_service: GeminiZoneService | None,
    sqlite_service: SQLiteService,
) -> None:
    caption = message.caption or ""
    prediction = await asyncio.to_thread(zone_service.predict_from_image, image_bytes, caption)
    if zone_ai_service:
        try:
            prediction = await asyncio.to_thread(
                zone_ai_service.refine_prediction,
                image_bytes,
                caption,
                prediction,
            )
        except Exception as exc:
            logger.warning("Gemini-assisted zone image analysis failed: %s", exc)
            prediction = replace(
                prediction,
                notes=[
                    *prediction.notes,
                    "Gemini vision ใช้งานไม่ได้ชั่วคราว จึงใช้ผล rule-based เดิม",
                ],
            )

    await sqlite_service.log_query(
        user=message.from_user,
        command="/zone_image",
        query=caption or "[photo]",
        matched_type=prediction.analysis_source if prediction.final_center_x is not None else None,
    )
    await answer_zone_image_prediction(message, prediction, image_bytes)


@router.message(Command("zonepic"), F.text)
async def zonepic_command(message: Message, sqlite_service: SQLiteService) -> None:
    await sqlite_service.log_query(
        user=message.from_user,
        command="/zonepic",
        query=command_args(message.text),
        matched_type="zone_image_help",
    )
    await answer_text(
        message,
        "\n".join(
            [
                "วิธีใช้ทำนายวงจากรูป:",
                "ส่งรูปแผนที่ที่เห็นเส้นวงสีขาว/ฟ้าชัด ๆ เข้ามาในแชต",
                "",
                "แนะนำให้ใส่ caption เช่น:",
                "- /zonepic erangel phase 4",
                "- ทำนายวง phase 5",
                "- วง 4",
            ]
        ),
    )


async def _download_largest_photo(message: Message, bot: Bot) -> bytes:
    photos = message.photo or []
    if not photos:
        return b""

    output = BytesIO()
    await bot.download(photos[-1], destination=output)
    return output.getvalue()
