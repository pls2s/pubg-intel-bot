from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import Settings
from handlers import common, drop, loot, search, secret, vehicle
from services.map_service import MapService
from services.search_service import SearchService
from services.sqlite_service import SQLiteService


async def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    map_service = MapService(settings.database_dir)
    search_service = SearchService(map_service)
    sqlite_service = SQLiteService(settings.sqlite_path)
    await sqlite_service.init()

    bot = Bot(token=settings.bot_token)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Open PUBG Intel Bot"),
            BotCommand(command="help", description="Show commands and examples"),
            BotCommand(command="vehicle", description="Find vehicle spawn locations"),
            BotCommand(command="secret", description="Find secret room locations"),
            BotCommand(command="loot", description="Get loot intelligence"),
            BotCommand(command="drop", description="Get drop recommendations"),
        ]
    )
    dp = Dispatcher()

    # Router order matters: natural-language search is the final catch-all.
    dp.include_router(common.router)
    dp.include_router(vehicle.router)
    dp.include_router(secret.router)
    dp.include_router(loot.router)
    dp.include_router(drop.router)
    dp.include_router(search.router)

    logging.info("PUBG Intel Bot started with %d maps loaded.", len(map_service.maps))
    await dp.start_polling(
        bot,
        map_service=map_service,
        search_service=search_service,
        sqlite_service=sqlite_service,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("PUBG Intel Bot stopped.")
