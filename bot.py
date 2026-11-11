import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database import init_db
from handlers import get_routers
from services.scheduler import setup_scheduler



logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    await init_db()          # jadvallarni yaratadi
    logging.info("Baza tayyor, bot ishga tushdi")


async def main():
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_routers(*get_routers())
    dp.startup.register(on_startup)

    await bot.delete_webhook(drop_pending_updates=True)
    scheduler = setup_scheduler(bot)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")