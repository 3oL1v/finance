from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.bot.handlers import router
from app.config.settings import get_settings
from app.db.database import init_db


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token or "your_telegram_bot_token_here" in settings.bot_token:
        raise RuntimeError("BOT_TOKEN is missing. Update .env before starting the bot.")

    init_db()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="mark", description="Отметить день"),
            BotCommand(command="streak", description="Показать серию"),
            BotCommand(command="help", description="Помощь"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
