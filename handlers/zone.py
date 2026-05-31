from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.sqlite_service import SQLiteService
from services.zone_service import ZoneService
from utils.formatters import format_zone_phase_table
from utils.telegram import answer_text
from utils.text import command_args
from utils.zone_responses import answer_zone_prediction


router = Router(name="zone")


@router.message(Command("zone"))
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
