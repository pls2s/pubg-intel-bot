from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import Settings
from handlers import common, drop, loot, search, secret, vehicle, zone
from services.gemini_zone_service import GeminiZoneService
from services.map_service import MapService
from services.search_service import SearchService
from services.sqlite_service import SQLiteService
from services.zone_service import ZoneService


async def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    map_service = MapService(settings.database_dir)
    search_service = SearchService(map_service)
    zone_service = ZoneService(map_service)
    zone_ai_service = None
    if settings.gemini_api_key:
        zone_ai_service = GeminiZoneService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_zone_model,
            timeout_seconds=settings.gemini_timeout_seconds,
        )
    sqlite_service = SQLiteService(settings.sqlite_path)
    await sqlite_service.init()

    bot = Bot(token=settings.bot_token)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="เปิด PUBG Intel Bot"),
            BotCommand(command="help", description="ดูคำสั่งและตัวอย่าง"),
            BotCommand(command="vehicle", description="ค้นหาจุดเกิดรถ"),
            BotCommand(command="secret", description="ค้นหาห้องลับ/จุดพิเศษ"),
            BotCommand(command="loot", description="ดูข้อมูล loot"),
            BotCommand(command="drop", description="แนะนำจุดลง"),
            BotCommand(command="zone", description="ดู phase และทำนายวง"),
            BotCommand(command="zonepic", description="วิธีส่งรูปเพื่อทำนายวง"),
        ]
    )
    dp = Dispatcher()

    # Router order matters: natural-language search is the final catch-all.
    dp.include_router(common.router)
    dp.include_router(vehicle.router)
    dp.include_router(secret.router)
    dp.include_router(loot.router)
    dp.include_router(drop.router)
    dp.include_router(zone.router)
    dp.include_router(search.router)

    logging.info("PUBG Intel Bot started with %d maps loaded.", len(map_service.maps))
    await dp.start_polling(
        bot,
        map_service=map_service,
        search_service=search_service,
        zone_service=zone_service,
        zone_ai_service=zone_ai_service,
        sqlite_service=sqlite_service,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("PUBG Intel Bot stopped.")
