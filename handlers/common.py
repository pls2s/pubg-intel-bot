from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from services.sqlite_service import SQLiteService
from utils.telegram import answer_text


router = Router(name="common")


HELP_TEXT = """PUBG Intel Bot

คำสั่ง:
/start - เปิดใช้งานบอท
/help - ดูวิธีใช้
/vehicle <สถานที่หรือแผนที่> - ค้นหาจุดเกิดรถ
/secret <แผนที่> - ค้นหาห้องลับ/จุดพิเศษ
/loot <สถานที่> - ดูข้อมูล loot และเส้นทางฟาร์ม
/drop <แผนที่> - แนะนำจุดลง

ตัวอย่าง:
/vehicle pochinki
/secret taego
/loot school
/drop erangel
where car pochinki
Secret room ใน Vikendi อยู่ไหน
ของดีใน School มีอะไร
จุดลงเงียบๆใน Erangel
"""


@router.message(CommandStart())
async def start_command(message: Message, sqlite_service: SQLiteService) -> None:
    await sqlite_service.log_query(
        user=message.from_user,
        command="/start",
        query="",
        matched_type="start",
    )
    await answer_text(
        message,
        "PUBG Intel Bot พร้อมช่วยหาจุดเกิดรถ ห้องลับ เส้นทาง loot และจุดลงในแต่ละแผนที่\n\n"
        "พิมพ์ /help เพื่อดูตัวอย่างคำสั่ง",
    )


@router.message(Command("help"))
async def help_command(message: Message, sqlite_service: SQLiteService) -> None:
    await sqlite_service.log_query(
        user=message.from_user,
        command="/help",
        query="",
        matched_type="help",
    )
    await answer_text(message, HELP_TEXT)
